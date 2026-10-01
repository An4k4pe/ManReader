# La compilazione della scheda in YAML — criterio (scritto prima)

15 settembre 2026, ramo `claude/statblock-markdown-ir2-7b2573`, dopo il commit
`7a90f5e` (fine della scheda) e prima di scrivere il codice.

## Che cosa si mette alla prova
Oggi i campi della scheda escono come prosa, e su DrM staccati dalle etichette:
`1S 6 **Size Speed**`, `M **ight** 0`. Forma scelta dall'utente il 15 settembre:
**YAML**, «soprattutto se poi si puo' implementare un css per la lettura».

Si compila la **parte a campi**: le righe dopo il nome fino all'ultima riga con
etichette della struttura. La parte libera resta com'e', in paragrafi sotto il
blocco YAML. Il nome resta il titolo e non si ripete nel YAML.

**Prima lettura, per struttura, sul documento intero.** Per ogni testo di span
(normalizzato come le etichette) si conta in quante istanze della struttura
compare nella parte a campi. E' il modello: cio' che si ripete in tutte le schede
e' etichetta, cio' che cambia e' valore.

**Seconda lettura, per scheda**, sugli span della parte a campi:

- **righe geometriche**: uno span sta nella riga se il suo centro verticale cade
  nell'altezza del primo span della riga. Le sottocolonne di DrM finiscono nella
  stessa riga, come si leggono sulla pagina;
- **un segno solo**: due span che si sovrappongono in orizzontale sono una parola
  sola (`M` del font di glifi + `ight`);
- **coppia in linea**: la regola di `label_spans` sulle parole. Un'etichetta e'
  seguita da uno stile diverso, e il valore e' la corsa in quello stile. Una corsa
  di soli `:` resta all'etichetta (`PF` + `:` sul Quickstart);
- **coppia impilata**: due righe consecutive senza coppie in linea, con lo stesso
  numero di parole e ogni parola sovrapposta in orizzontale a una sola dell'altra
  riga. E' etichetta la riga i cui testi ricorrono di piu' nel modello
  (`Size`/`Speed` sopra o sotto `1S`/`6`);
- **riga che continua**: una riga senza coppie, nello stile del valore dell'ultima
  coppia della riga prima, prolunga quel valore (`surround, trail` su
  Daggerheart);
- il resto sono **valori senza etichetta**, in ordine di riga.

**In IR 2** la scheda diventa una struttura, come il modello aveva gia' dichiarato
(«alla seconda volta -- callout, scheda mostro -- si allarga questa unione»):
`StatBlockIR2` con campi etichetta/valore e le loro primitive, kind
`layout.stat_block`. Il testo nell'IR resta quello della sorgente; la resa toglie
i `:` finali delle etichette e il separatore finale di un valore (`12 |`), come
il marcatore d'elenco.

**Resa**: blocco ` ```yaml `. Chiavi come stampate; i valori senza etichetta sotto
`text:`, come elenco; una chiave ripetuta diventa un elenco; virgolette solo dove
il YAML le esige.

Tutto sta dietro `--schede-struttura`. La regola di 3a non produce parti a campi.

## Predizioni, scritte prima
- **P1** DrM idx 41 [35]: le quattro schede hanno `Size`, `Speed`, `Stamina`,
  `Stability`, `Free Strike`, `Might`, `Agility`, `Reason`, `Intuition`,
  `Presence`, ciascuna col suo valore. Angulotl Cleaver: 1S, 6, 4, 0, 2, 0, +2,
  0, +1, 0.
- **P2** Daggerheart idx 38, Dire Wolf: `Difficulty` 12, `Thresholds` 5/9, `HP`
  4, `Stress` 3, `ATK` +2, `Experience` Keen Senses +3, `Motives & Tactics` con
  «surround, trail» in coda.
- **P3** Quickstart idx 29, Ragno Gigante: `Ferocia` 2, `Taglia` Normale,
  `Movimento` 24, `Armatura` —, `PF` 36.
- **P4** Senza flag l'uscita resta identica: i quattro giri di confronto e la
  barra E-B (`scripts/check_eb.py`), 9 su 10 con la sola Fab idx 126 diversa.

## Materiale per il giudizio, deciso ora
Gli stessi quattro giri e le stesse nove pagine della fine della scheda (DrM idx
41, 43, 59; Daggerheart 38, 52; Quickstart 29, 31; DB 91, 116), con il Markdown
di prima sopra quello di dopo.

## Soglia di accettazione
Il giudizio a vista dell'utente sulle nove pagine. P1-P3 li controllo io prima di
mostrarle: una predizione che cade si scrive nell'esito, con la sua diagnosi,
prima di toccare la regola.
