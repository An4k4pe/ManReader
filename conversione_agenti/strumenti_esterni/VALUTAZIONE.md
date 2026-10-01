# Marker e Docling contro la bozza: esito (30 set 2026)

Criterio in `CRITERIO.md`, scritto prima dei dati. Numeri per pagina in `risultati.json`, script `confronta.py`.
Versioni: marker-pdf 2.0.0 (`--mode fast`, CPU, `LLAMA_CPP_NGL=0`), docling 2.131.0 (CPU). 30 pagine, 10 per manuale.

## Mediane (A = forma+contenuto, B = solo parole)

| manuale | gruppo | bozza A/B | marker A/B | docling A/B |
|---|---|---|---|---|
| Candela | difficili | 0.447 / 0.478 | 0.392 / 0.471 | 0.911 / 0.872 |
| Candela | facili | 1.000 / 1.000 | 0.997 / 0.992 | 0.995 / 0.988 |
| Vileborn | difficili | 0.926 / 0.974 | 0.929 / 0.935 | 0.745 / 0.891 |
| Vileborn | facili | 0.995 / 1.000 | 0.966 / 0.946 | 0.974 / 0.960 |
| Draw Steel | difficili | 0.743 / 0.783 | 0.725 / 0.658 | 0.802 / 0.857 |
| Draw Steel | facili | 0.994 / 1.000 | 0.917 / 0.963 | 0.980 / 0.989 |

**Esito sul criterio: nessuno dei due è candidato a base.** Docling vince sulle difficili in 2 manuali su 3,
ma perde più di 0,01 sulle facili in tutti e 3; Marker non vince in nessuno.

## Limiti della misura
- Le pagine rivedute nascono dalla revisione della bozza: la misura favorisce la bozza nelle scelte di forma,
  ed è per questo che esiste B.
- Candela p.97 (testo spostato a p.96 dal revisore) e p.115 (didascalie dentro le note immagine) sono artefatti:
  Docling prende 1,0 su p.115 perché **ha perso** le didascalie.
- Pagine singole: si perdono i segnali di documento (segnalibri per i titoli di Docling, ripetuti per Marker).
- Marker `balanced` (VLM) non provato: vuole la GPU.

## A vista (diff contro le pagine rivedute)
- **Ordine di lettura**: Docling mette meglio il riquadro di Candela p.13 e raggruppa meglio DrW p.78.
  Marker `fast` sbaglia l'ordine su DrW p.46, Vileborn p.39 e p.219 (0,4-0,7), anche se il contenuto c'è.
- **Testo alterato**: Docling raddrizza le virgolette tipografiche, perde i trattini lunghi, fonde parole
  ("COLLABORATIONAT") e non tiene grassetto e corsivo. Marker li tiene.
- **Rumore dalle immagini**: Docling lascia passare il testo dentro i grafici (Vileborn p.84: "SUBD COR CIA SEN").
- **Glifi**: nessuno dei due conosce i font simboli (`¥` come punto elenco, `á í é` per i livelli di DrW),
  mentre la bozza col profilo li traduce.
- **Tabelle**: tutti e tre trovano le stesse 3 tabelle su 6 (DrW p.128, 146, 164). Falsi positivi: bozza 1,
  Marker 2, Docling 4 (l'indice di Vileborn p.8 diventa una tabella).
- **Immagini**: entrambi salvano ogni figura, decorazioni comprese (Candela p.13: 4 contro 1 reale), senza
  distinguere sfondi o ripetuti e senza note. Su questo la classificazione asset del processo è più avanti.

## Cosa vale la pena prendere
1. **La gerarchia dei titoli di Docling** (`docling/models/stages/heading_hierarchy/heading_hierarchy_model.py`,
   MIT): segnalibri, poi numerazione, poi stile. Quando i corpi si equivalgono, lo spareggio va a peso, poi
   inclinazione, poi maiuscolo. La bozza ha già segnalibri e corpo (`heading_size_levels`), le mancano lo
   spareggio e la numerazione, e il residuo della bozza è proprio nei livelli dei titoli. Da provare col banco.
2. **Docling come seconda opinione sull'ordine** (ipotesi, non misurata a sufficienza: 2-3 pagine): solo sulle
   pagine dove la bozza è incerta, e fuori da ManReader, perché porta torch.
3. Niente da prendere per tabelle, glifi e immagini.

---
# Secondo giro (30 set 2026 sera): modelli visivi in GPU e strumenti leggeri

Versioni: MinerU 4.0.10 (mineru-kit parse, tier standard, "ibrido": strato di testo + MinerU2.5-Pro-2605 1.2B Q8
su llama.cpp in GPU), PaddleOCR-VL 1.6 (paddleocr 3.7, layout su CPU, VL 0.9B su llama.cpp in GPU),
PyMuPDF4LLM 1.28.2, OpenDataLoader PDF 2.5.11 (Java, JRE Temurin 21 portabile in `jre/`), LiteParse 2.15.
GPU: 9 minuti di carico, picco 68 °C bordo / 90 °C giunzione, nessuno spegnimento (`gpu_monitor.log`).
MinerU 4 **manda telemetria a mineru.net** dalla parte `mineru` (doclib) se non disattivata; `mineru-kit parse`
non la importa.

## Correzione del primo giro
La misura B contava come diverse `l'ordine` e `l’ordine`. Ora gli apostrofi sono normalizzati: gli strumenti
esterni salgono (Docling Vileborn difficili 0,891 → 0,933). Numeri aggiornati in `confronto_finale.txt`.

## Esito sul criterio scritto
Con B corretta **Docling e MinerU superano il criterio** (2 manuali su 3). Ma il criterio era difettoso: la
mediana nasconde le pagine perse. MinerU su Vileborn p.57 (pagina "facile") scambia tutto il testo per
un'immagine e ne tiene 0,03; su Candela p.203 lo stesso con quattro elenchi. Pagine con B < 0,9 su 28
(esclusi gli artefatti p.97 e p.115): bozza 7, PaddleOCR-VL 4, Docling 8, OpenDataLoader 8, PyMuPDF4LLM 9,
MinerU 10, LiteParse 10, Marker 11.
Parole assenti sia dal PDF sia dalla riveduta: bozza 0,15%, PyMuPDF4LLM 0,10%, LiteParse 0,32%, Docling 0,50%,
Marker 0,59%, OpenDataLoader 0,86%, PaddleOCR-VL 1,24% (LaTeX per il sottolineato, entità HTML, parole fuse),
MinerU 1,63% (lettura delle scritte decorative).

## A vista
- MinerU: l'unico che su Candela p.13 salva solo l'immagine vera (1 invece di 3-4 decorazioni); tiene grassetto e
  virgolette tipografiche perché legge lo strato di testo; ma perde blocchi di testo interi. Tabelle 1/6.
- PaddleOCR-VL: meno pagine perse di tutti, vince su DrW p.78 e p.235; rumore di formato; tabelle 3/6 con 4 falsi.
- I leggeri (PyMuPDF4LLM, OpenDataLoader, LiteParse) non battono la bozza: sono la stessa famiglia di euristiche.

## Pista nuova: il disaccordo come smistamento (NON validata)
Segnalare le pagine dove la bozza e uno strumento concordano (parole) meno di 0,9:
PaddleOCR-VL segnala 7 pagine, 6 delle 7 con bozza < 0,95, 1 falso allarme; Docling 8, 6/7, 2 falsi.
Soglia scelta guardando i dati, campione di 28 con metà pagine difficili: va provata sui 503 pagine rivedute
intere (bozza già misurata pagina per pagina), con soglia fissata prima.
