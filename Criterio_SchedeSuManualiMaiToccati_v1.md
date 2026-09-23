# Criterio — le schede su manuali che non hanno partecipato a costruirle

Dichiarato il 23 settembre 2026, **prima** della misura. Ultimo passo del piano
dell'utente: «alla fine un test su manuali mai toccati».

## 0. Perché

Tutto il riconoscimento delle schede — righe di campi, posizione relativa,
policy di documento, consumer, riquadri v3 — è stato costruito e misurato su
**tre** manuali: DB (Dragonbane), Dag (Daggerheart), Apo (Apocalisse). Ogni
condizione è stata scelta guardando pagine di quei tre. Una regola formata su
una popolazione non è verificata da quella popolazione.

`stat_block_regions.py`, portato dalla chat delle schede, ha in più nella sua
storia DrM (Draw Steel: Monsters) e il Dragonbane Quickstart: **DrM resta fuori**
da questo test, e con lui DrW, che è dello stesso sistema.

## 1. La popolazione, scelta prima di guardare

Sei manuali, di editori e sistemi diversi, nessuno dei quali compare in un
criterio o in un esito delle schede:

| manuale | pagine |
| --- | ---: |
| Wil | 316 |
| BiD | 328 |
| DIE | 408 |
| SV | 372 |
| Kul | 242 |
| Vil | 272 |

Restano fuori per tempo, e non per scelta di risultato: BoB, FW, FWK, Fab, Lan.
Fab compare solo come `Fab idx 126`, la differenza già a verbale della barra
E-B, che non ha formato nessuna regola.

## 2. La misura

Ogni manuale reso due volte:

- **senza schede**: `--tabelle`
- **con schede**: `--tabelle --schede-producer`

Il confronto è fra le due rese dello stesso manuale. Non c'è uno stato
precedente da difendere: qui si guarda che cosa il meccanismo **fa** dove non è
mai stato provato.

## 3. Che cosa deve succedere perché passi

**A. Niente cade.** I dodici render arrivano in fondo con uscita 0. Un errore
non è un fallimento del criterio ma lo interrompe: va guardato prima di tutto.

**B. Le tabelle possono solo perdere righe o sparire.** Una tabella che ne
**guadagna** è un difetto d'implementazione, e ferma tutto.

**C. Il giudizio, sull'immagine della pagina.** Ogni tabella che cambia si
guarda: **meglio** se esce una riga che la pagina stampa **fuori** dalla
tabella, **peggio** se ne esce una che la pagina stampa **dentro**. Se cambiano
più di 30 tabelle, si guardano le prime 30 in ordine di manuale e pagina.
**Passa se meglio ≥ peggio.**

**D. Nessuna prosa tagliata.** Su ogni manuale il numero di paragrafi che
cominciano in minuscola — una frase orfana, cioè prosa spezzata — non sale.

**E. Dove ci sono schede, si vedono.** Per ogni manuale si riporta quante
combinazioni di campi la policy ammette e quante schede il consumer accetta, e
si guarda **una pagina per manuale** sull'immagine: se il manuale ha schede,
devono essere riconosciute; se non ne ha, il meccanismo deve tacere come su
Apocalisse.

**Veto.** Se una tabella che la pagina stampa come tabella perde righe perché
una scheda o un riquadro se le è prese, il meccanismo non è universale e la
misura lo dice.

## 4. La previsione, scritta prima di guardare

- **Silenzio dove non ci sono schede.** Su un manuale di sola prosa la policy
  ammette zero combinazioni e non cambia niente, come su Apocalisse.
- **Il rischio vero è la policy, non il riquadro.** Le combinazioni si imparano
  da ciò che si ripete: un manuale con intestazioni ricorrenti in grassetto
  seguite dai due punti — «Prerequisiti:», «Durata:», «Costo:» in una lista di
  incantesimi — può produrre combinazioni che non sono schede. Se succede, si
  vedrà come righe che escono dalle tabelle di quegli elenchi.
- **Mi aspetto almeno un manuale con un difetto nuovo.** Sei manuali mai visti
  contro regole formate su tre: se tutti e sei passassero puliti, guarderei con
  sospetto la misura prima di festeggiare.
