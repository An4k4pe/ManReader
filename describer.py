"""
describer.py — Descrizioni AI per immagini e tabelle estratte da manuali GDR.

Supporta tre backend selezionabili via flag --vision-backend:
  - anthropic : API Anthropic Claude (richiede ANTHROPIC_API_KEY)
  - gemini    : API Google Gemini, tier gratuito (richiede GEMINI_API_KEY)
  - ollama    : Inferenza locale via Ollama (nessuna API key, richiede Ollama in esecuzione)

Pattern interno: classe base astratta BaseDescriber + implementazioni specifiche.
La factory function `create_describer()` istanzia il backend corretto.
Il resto del codice (extractor.py, epub_builder.py) non vede differenze.

Note rate limiting:
  - Anthropic: retry con backoff esponenziale su 429
  - Gemini: quota free 1500 req/giorno, 15 req/min — stessa logica di retry
  - Ollama: locale, nessun rate limit ma latenza dipende dall'hardware
"""

import base64
import time
from abc import ABC, abstractmethod
from typing import List


# ---------------------------------------------------------------------------
# Interfaccia comune
# ---------------------------------------------------------------------------

class BaseDescriber(ABC):
    """
    Interfaccia che tutti i backend devono implementare.
    describe_image e describe_table sono i due metodi usati dal resto del codice.
    """

    def __init__(self, language: str = "italiano"):
        self.language = language

    @abstractmethod
    def describe_image(self, image_data: bytes, ext: str) -> str:
        """Ritorna una descrizione testuale dell'immagine."""
        ...

    @abstractmethod
    def describe_table(self, rows: List[List[str]]) -> str:
        """Ritorna una descrizione testuale della tabella."""
        ...

    # Utility condivisa: costruisce il prompt immagine
    def _image_prompt(self) -> str:
        return (
            f"Sei un assistente specializzato in manuali di giochi di ruolo (GDR/RPG). "
            f"Descrivi questa immagine in {self.language} in 2-3 frasi concise. "
            f"Indica: cosa mostra (illustrazione, mappa, diagramma, tabella visiva, "
            f"personaggio, creatura, equipaggiamento, scenario, ecc.), "
            f"il suo probabile scopo nel manuale, e qualsiasi informazione "
            f"rilevante per un giocatore/master che ne abbia bisogno come riferimento."
        )

    # Utility condivisa: costruisce il prompt tabella
    def _table_prompt(self, rows: List[List[str]]) -> str:
        if not rows:
            return ""
        header = " | ".join(rows[0])
        sample = "\n".join(" | ".join(r) for r in rows[1:6])
        total_rows = len(rows) - 1
        extra = f"\n(+ altre {total_rows - 5} righe)" if total_rows > 5 else ""
        table_repr = f"Intestazioni: {header}\nRighe:\n{sample}{extra}"
        return (
            f"Sei un assistente specializzato in manuali di giochi di ruolo (GDR/RPG). "
            f"Descrivi in {self.language} in 1-2 frasi cosa contiene questa tabella "
            f"e a cosa serve (es: statistiche mostri, tabella danni, modificatori abilità, "
            f"lista incantesimi, prezzi equipaggiamento, ecc.):\n\n{table_repr}"
        )

    @staticmethod
    def _ext_to_mime(ext: str) -> str:
        return {
            "png":  "image/png",
            "jpg":  "image/jpeg",
            "jpeg": "image/jpeg",
            "gif":  "image/gif",
            "webp": "image/webp",
            "jp2":  "image/jp2",
        }.get(ext.lower(), "image/png")

    @staticmethod
    def _retry(call_fn, max_retries: int = 3) -> str:
        """Backoff esponenziale su rate limit (429). Comune a tutti i backend HTTP."""
        for attempt in range(max_retries):
            try:
                return call_fn()
            except Exception as e:
                err = str(e)
                if "429" in err or "rate_limit" in err.lower() or "quota" in err.lower():
                    wait = 2 ** (attempt + 1)
                    print(f"\n  [rate limit] attendo {wait}s...")
                    time.sleep(wait)
                else:
                    return f"[Descrizione non disponibile: {e}]"
        return "[Descrizione non disponibile: troppi tentativi]"


# ---------------------------------------------------------------------------
# Backend Anthropic (comportamento invariato rispetto alla versione precedente)
# ---------------------------------------------------------------------------

class AnthropicDescriber(BaseDescriber):
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, language: str = "italiano"):
        super().__init__(language)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def describe_image(self, image_data: bytes, ext: str) -> str:
        b64 = base64.standard_b64encode(image_data).decode("utf-8")
        mime = self._ext_to_mime(ext)
        prompt = self._image_prompt()

        return self._retry(lambda: self.client.messages.create(
            model=self.MODEL,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        ).content[0].text.strip())

    def describe_table(self, rows: List[List[str]]) -> str:
        if not rows:
            return "[Tabella vuota]"
        prompt = self._table_prompt(rows)
        return self._retry(lambda: self.client.messages.create(
            model=self.MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        ).content[0].text.strip())


# ---------------------------------------------------------------------------
# Backend Google Gemini (tier gratuito: 1500 req/giorno, 15 req/min)
# Usa il pacchetto google-genai (google.generativeai è deprecato da maggio 2025)
# Documentazione: https://googleapis.github.io/python-genai/
# ---------------------------------------------------------------------------

class GeminiDescriber(BaseDescriber):
    MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str, language: str = "italiano"):
        super().__init__(language)
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError:
            raise ImportError(
                "Libreria google-genai non installata.\n"
                "Installa con: pip install google-genai"
            )
        self.client = genai.Client(api_key=api_key)
        self._types = genai_types

    def describe_image(self, image_data: bytes, ext: str) -> str:
        mime = self._ext_to_mime(ext)
        image_part = self._types.Part.from_bytes(data=image_data, mime_type=mime)
        prompt = self._image_prompt()

        def call():
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=[image_part, prompt],
                config=self._types.GenerateContentConfig(max_output_tokens=256),
            )
            return response.text.strip()

        return self._retry(call)

    def describe_table(self, rows: List[List[str]]) -> str:
        if not rows:
            return "[Tabella vuota]"
        prompt = self._table_prompt(rows)

        def call():
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config=self._types.GenerateContentConfig(max_output_tokens=150),
            )
            return response.text.strip()

        return self._retry(call)


# ---------------------------------------------------------------------------
# Backend Ollama (inferenza locale, nessuna API key)
# Documentazione: https://github.com/ollama/ollama/blob/main/docs/api.md
# Modelli vision consigliati: llama3.2-vision, llava, bakllava
# ---------------------------------------------------------------------------

class OllamaDescriber(BaseDescriber):
    DEFAULT_MODEL = "llama3.2-vision"
    DEFAULT_HOST  = "http://localhost:11434"

    def __init__(self, model: str = None, host: str = None, language: str = "italiano"):
        super().__init__(language)
        try:
            import requests
            self._requests = requests
        except ImportError:
            raise ImportError("Libreria requests non installata: pip install requests")
        self.model = model or self.DEFAULT_MODEL
        self.host  = (host or self.DEFAULT_HOST).rstrip("/")
        self._check_connection()

    def _check_connection(self):
        """Verifica che Ollama sia raggiungibile e il modello sia disponibile."""
        try:
            r = self._requests.get(f"{self.host}/api/tags", timeout=5)
            r.raise_for_status()
            available = [m["name"] for m in r.json().get("models", [])]
            # Cerca corrispondenza anche parziale (es. "llama3.2-vision:latest")
            matches = [m for m in available if self.model.split(":")[0] in m]
            if not matches:
                print(
                    f"\n  [ollama] Modello '{self.model}' non trovato tra i modelli installati.\n"
                    f"  Modelli disponibili: {', '.join(available) or 'nessuno'}\n"
                    f"  Installa con: ollama pull {self.model}"
                )
        except Exception as e:
            print(
                f"\n  [ollama] Impossibile connettersi a {self.host}: {e}\n"
                f"  Assicurati che Ollama sia in esecuzione: ollama serve"
            )

    def describe_image(self, image_data: bytes, ext: str) -> str:
        b64 = base64.standard_b64encode(image_data).decode("utf-8")
        payload = {
            "model":  self.model,
            "prompt": self._image_prompt(),
            "images": [b64],
            "stream": False,
            "options": {"num_predict": 256},
        }

        def call():
            r = self._requests.post(
                f"{self.host}/api/generate", json=payload, timeout=120
            )
            r.raise_for_status()
            return r.json()["response"].strip()

        return self._retry(call)

    def describe_table(self, rows: List[List[str]]) -> str:
        if not rows:
            return "[Tabella vuota]"
        payload = {
            "model":  self.model,
            "prompt": self._table_prompt(rows),
            "stream": False,
            "options": {"num_predict": 150},
        }

        def call():
            r = self._requests.post(
                f"{self.host}/api/generate", json=payload, timeout=60
            )
            r.raise_for_status()
            return r.json()["response"].strip()

        return self._retry(call)


# ---------------------------------------------------------------------------
# Factory function — punto di ingresso unico per main.py
# ---------------------------------------------------------------------------

SUPPORTED_BACKENDS = ("anthropic", "gemini", "ollama")

def create_describer(
    backend: str,
    language: str = "italiano",
    api_key: str = None,
    ollama_model: str = None,
    ollama_host: str = None,
) -> BaseDescriber:
    """
    Istanzia e ritorna il backend richiesto.

    Args:
        backend:      "anthropic" | "gemini" | "ollama"
        language:     lingua per le descrizioni
        api_key:      chiave API (obbligatoria per anthropic e gemini, ignorata per ollama)
        ollama_model: modello Ollama da usare (default: llama3.2-vision)
        ollama_host:  URL del server Ollama (default: http://localhost:11434)

    Raises:
        ValueError: se il backend non è supportato o mancano le credenziali richieste
    """
    backend = backend.lower()

    if backend == "anthropic":
        if not api_key:
            raise ValueError(
                "Backend 'anthropic' richiede una API key.\n"
                "Imposta ANTHROPIC_API_KEY o usa --api-key"
            )
        return AnthropicDescriber(api_key, language)

    elif backend == "gemini":
        if not api_key:
            raise ValueError(
                "Backend 'gemini' richiede una API key.\n"
                "Ottienila gratis su https://aistudio.google.com/app/apikey\n"
                "Imposta GEMINI_API_KEY o usa --api-key"
            )
        return GeminiDescriber(api_key, language)

    elif backend == "ollama":
        return OllamaDescriber(
            model=ollama_model,
            host=ollama_host,
            language=language,
        )

    else:
        raise ValueError(
            f"Backend '{backend}' non supportato. "
            f"Scegli tra: {', '.join(SUPPORTED_BACKENDS)}"
        )


# ---------------------------------------------------------------------------
# Alias di retrocompatibilità — il resto del codice che importa AIDescriber
# direttamente continua a funzionare senza modifiche
# ---------------------------------------------------------------------------

AIDescriber = AnthropicDescriber

