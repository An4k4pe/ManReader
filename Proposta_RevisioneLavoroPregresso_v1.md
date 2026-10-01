# Proposta — cosa va rivisto, ora che IR 2 è il bersaglio

Secondo documento, su rilievo dell'utente: *«nelle tue proposte sopra spesso
abbiamo girato a vuoto cercando di fare cose inutili e andranno riviste»*.

Il metro nuovo, che vale da qui in avanti: **non si costruisce niente che non
finisca in `page_ir2.md`.** Questo documento applica quel metro all'indietro e
dice cosa resta, cosa cade e cosa va rifatto — perché un lavoro pregresso non
rivisto viene ricitato come valido.

---

## 1. Ha girato a vuoto, e va archiviato

**I tre criteri sulla discriminazione scheda/tabella.**
`Esito_RegolaritaTableCandidate_v1.md` e `Esito_SeparatoriVariabili_v1.md` sono
caduti; `Criterio_TabellaRisolvibile_v1.md` è registrato e mai eseguito. Tutti e
tre al livello dei candidati, **nessuno con un'uscita**.

Cosa resta di buono, e non è poco: entrambi i verbali registrano **perché** sono
caduti, e la causa è la stessa — i segnali dipendono da come la cattura ha
raggruppato il testo, e quel raggruppamento cambia fra due pannelli identici dello
stesso manuale. È un fatto sulla cattura, non sulla scheda, e vale per chiunque
proverà a discriminare qualcosa al livello dei candidati.

**Il terzo criterio va tenuto registrato** ma spostato: la sua domanda — «questa
regione si risolve?» — diventa un **dato della misura satellite** della proposta
sulle tabelle, cioè finisce in un'uscita. Da criterio a sé a effetto collaterale
di qualcosa che serve.

## 2. Sono state utili, e restano

**`Esito_StrategiaTabella_v1.md`.** La misura sulle strategie è servita e serve:
seleziona `lines/lines` come base ed è la guardia A3 della proposta sulle tabelle.
Il suo limite dichiarato — 5 pagine utili, non 12 — resta.

**Milestone 38 e i suoi verbali.** IR 2 esiste, E‑B è 10 su 10, il campione cieco
è giudicato. È il lavoro che ha prodotto il bersaglio.

**Le rettifiche alla chiusura.** Quattro affermazioni dichiarate più forti del
codice, scritte invece che nascoste.

## 3. Va rifatta

**`Proposta_IR2Minima_v1.md` e `_v2.md`.** Rifinivano la nota d'asset dentro uno
script diagnostico. La v1 è già ritirata con la sua ritrattazione in testa; **la
v2 non lo è**, e va marcata: la sua diagnosi — «la nota non riassume» — è stata
sostituita dalla v3, e citarla oggi darebbe una causa sbagliata.

**`Domanda_NodoTabellaIR2_v1.md`.** La revisione ha mostrato che «Chat A non ha
una preferenza» non regge alla lettura: C era l'unica con precedente «forte» e
problemi attenuati ed è l'opzione che non compila; D era condannata con la parola
«riassemblare» usata impropriamente — le tre correzioni agli atti riguardano il
riassemblaggio **geometrico** del testo, non il raggruppare nodi per un id
dichiarato; E si autoproclamava vincente nel titolo. Il documento è superato da
`Proposta_TabellaInIR2_v1.md` e va marcato come tale, con il rilievo dentro.

## 4. Resta aperta e non è stata toccata

In ordine di quanto blocca l'uscita:

1. **Nel percorso IR 2 non esiste un invariante di conservazione dei caratteri.**
   Il validatore garantisce la copertura per **id di primitiva**, non che i
   caratteri ci siano. Su questo lo stadio nuovo è **più debole della fetta**, che
   esegue `_verify_content_conservation` a ogni giro. È la cosa più grossa aperta
   su IR 2 e non dipende dalle tabelle.
2. **L'ancora delle note d'asset** è per `y` e sbaglia colonna su due colonne.
   Dichiarata e localizzata nel chiamante, non risolta.
3. **I glifi dei badge sono minuscole per la codifica** (`á` = U+00E1), quindi la
   regola di paragrafo li legge come prosa che continua. Difetto locale, causa
   nota, chiudibile senza aprire niente — su DrW p.97 chiude due sintomi.
4. **L'interruzione del corridoio dai filetti** è misurata (su cinque pagine non
   rompe niente e ne aggiusta due) e **spenta**. Accenderla cambia l'ordine,
   quindi la base di E‑B va rigenerata **e rigiudicata**.
5. **La rimozione dell'arredo**: 65 nodi in review sulle dieci pagine, di cui 55
   `embedded_visual`. `content_digest` non separa i filetti.
6. **La milestone di uscita dallo shadow mode** continua a non esistere, e ora c'è
   un secondo emettitore Markdown accanto al legacy.

## 5. Cosa propongo, in ordine

1. **Le tabelle in IR 2** (`Proposta_TabellaInIR2_v1.md`) — è il bersaglio, ed è
   l'unica di queste che aggiunge una cosa che si vede nell'uscita.
2. **L'invariante di conservazione dei caratteri**, prima o insieme: senza, ogni
   cosa che si aggiunge a IR 2 può perdere contenuto passando i controlli. È
   piccolo e chiude un buco noto.
3. **I glifi**, quando capita: costa poco e chiude due sintomi.

Il resto aspetta, dichiarato.

## 6. Decisione presa mentre questo documento esisteva

**Forma della tabella: un nodo con dentro la griglia**, non le celle come nodi.
La condizione che l'avrebbe ribaltata — la correzione umana per cella — è stata
posta all'utente e non si dà, per una ragione che viene dall'obiettivo e non da
una preferenza: il prodotto è di **consultazione**. La §3.1 di
`Proposta_TabellaInIR2_v1.md` è chiusa.
