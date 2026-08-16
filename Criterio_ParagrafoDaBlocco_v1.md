# Criterio di accettazione — il paragrafo viene dal blocco

**AVVISO — questo file è stato modificato DOPO l'implementazione.** Il §3
contiene una postilla aggiunta a implementazione avvenuta, che **rilassa** P0.
Rilievo della revisione indipendente: l'intestazione dice «scritto prima» e il
file in HEAD non è quello pre-registrato, quindi per questo criterio la
precedenza va stabilita per diff (`git diff 177f52c..HEAD -- Criterio_ParagrafoDaBlocco_v1.md`),
non letta qui. Il rilassamento di un criterio di accettazione dopo aver visto il
risultato è il caso in cui la distinzione conta di più, e va segnalato in testa,
non solo etichettato dove sta.

Scritto **prima** dell'implementazione, come i due criteri precedenti di questa
sessione. La decisione non è in discussione — è una posizione permanente
dell'utente, ribadita qui per la terza volta: *la ricostruzione geometrica del
testo ha già fallito altre volte, si usa solo come posizionamento o controllo
della posizione, il testo deve arrivare da dove lo salva PyMuPDF.* Quello che
questo criterio fissa è **come si verifica** che il cambio non rompa altro.

---

## 1. Cosa cambia

La regola di paragrafo smette di dedurre l'interruzione dalla sovrapposizione
delle y fra primitive consecutive e la legge da `block_index`
(`source_observation_id`, formato `text:b{block}:l{line}:s{span}`). Blocco nuovo
→ paragrafo nuovo.

Verificato su DB p.53 che il blocco **sia** il paragrafo: `b3` è un paragrafo di
prosa su tre righe, `b4`-`b7` sono quattro voci di elenco, una per blocco.

Cade con essa la pezza aggiunta poche ore fa («una primitiva senza testo non fa
da termine di paragone»): serviva solo perché su DB p.53 uno span vuoto con
bbox più alto faceva da ponte fra due voci. Con il paragrafo letto dal blocco
quel ponte non esiste. **Una pezza che cura un sintomo di una deduzione che non
deve esserci va tolta insieme alla deduzione**, non lasciata come cintura di
sicurezza.

Perimetro: i tre emettitori di testo (`_build_markdown_body` e
`_ordered_markdown_body` nella fetta verticale, `_render` nel confronto),
tenuti sulla stessa definizione di proposito — su questo progetto due
definizioni della stessa cosa sono già divergute una volta.

## 2. Le due invarianti che devono reggere

- **I1 — conservazione**: il multiset dei caratteri non-spazio resta identico su
  tutte le varianti di tutte le pagine provate. È l'invariante che la fetta
  verifica già da sola, con uscita `4`.
- **I2 — nessun riordino**: questo cambio tocca **dove si va a capo**, non
  l'ordine. Quindi la **sequenza** dei caratteri non-spazio, letta a nastro
  ignorando ogni spaziatura e ogni interruzione di riga, deve restare
  **identica** carattere per carattere. È più forte di I1, che è cieco
  all'ordine, ed è esattamente il buco che State.md:76 segnala nell'invariante
  di Milestone 36.

I2 è la verifica portante: se regge, tutto ciò che è cambiato è la
segmentazione in paragrafi, che è ciò che vogliamo cambiare.

## 3. P0 cambia, ed è dichiarato

Nei due criteri precedenti P0 era «`page.md` resta identico byte per byte».
**Qui non può reggere e non deve**: `page.md` usa la stessa regola di paragrafo
difettosa, e lasciarcela vorrebbe dire tenere per buono un artefatto di
Milestone 36 che sappiamo sbagliato.

**Postilla dopo l'implementazione, rilievo dell'utente**: quel P0 era comunque
troppo stretto. `page.md` non è un producer né un artefatto definitivo — lo
dicono sia la docstring dello script («diagnostic prototype, not production
code»; la regola di paragrafo è «a diagnostic display choice for this
prototype … carries no weight beyond this script») sia `State.md` su
Milestone 36 («l'emettitore diagnostico **non è** il punto di partenza del
renderer IR-first»). Non c'era nulla da preservare byte per byte. Come guardia
contro un cambio **silenzioso** introdotto da un flag restava utile, ed è per
quello che era nato; l'invariante che porta davvero il peso è I2.

P0 diventa quindi: **`page.md` può cambiare solo nelle interruzioni di
paragrafo**, e la prova è I2 applicata a lui. Un cambio dichiarato e verificato
non è un cambio silenzioso, che è ciò contro cui P0 esisteva.

## 4. Giudizio a vista

Le pagine già giudicate dall'utente vanno **rilette**, perché cambia come il
testo viene spezzato e non solo come viene ordinato: DrW p.97, Dag p.164,
DB p.50, DB p.53. Su DB p.53 il risultato atteso è che le tre voci
`Esausto`/`Malaticcio`/`Disorientato` tornino su tre righe **senza** la pezza
sullo span vuoto.

Il giro regge se non compare nessuna pagina in cui la segmentazione peggiora.

## 5. Riserva dichiarata

I blocchi vengono dallo stesso livello `dict` che su Kul p.233 è degenere
(State.md:62). Dove la cattura degenera, degenerano anche i blocchi — ma lì
degenera pure la geometria, quindi non è un argomento per tenere la deduzione.
Resta la milestone sul rilevatore di degenerazione in cattura, non toccata qui.

## 6. Dopo

Come i due criteri precedenti: l'esito si scrive e **nessun altro giro viene
proposto dall'interno di questo**.
