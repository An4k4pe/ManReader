# Criterio — quale strategia di tabella risolve meglio

Registrato **prima** della misura. Decide se la strategia del producer va
cambiata, affiancata, o lasciata sola; la posizione dell'utente entrando è
«probabilmente affiancata, ma facciamo delle prove».

## 1. Che cosa vuol dire «meglio», fissato prima

Non «trova più tabelle». Il disegno concordato prende da pdfplumber **la geometria
della griglia** e il testo **dalla sorgente**, quindi la qualità che conta è una
sola:

> **i confini delle colonne non devono cadere dentro il testo della sorgente.**

Lo `span` è l'unità atomica della sorgente. Un confine di colonna che attraversa
la bbox di uno span taglia una parola — è il difetto osservato,
`['rocia: 2 Taglia:', 'ormale']`, dove `Ferocia` ha perso la F.

## 2. Le tre misure, per strategia e per pagina

1. **span tagliati**: quota di span la cui bbox è attraversata da un confine di
   colonna della griglia. **Meno è meglio.** È la misura portante.
2. **regioni risolte**: griglie trovate con ≥ 80% di celle non vuote (stessa
   soglia di `Criterio_TabellaRisolvibile_v1.md`, fissata lì prima di questa).
3. **regioni trovate**: quante griglie in tutto. Si riporta, non decide: una
   strategia che trova molto e taglia molto non è migliore.

## 3. Le strategie confrontate, elencate prima

- `lines` / `lines` — default, basata sui filetti
- `text` / `lines` — **quella del producer**, Milestone 20
- `lines_strict` / `lines_strict`
- `text` / `text`

## 4. Regola di lettura, fissata prima

- **Cambiare**: una strategia taglia **meno** span **e** risolve **almeno quante**
  regioni di `text/lines` su ≥ 80% delle pagine del campione.
- **Affiancare**: nessuna domina, cioè una taglia meno e l'altra risolve di più.
  In quel caso serve **una regola di scelta per regione**, che questo criterio non
  fornisce e che va decisa a parte.
- **Lasciare sola `text/lines`**: nessuna la batte su nessuna delle due misure.

## 5. Il campione, non scelto da Chat A

12 pagine estratte uniformemente, **seed `20260821`**, dal pool dei 16 manuali,
escluse per costruzione le pagine già usate in questa sessione. Riportato quante
pagine non contengono alcuna griglia con nessuna strategia: sono pagine su cui la
domanda non si pone, e vanno tolte dai denominatori invece che contate come
successi.

## 6. Limite dichiarato prima

Misura la **geometria della griglia**, non la bontà dell'estrazione del testo di
pdfplumber, che nel disegno concordato non viene usata. Se un giorno il testo
venisse da lì, questa misura non direbbe nulla su quel punto.

E non decide se `table_candidate` vada modificato: dice quale strategia taglia
meno. Modificare un producer wired ha oracoli propri (Milestone 20, Dag p.137,
114/57 primitive) che vanno rieseguiti a parte.
