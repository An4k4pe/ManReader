# La nota dello sfondo della scheda — criterio pre-registrato (passo 3b)

Ordine: 3a (committato, `e05ebfa`), **3b**, 3c. Il giro di revisione di Chat B si
fa dopo, per decisione dell'utente dell'11 settembre 2026.

## Il difetto
In IR 2 la nota di un'immagine dice il kind **proposto** dal candidato:
«riquadro», «immagine inserita». Sulla pagina della Signora il ritratto e'
`[riquadro]` e la pergamena della scheda `[immagine inserita]`; sui Pipistrelli
e' il contrario. La nota non dice che cosa ha sostituito, che e' meta'
dell'obiettivo (`AGENTS.MD` §Obiettivo).

## La modifica
- **Contratto**: `AssetRefIR2.stat_block_name: str | None`, non vuoto se c'e'.
  Dice che l'asset e' lo sfondo disegnato della scheda con quel nome. E' un
  campo additivo su un contratto esistente -- «aprire uno stadio non e'
  estenderlo» (`AGENTS.MD`) -- quindi criterio e test, nessuna decisione
  dedicata. Serializzazione: chiave obbligatoria, come `runs`, `heading_level` e
  `marker` prima di lui; lo schema resta `2.0`, come allora.
- **Chi lo riempie**: l'innesto in `scripts/prototype_ir2_page.py`, per le
  immagini che sono membri del riquadro di una scheda **con nome**
  (`StatBlockRegion.frame_primitive_ids`). Solo con nome: il nome e' la prova che
  il riquadro intesta qualcosa, e a DB idx 99 la regione senza nome e'
  un'illustrazione con sopra anche prosa.
- **Resa**: `> **[sfondo della scheda RAGNO GIGANTE]** 254×94 pt — file`. Il nome
  e' il testo del titolo che la scheda porta dopo 3a.
- Non cambia nient'altro: le note che sfondi di scheda non sono restano come
  sono, e quali note entrano nel corpo lo decide ancora la porta di Resolution.

## Cosa NON fa
Il cartiglio del nome e il riquadro della tabella degli attacchi, che su
Dragonbane sono immagini separate dal riquadro della scheda: restano «riquadro» o
«immagine inserita». Gli sfondi vettoriali, come quelli di Daggerheart: non hanno
nota ne' prima ne' dopo. Le righe dentro la scheda (3c).

## Predizioni
- **S1, la condizione.** Sugli stessi intervalli di 3a, con base l'uscita di 3a
  (`e05ebfa`): le righe del Markdown che cambiano sono **solo righe di nota**, e
  solo su pagine con una scheda con nome; il testo dell'IR (nodi e celle) e'
  identico su **tutte** le pagine.
- **S2** Daggerheart 36-56: nessuna pagina cambia, perche' i riquadri sono
  vettoriali.
- **S3** Dragonbane: cambiano **fra 4 e 6 note**, una per scheda (Ragno,
  Pipistrelli, Signora, Wight, e forse Grub e AZIONI), e la nota che cambia e'
  quella della pergamena, **non** quella del ritratto ne' del cartiglio.
- **S4** DB 95-125: il numero non e' predetto e si riporta.
- **S5** Il round trip della serializzazione resta senza perdita su ogni pagina:
  lo controlla gia' `run()` a ogni pagina.
- **S6** E-B invariato: le note si tolgono dal confronto per costruzione.
- **S7** Suite verde, con test nuovi per modello, serializzazione, resa, costruttore
  e riconoscimento.

## Accettazione
S1 e' la condizione. S3 si verifica sulle pagine, a vista, anche dall'utente. S2,
S4, S5, S6 e S7 si riportano.
