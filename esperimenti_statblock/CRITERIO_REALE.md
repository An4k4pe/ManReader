# Criterio per il giro su Daggerheart SRD — scritto prima di aprire il PDF

## Scopo
Verificare la catena su dati reali: aperture -> scheletri -> schema indotto ->
schema come classificatore. Non e' piu' una prova di meccanismo: qui i numeri
contano.

## Verita' di riferimento, stabilita per via INDIPENDENTE dal metodo
Non uso il mio rilevatore per definire cosa e' una scheda. Costruisco la verita'
per ricerca testuale delle etichette di campo del formato Daggerheart
(es. "Difficulty", "Thresholds", "HP", "Stress", "ATK", "Motives"), contando le
occorrenze riga per riga, e poi **guardo a occhio** un campione delle pagine per
confermare che quelle occorrenze siano schede e non citazioni nel testo.
Se le due vie divergono, vince l'ispezione a vista, e lo scrivo.

## Cosa conto
- **Mancate**: schede presenti nella verita' e non proposte dal metodo. E' la
  metrica che decide: una scheda mancata e' irrecuperabile a valle.
- **Falsi positivi**: zone proposte che l'ispezione dice non essere schede.
- **Rifiuti sbagliati**: schede vere che il classificatore-schema SCARTA. E' il
  guasto peggiore perche' arriva con una motivazione plausibile.
- **Troncate / code**: quante schede attraversano una colonna o una pagina, e se
  il metodo le dichiara invece di emetterle mutile.

## Falsificazione
- Se le mancate sono > 10% delle schede vere, il rilevamento non regge e va detto.
- Se il classificatore-schema rifiuta anche una sola scheda vera per un motivo
  che non sia "incompleta", il test di forma va declassato ad avviso, come gia'
  previsto dal giro sintetico.
- Se lo schema indotto contiene etichette che non sono campi (es. parole di
  prosa ricorrenti), l'induzione non e' pronta e va detto.

## Vincolo
Nessuna taratura dopo aver visto i risultati senza dichiararla come tale.
I numeri del primo giro restano a verbale anche se il secondo va meglio.
