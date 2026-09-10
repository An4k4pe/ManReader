# Milestone 44 — V4: le colonne di tabella diventano bande. Piano e criteri

Aperta su decisione dell'utente dopo la chiusura diagnostica della Milestone 43
(`Verbale_Milestone43_v1.md`). Questa e' **implementazione**, non diagnostica: i
numeri ci sono gia' e non vanno rimisurati, vanno rispettati.

## Obiettivo unico
Far si' che un corridoio verticale **dentro una tabella** con un lato che non
porta parole (la colonna dei numeri di dado) smetta di sparire, e diventi
disponibile come struttura di colonna — senza toccare nessuna soglia e senza
cambiare il comportamento fuori dalle tabelle.

## Cosa e' gia' stabilito, e non si rimisura
Su 14 corridoi giudicati a vista dall'utente su 15 pagine di DB:

| regola | verita' | DB 126 pag. | Apo 148 pag. |
| --- | --- | --- | --- |
| V0, oggi | 5/14 | 326 bande | 47 |
| V1, somma >= 5 | 13/14 | 354 | 69 |
| V3, lato non vuoto | 14/14 | 358 | 102, di cui **33 fuori tabella** |
| **V4, non vuoto in tabella** | **14/14** | **357, 0 fuori** | **69, 0 fuori** |

V4 = dentro un `table_candidate`, si scarta solo se un lato somma **zero**
caratteri; fuori, `too_few_wordy_lines` resta identico. Zero costanti nuove.

## Il vincolo architetturale, ed e' il cuore del piano
V4 usa l'uscita di **un altro producer**. `AGENTS.MD` §Layout e candidati:
«la relazione fra candidati di producer diversi si decide in Resolution o nel
consumer, **mai dentro un producer**». Quindi V4 **non** e' una patch dentro
`page_analysis_column_band.py`, e chi la scrivesse li' violerebbe l'invariante
che questa milestone esiste per rispettare.

Ma c'e' un secondo ostacolo, meno ovvio: **Resolution decide su candidati
emessi**. Oggi il corridoio scartato non diventa candidato e non lascia traccia
in nessun artefatto: non c'e' niente su cui decidere. Prima di poter applicare
V4, l'informazione deve smettere di essere buttata.

Il producer lo dice gia' di se stesso (`_reject_reason`, docstring): «uno scarto
etichettato e' materiale per i producer successivi. Un gutter con un solo
carattere numerico per lato e' un forte indizio di TABELLA — e va passato a chi
rileva tabelle, non perso». Oggi non lo passa a nessuno.

## Le due strade, con la raccomandazione
**A — misura satellite dei corridoi scartati.** Un modulo nuovo emette, per
pagina, i corridoi che l'ammissione ha respinto, con il loro profilo (righe di
fianco per lato, caratteri sommati per lato, altezza in righe di pagina, motivo).
Nessun candidato nuovo, nessun `structural_kind` nuovo, **nessun consumer cambia
comportamento**. Chi vuole V4 combina tre cose gia' esistenti: bande, corridoi
scartati, `table_candidate`.

**B — candidato con `structural_kind` proprio.** Il corridoio scartato diventa un
`RegionCandidate` di tipo distinto. Piu' diretto, ma cambia la superficie del
contratto per **tutti** i consumer, e obbliga a battezzare adesso una categoria
che nessun consumer ha ancora chiesto.

**Raccomandata: A.** Rischio di regressione zero, e' il passo piu' piccolo che
smette di buttare l'informazione, ricalca il precedente di Milestone 33 (cio' che
un candidato minimale non puo' portare va in una misura satellite), e rimanda la
decisione di categoria a quando un consumer la chiedera' davvero.

## Piano in tre fasi
- **Fase 1 — la misura.** Modulo nuovo `page_analysis_column_band_rejected_gutters.py`
  (nome provvisorio) piu' i suoi test. Osserva, non decide. Nessuna modifica a
  `page_analysis_column_band.py` se non l'estrazione della funzione che gia'
  calcola i corridoi, **senza cambiarne il comportamento**.
- **Fase 2 — la decisione V4.** Dove va scritta e' la scelta A/B qui sopra; con A
  vive in Resolution (`resolution_page_candidates.py`, dove Milestone 34 ha messo
  la prima regola) oppure nel consumer. Consuma misura + `table_candidate`.
- **Fase 3 — la lettura per righe delle tabelle.** Obbligatoria e non rinviabile
  oltre la 2: una banda a due colonne su una tabella la fa leggere «tutti i
  numeri, poi tutte le descrizioni». **Se la Fase 2 entra in produzione senza la
  Fase 3, le tabelle peggiorano invece di migliorare.** E' scritto qui perche'
  non venga dimenticato quando la 2 sembrera' finita.

## Criteri di accettazione, fissati prima
- **Fase 1**: i 14 corridoi verificati compaiono nella misura con il profilo
  gia' misurato (somme e righe di fianco identiche a quelle del verbale della
  42); nessuna banda cambia su DB e Apo (conteggi invariati: 326 e 47);
  ruff verde, basedpyright 0/0/0, suite completa verde.
- **Fase 2**: sui 14 corridoi la regola decide **14 su 14**; su DB **+31 bande,
  0 fuori tabella**; su Apo **+22 bande, 0 fuori tabella**. Numeri gia' misurati:
  se l'implementazione ne da' altri, e' l'implementazione a essere sbagliata.
- **Fase 3**: su una pagina di tabella verificata a vista, l'ordine emesso e' per
  righe e non per colonne.

## File ammessi e vietati
Ammessi in Fase 1: il modulo nuovo, i suoi test, e `page_analysis_column_band.py`
**solo** per esporre senza modificarlo il calcolo dei corridoi.
Vietati in ogni fase: qualunque soglia (`min_flanking_chars`,
`min_flanking_groups`, `min_gutter_lines`, `bin_*`); la pipeline legacy;
`markdown_builder.py`; i renderer; EPUB; gli altri cinque producer.

## Fuori scope, dichiarato
Il terzo manuale sigillato; le pagine Apo marcate (l'ispezione ha gia' risposto);
la frammentazione delle bande; il caso `too_short` sul filo; qualunque
riformulazione di `too_few_wordy_lines` fuori dalle tabelle.
