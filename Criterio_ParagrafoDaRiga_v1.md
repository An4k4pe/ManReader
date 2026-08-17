# Criterio di accettazione — il paragrafo viene dalla riga, non dal blocco

Scritto **prima** dell'implementazione, e committato in un commit che non contiene
nulla dell'implementazione. La precedenza deve restare dimostrabile per diff.

**Supera `Criterio_ParagrafoDaBlocco_v1.md`, non lo emenda.** Quel criterio non
viene ritirato come metodo — le sue due invarianti restano, rafforzate — ma il suo
meccanismo cambia: il paragrafo non viene dal blocco.

---

## 1. Cosa cambia

**L'atomo è la riga della sorgente** (`text:b{block}:l{line}:s{span}`, il livello
`line`), non il blocco. Il blocco smette di decidere alcunché.

1. **Dentro una riga si concatena** senza separatore, ordinando per `span_index`.
2. **Fra due righe consecutive si va a capo** se una di queste è vera; altrimenti
   si uniscono con un singolo spazio:
   - la riga successiva **non** comincia in minuscola;
   - la riga precedente finisce con `.` `;` `!` `?`;
   - la riga precedente finisce con `:` **e** la successiva comincia con un
     trattino o una cifra (guardia elenchi).
3. **De-sillabazione** con `_HYPHENATED_WORD_RE` di `ir_builder.py:18`, alle sue
   condizioni: lettera prima del trattino, minuscola dopo. Non il solo trattino
   finale.

Il `:` **non** termina il paragrafo — a differenza di
`_ends_with_strong_punctuation` (`markdown_builder.py:164`) — ed è ciò che tiene
`Non-Mostri:` attaccato al proprio testo.

## 2. Perché, con la pagina

**DB p.99 posizionale (stampata 97, verificata a render).** Box *Non-Mostri*, tre
voci a rientro sospeso. I blocchi le tagliano di traverso:

```
b0003: 'contano come mostri, ma come normali PNG.' | 'Resistenza: … sono dimez-'
b0004: 'zati (arrotondando per eccesso).'          | 'Immunità: … alla paura e '
```

`b0003` contiene la fine della prima voce **e** l'inizio della seconda; e il
confine cade anche in mezzo alla parola `dimez-`/`zati`, quindi la de-sillabazione
applicata dentro il blocco non scatta mai.

Applicando le regole del §1 **fra righe**, su DB p.99: 46 righe → 33 paragrafi, e
il box esce in tre voci corrette. Si ricongiunge inoltre la prosa spezzata fra le
due colonne.

**Affermazione ritirata**, registrata perché non venga riusata: che il confine di
voce fosse visibile «solo nel rientro» e richiedesse geometria. È falso — lo porta
il testo. Il rientro resta **scartato** come segnale, per la ragione dell'utente:
è impaginazione, e non vale in tutti i manuali.

## 3. Le due invarianti, e come cambiano

**I1 — conservazione** e **I2 — nessun riordino** di
`Criterio_ParagrafoDaBlocco_v1.md` §2 restano il metro. Ma la regola 3 **le rompe
entrambe**, e va dichiarato invece che scoperto: un trattino è un carattere
non-spazio, quindi toglierlo cambia sia il multiset sia la sequenza.

**Emendamento, esplicito e limitato:**

> I1 e I2 si valutano su un testo da cui è stata rimossa **ogni occorrenza che
> `_HYPHENATED_WORD_RE` rimuoverebbe**, applicata a entrambi i lati del confronto.
> Nessun'altra differenza di caratteri non-spazio è ammessa.

Questa è l'unica esenzione. Se il confronto mostra una qualunque differenza che
non sia una sillabazione rimossa dalla regex, il giro **fallisce**.

L'invariante eseguibile della fetta (`_verify_content_conservation`) va aggiornato
alla stessa forma, non aggirato con un'eccezione locale.

## 4. Precondizione: DB p.53

`Criterio_ParagrafoDaBlocco_v1.md` era stato verificato su **DB p.53** (`b3`
paragrafo di prosa su tre righe, `b4`-`b7` quattro voci di elenco una per blocco).
Il meccanismo nuovo va provato **lì per primo**.

- **Regge** se su DB p.53 le regole del §1, senza usare il blocco, producono la
  stessa segmentazione che il blocco produceva: un paragrafo di prosa e quattro
  voci distinte, e le tre voci `Esausto`/`Malaticcio`/`Disorientato` su tre righe.
- **Cade** se il blocco lì serve ancora. In quel caso il blocco non si supera: si
  tiene come default e le regole del §1 lo scavalcano, e questo criterio va
  riscritto prima di procedere.

Dichiarato prima di guardare, perché è la pagina su cui il criterio precedente era
stato costruito e quindi quella con più probabilità di smentire il nuovo.

## 5. Giudizio a vista

Vanno rilette le pagine già giudicate dall'utente, perché cambia dove il testo
viene spezzato: DrW p.97, Dag p.164, DB p.50, DB p.53, DB p.99.

Il giro regge se **non compare nessuna pagina in cui la segmentazione peggiora**.

## 6. Riserve dichiarate

- **La guardia elenchi non è stata esercitata**: su DB p.99 zero righe finiscono
  con `:`. Va provata su una pagina che ne contenga, e finché non lo è va trattata
  come non verificata.
- Le righe vengono dallo stesso livello `dict` che su Kul p.233 è degenere
  (`State.md:68`). Dove la cattura degenera degenerano anche le righe; resta la
  milestone sul rilevatore di degenerazione, non toccata qui.
- Le regole 2 e 3 sono **sul testo**, non sulla geometria, ma restano euristiche:
  una riga che finisce senza punteggiatura e continua con una maiuscola verrà
  spezzata anche quando la frase prosegue. Nessuna misura di quanto sia frequente.

## 7. Dopo

L'esito si scrive, e **nessun altro giro viene proposto dall'interno di questo**.
