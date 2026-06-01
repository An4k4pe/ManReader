"""
describer.py — Descrizioni AI per immagini e tabelle.

Usa l'API Anthropic (modello con vision) per generare una descrizione
contestualizzata al dominio GDR. Le descrizioni vengono salvate come
file .txt accanto agli asset, e inserite come caption nell'EPUB.

Nota sul rate limiting: l'API ha limiti di richieste al minuto.
In caso di errori 429, il codice fa un retry con backoff esponenziale
(max 3 tentativi). Per PDF molto grandi (>100 immagini) considera
di disabilitare --ai e fare una seconda passata.
"""

import base64
import time
from typing import List


class AIDescriber:
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, language: str = "italiano"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.language = language

    # -----------------------------------------------------------------------
    # Descrizione immagini
    # -----------------------------------------------------------------------

    def describe_image(self, image_data: bytes, ext: str) -> str:
        """
        Invia l'immagine all'API con un prompt contestualizzato ai manuali GDR.
        Ritorna la descrizione come stringa.
        """
        media_type = self._ext_to_media_type(ext)
        b64 = base64.standard_b64encode(image_data).decode("utf-8")

        prompt = (
            f"Sei un assistente specializzato in manuali di giochi di ruolo (GDR/RPG). "
            f"Descrivi questa immagine in {self.language} in 2-3 frasi concise. "
            f"Indica: cosa mostra (illustrazione, mappa, diagramma, tabella visiva, "
            f"personaggio, creatura, equipaggiamento, scenario, ecc.), "
            f"il suo probabile scopo nel manuale, e qualsiasi informazione "
            f"rilevante per un giocatore/master che ne abbia bisogno come riferimento."
        )

        return self._call_with_retry(lambda: self.client.messages.create(
            model=self.MODEL,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        ))

    # -----------------------------------------------------------------------
    # Descrizione tabelle
    # -----------------------------------------------------------------------

    def describe_table(self, rows: List[List[str]]) -> str:
        """
        Costruisce una rappresentazione testuale della tabella e chiede
        all'AI di spiegarne il contenuto nel contesto GDR.

        Non inviamo tutte le righe per contenere i costi: intestazioni +
        max 5 righe di esempio sono sufficienti per capire il contenuto.
        """
        if not rows:
            return "[Tabella vuota]"

        header = " | ".join(rows[0]) if rows else ""
        sample = "\n".join(" | ".join(r) for r in rows[1:6])
        total_rows = len(rows) - 1
        extra = f"\n(+ altre {total_rows - 5} righe)" if total_rows > 5 else ""

        table_repr = f"Intestazioni: {header}\nRighe:\n{sample}{extra}"

        prompt = (
            f"Sei un assistente specializzato in manuali di giochi di ruolo (GDR/RPG). "
            f"Descrivi in {self.language} in 1-2 frasi cosa contiene questa tabella "
            f"e a cosa serve (es: statistiche mostri, tabella danni, modificatori abilità, "
            f"lista incantesimi, prezzi equipaggiamento, ecc.):\n\n{table_repr}"
        )

        return self._call_with_retry(lambda: self.client.messages.create(
            model=self.MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        ))

    # -----------------------------------------------------------------------
    # Utilità interne
    # -----------------------------------------------------------------------

    def _call_with_retry(self, call_fn, max_retries: int = 3) -> str:
        """
        Esegue la chiamata API con backoff esponenziale in caso di rate limit.
        """
        for attempt in range(max_retries):
            try:
                response = call_fn()
                return response.content[0].text.strip()
            except Exception as e:
                err = str(e)
                if "429" in err or "rate_limit" in err.lower():
                    wait = 2 ** (attempt + 1)  # 2, 4, 8 secondi
                    print(f"\n  [rate limit] attendo {wait}s...")
                    time.sleep(wait)
                else:
                    return f"[Descrizione non disponibile: {e}]"
        return "[Descrizione non disponibile: troppi tentativi]"

    @staticmethod
    def _ext_to_media_type(ext: str) -> str:
        return {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "jp2": "image/jp2",
        }.get(ext.lower(), "image/png")
