# Passaggio di consegne 2 — riconoscimento delle schede statistiche

Secondo documento di trasferimento, scritto alla chiusura della sessione del
6-9 settembre 2026. **Non sostituisce `PASSAGGIO_DI_CONSEGNE.md`**: quello resta
valido per il metodo e per la storia fino al 5 settembre. Questo dice cosa e'
successo dopo, cosa e' caduto, e da dove si riparte.

Leggi prima `CLAUDE.md` e `AGENTS.MD` del repo, e la sezione pertinente di
`State.md`. **Non leggere `State_Archive.md`.**

Ramo: `claude/statblock-asset-class-yf3y9c-2054f9`, commit `217a1fb`.

---

## 0. La cosa che serve subito: dove sono i manuali

La sessione precedente lavorava su upload cloud. **I file esistono in locale**, e
ritrovarli e' costato tempo:

    manuale 1 (banco di sviluppo)   /home/an4k4pe/Documenti/KDrive/ManualiGdr/
                                    DaggerHeart/Daggerheart-SRD-9-09-25.pdf
                                    (868 KB, 68 pagine — e' esattamente quello
                                    su cui il metodo e' stato progettato)

    manuale 2 (bruciato dal test)   /home/an4k4pe/Documenti/KDrive/ManualiGdr/
                                    Dragonbane/Dragonbane-Quickstart-jxfem8_
                                    647f908c2f17e.pdf  (47 pagine)

    terzo manuale, SIGILLATO        /home/an4k4pe/Documenti/KDrive/ManualiGdr/
                                    Draw_Steel_Monsters_v1.01.pdf
                                    (385 pagine, inglese, sistema mai usato,
                                    bestiario numeroso). NON APERTO. Serve a
                                    validare, e si apre solo col criterio scritto.

Python: `/home/an4k4pe/Documenti/ManReader (Copia)/venv/bin/python` (3.14,
PyMuPDF 1.28). I PDF non stanno nel worktree: `*.pdf` e' gitignorato.

**Verificato all'inizio della sessione**: `pila.py` congelato riproduce
`out_pila.txt` **riga per riga** sul manuale 1 (474 record, 148/148), e riproduce
il fallimento documentato sul manuale 2 (34 etichette, 16 gruppi). Le basi
reggono; chi riprende non deve rifare quella verifica.

---

## 1. Un dettaglio che il primo passaggio di consegne non aveva

Sul manuale 2 le 4 schede mostro **vengono emesse**, non perse: stanno tutte nel
gruppo 3, unica etichetta di schema `Movimento` (7 occorrenze, sopra soglia),
profondita' di testa dedotta **1**. Il record parte dalla riga `Ferocia: …` e il
**nome del mostro resta fuori**; l'estensione corre fino alla testa successiva
(6, 20, 32, 39 righe).

Quindi non e' vero che il prerequisito era fallito del tutto a monte: la pila di
testa **era** stata esercitata, e aveva trovato uno strato dove ne servivano due.
Non cambia il verdetto di fallimento, cambia il bersaglio.

---

## 2. Correzioni 2 e 3: fatte, misurate, NON accettate

Criterio `CRITERIO_CORREZIONI_2_3.md`, risultati `RISULTATI_CORREZIONI_2_3.txt`.
Codice: `pila2.py` (copia di `pila.py` con le due sole correzioni; `pila.py`
resta congelato) e `colonne.py`.

- **Correzione 2, estrazione multipla per riga**: fatta. Regola size-free —
  uno span e' etichetta se il successivo ha stile diverso, il valore e' la corsa
  in quello stile. **Non** la versione di `real5.py`, che chiedeva che
  l'etichetta non fosse piu' grande del corpo locale e avrebbe rimesso dentro
  una soglia di dimensione.
- **Correzione 3, confini di colonna**: `COL_GAP = 30pt` sostituito dal producer
  `layout.column_band` di produzione, consumato dal **contratto** (candidati piu'
  misure satellite), non dalle strutture interne.

Esiti contro le predizioni registrate:

| | esito |
| --- | --- |
| P1 non-regressione su manuale 1 | **REGGE**. 148/148, e la firma degli avversari recupera `HP` e `Thresholds`, che stanno sulla riga di `Difficulty` e la versione a una etichetta perdeva |
| P2 occorrenze | **FALSIFICATA IN PARTE**. `Taglia` 0→4 come previsto, ma `Armatura` 5 e `PF` 11: comparivano anche fuori dalle schede, e non l'avevo previsto |
| P3 nome e campi nella stessa colonna | **FALSIFICATA**. Resta 2 su 4, ma non le stesse due: p.29 guadagna, p.35 perde |
| P4 il template non deve formarsi | **FALSIFICATA**. Si forma: `{Armatura, Movimento, PF}`, 5 nuclei, profondita' 4 |

**Verdetto: non accettate come formulate.** Nessuna costante spostata.

**Due cose importanti sotto quei numeri.**

1. Il template si forma **per un conteggio gonfiato**: `PF` arriva a 11 perche' 7
   occorrenze sono schede personaggio. Il gruppo ha 5 nuclei = 4 schede vere piu'
   un falso positivo (pagina indice 32, scheda personaggio). Non e' la
   correzione 1, e non va scambiata per quella.
2. Sotto la causa 3 c'era **una seconda causa mai isolata**: su 2 schede su 4 il
   nome e' un **titolo centrato sopra un corpo a due colonne**. La pila di testa
   cammina all'indietro dentro una colonna contando righe, e li' non puo'
   arrivare per costruzione.

---

## 3. Correzione 4, la misura di copertura: ACCETTATA

Criterio `CRITERIO_COPERTURA.md`, risultati `RISULTATI_COPERTURA.txt`, codice
`copertura.py`. **E' la cosa piu' utile prodotta in questa sessione.**

Definizione, senza costanti nuove: una riga e' **residua** se porta etichette e
**nessuna** e' nello schema; le corse residue si formano con la stessa tolleranza
di stacco dei nuclei; si raggruppano con lo stesso Jaccard. Il residuo si
definisce sulle **etichette**, non sull'appartenenza a un record emesso — ed e'
esattamente cosi' che il fallimento era stato silenzioso.

**Il retro-test, che era il criterio vero**: eseguita sul rilevatore
**congelato**, cioe' sul giro che ha fallito in silenzio, l'uscita e' di **due
righe** su 47 pagine, e la prima e':

    4 pagine, 4 corse   pagine [29, 31, 33, 35]   firma: ['Ferocia', 'Resistenza']

Le quattro schede mostro, sulle quattro pagine esatte della verita'. Con questa
misura accesa quel fallimento **non poteva** restare silenzioso.

Altri due esiti:
- **discrimina**: sul manuale 1 il residuo sulle pagine del bestiario e' al
  livello del caso (2 delle 10 pagine peggiori, attese 2,1);
- **trova da sola il compito aperto**: le 6 firme rare ricorrenti del manuale 1
  sono `Massive`, `Brutal/Deadly`, `Minion (6) - Passive`, `Minion (3) -
  Passive` — capacita' rare di avversario, cioe' il caso di
  `COMPITO_APERTO_schede_rare.md`, senza che nessuno gliele indicasse.

Numero da guardare con sospetto e non con soddisfazione: **74,5%** del manuale 1
sta dentro un record. Con 30 gruppi e 477 record, «record» li' dentro vuol dire
molte cose diverse.

---

## 4. Le schede in Markdown: due giri

Criteri `CRITERIO_MARKDOWN_SCHEDE.md` e `CRITERIO_RESA_COMPLETA.md`, risultati
nei due `RISULTATI_*`, codice `markdown_schede.py` (primo giro) e
`markdown_ir.py` (secondo).

**Vincolo rispettato in entrambi**: il Markdown esce da
`markdown_builder.build_markdown(DocumentIR)` del repo, **invariato**. La
conservazione dei caratteri regge sempre, e verificata anche a valle del
renderer: zero caratteri persi.

**Primo giro, un producer solo** (`column_band`): la scheda esce come blocco
delimitato con la nota, ma 2 su 4, un muro di 68 callout su 47 pagine, e gli
elenchi spariti.

**Difetto mio, corretto**: costruivo un `BlockIR` per **riga**, mentre nella IR
del repo il blocco e' il **paragrafo** e la riga sta gia' nella sorgente
(`text:b{block}:l{line}:s{span}`). I marcatori di elenco li **deduco dal
documento** — un'etichetta ricorrente senza caratteri alfanumerici e' un
marcatore: su Dragonbane deduce `–` e `✦`. `ir_builder.py:17` ne tiene una lista
cablata di sei: `✦` c'e', `–` no.

**Secondo giro, tutti e sei i producer** (`markdown_ir.py`):

- **i confini della scheda vengono dal riquadro disegnato**, non dalla pila di
  testa: **4 su 4** contro 2 su 4;
- il criterio «questo riquadro e' una scheda» **non passa dalla frequenza**: un
  riquadro che contiene almeno **due righe con almeno due coppie
  etichetta/valore**. E' `State.md:903` alla lettera. Su tutto il manuale: 5
  regioni = 4 vere piu' una falsa (il riquadro di AZIONI);
- la frase spezzata sparisce: la tabella del d6 e' un blocco di
  `table_candidate` invece di essere tagliata da una testa spuria;
- **43 pagine su 47 portano una nota «ordine di lettura non stabilito»**.

Altri numeri utili:
- estrazione celle di pdfplumber conforme ai caratteri della pagina su **206
  tabelle su 248** (83%): una tabella Markdown vera sarebbe senza perdita su 4
  su 5;
- note d'asset: 1.902 note, 971 file estratti, 262 distinti (15 MB). Restano ~40
  per pagina perche' **le immagini inline non portano `content_digest`**, quindi
  la ripetizione non e' rilevabile per loro;
- sovrapposizioni regione x visuale: 4.208 coppie. Lo sfondo decorativo della
  scheda **non e' ancora sostituito da una nota**: e' il pezzo dell'obiettivo che
  manca.

---

## 5. Cosa e' successo dopo, e perche' riguarda le schede

Il «43 pagine su 47» ha aperto le **Milestone 43 e 44** sull'**ordine di
lettura**, fatte e chiuse (vedi `State.md`). Nascevano numerate 42 e 43 e sono
state rinumerate il 10 settembre 2026, perche' la 42 collideva con una gia'
pubblicata sul ramo dei titoli. Per le schede contano tre cose:

1. **La causa non era quella che sembrava.** Il danno reale (testo affiancato
   letto senza colonne) e' fra lo 0% e il 5,2% del testo di pagina, non il 90%.
2. **La colonna dei numeri di dado di una tabella e' un separatore di colonna**,
   e ora Resolution la ammette. Le tabelle degli attacchi mostruosi delle schede
   ne beneficiano direttamente.
3. **Il percorso Markdown vero e' IR 2**, su un altro ramo. `markdown_ir.py` di
   questa cartella usa IR 1 ed e' un **secondo percorso**: chi continua qui deve
   sapere che sta lavorando sul ramo sbagliato per la resa, e che il lavoro va
   portato su IR 2 come e' stato fatto per la 42/43/44
   (ramo `claude/ir2-porta-42-43`).

---

## 6. Da dove si riparte, in ordine

1. **Correzione 1, la co-occorrenza.** Mai fatta. E la sua valutazione e' oggi
   **inquinata**: il template si forma per conto suo, per conteggio gonfiato.
   Proposta di criterio, da scrivere prima di eseguire: dopo la co-occorrenza la
   firma `Ferocia/Taglia/Resistenza` deve **spostarsi** dal residuo a template, e
   **nessun'altra** firma residua deve farlo. Cosi' l'effetto e' attribuibile.
2. **Il caso del titolo centrato.** La pila di testa non puo' raggiungerlo. Il
   riquadro si'. Proposta: la pila di testa serve dove il riquadro non c'e', non
   al posto suo.
3. **La regola di non-perdita spara nel posto sbagliato**: le uniche 4 regioni
   «struttura non riconosciuta» emesse sono righe di prosa che cominciano con la
   parola *Dragonbane*. Va ristretta a cio' che ha davvero forma di record.
4. **Lo sfondo della scheda come nota.** Non fatto, ed e' meta' dell'obiettivo.
   Il numero (4.208 sovrapposizioni) dice che non e' un caso raro.
5. **Il terzo manuale.** Si apre solo dopo, e solo col criterio scritto prima.

---

## 7. Errori di questa sessione, perche' non si ripetano

- **Ho riportato numeri che non avevo misurato** («il corridoio e' alto ~2
  righe»): dedotti, non misurati, e sbagliati. Il valore vero era a 0,06pt dalla
  soglia.
- **Ho generalizzato da tre casi ispezionati** e l'utente mi ha smentito con
  quindici pagine marcate a mano. Il giudizio a vista ha corretto la conclusione
  tre volte in questa sessione: quando c'e', vale piu' di qualunque misura mia.
- **Ho attribuito male i corridoi** su una pagina che conteneva due tabelle
  tagliate in meta' affiancate, e ho chiamato «errore» del metodo un mio errore
  di lettura.
- **Ho misurato su un manuale solo** e concluso che una variante fosse gratis;
  sul secondo apriva 33 elenchi puntati come colonne.
- **Le predizioni registrate hanno funzionato**: sei su dieci sono cadute, e ogni
  caduta ha insegnato qualcosa. Senza registrarle sarebbero passate per successi
  con un ritocco. **Continuare a scriverle prima.**

---

## 8. Mappa dei file aggiunti in questa sessione

| file | cos'e' |
| --- | --- |
| `CRITERIO_CORREZIONI_2_3.md`, `RISULTATI_CORREZIONI_2_3.txt` | le due correzioni di difetto, non accettate |
| `pila2.py` | `pila.py` con le sole correzioni 2 e 3 |
| `colonne.py` | righe in ordine di colonna dal producer di produzione |
| `misure_correzioni_2_3.py` | le misure M2 e M3 |
| `CRITERIO_COPERTURA.md`, `RISULTATI_COPERTURA.txt`, `copertura.py` | la misura di copertura, accettata |
| `CRITERIO_MARKDOWN_SCHEDE.md`, `RISULTATI_MARKDOWN_SCHEDE.txt`, `markdown_schede.py` | primo giro Markdown |
| `CRITERIO_RESA_COMPLETA.md`, `RISULTATI_RESA_COMPLETA.txt`, `markdown_ir.py` | secondo giro, tutti e sei i producer |

Tutti girano con `./venv/bin/python`. `colonne.py` e `markdown_ir.py` sono gli
unici che importano dal repo, ed e' una scelta dichiarata.
