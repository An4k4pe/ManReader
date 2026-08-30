# Criterio — v2: **la finestra si sposta, non si allarga**

Emenda `Criterio_AmbitoDeiFatti_v1.md`. Il §0 di quel criterio — la diagnosi —
resta intero e verificato. Cade il §1, la separazione in due ambiti.

## 0. Che cosa è caduto della v1, e perché non è un salvataggio

La v1 divideva i fatti in due ambiti e misurava prosa, livelli, marcatori e firme
di scala su **tutte** le pagine. Misurato:

```
FWK   prosa da  6 dimensioni a 14      livelli da 5 a 2   (15,0 16,0 20,0 30,0 diventano PROSA)
Dag   prosa da  4 dimensioni a 23      livelli da 8 a 21  (comprese 2,8 e 3,0)
FWK   firme di scala: 0 → 1, ('*','•') — e spegne le quattro voci d'elenco di idx 122
```

`prose_sizes` taglia al **salto più grande fra le mediane** delle lunghezze di
riga. Quel taglio **non è invariante di scala**: con più dimensioni in gioco lo
spazio fra le mediane si riempie, il salto più grande si sposta, e il confine
prosa/titolo finisce altrove.

> **Dare a una statistica non invariante di scala una popolazione di taglia
> diversa è sbagliato a prescindere da come va a finire.** È la prova che
> `AGENTS.MD` §20 chiede: l'emendamento regge senza sapere se il meccanismo poi
> passa.

La v1 aveva ragione sul difetto — la finestra stava nel posto sbagliato — e torto
sul rimedio: ha cambiato **due cose insieme**, dove stava la finestra e quanto era
larga, e la seconda ha rotto ciò che la prima riparava.

## 1. La regola

> **Una finestra sola, della taglia di oggi, che contiene la pagina che si sta
> rendendo.** Tutti e sei i fatti si misurano su quella.

Non si allarga niente. L'ambito documento resta **chiuso**, e ci si torna solo
quando `prose_sizes` sarà invariante di scala — che diventa un problema aperto
con un nome.

## 2. Che cosa si guadagna, misurato sulle dieci pagine

### I titoli che mancavano

```
BiD idx 287   whitecrown       28,0 su prosa 9,6     →  ## **whitecrown**
Wil idx  71   IL BANCHETTO     37,0 su prosa 10,0    →  ### **IL BANCHETTO**
                                                     →  ### **PREPARARE IL BANCHETTO**
```

### L'arredo che il giudizio aveva segnalato

Sei esclusioni nuove, e **cinque sono esattamente i rilievi dell'utente**:

```
Vil idx  64   'Personaggi 61'   ← «è capitolo e numero pagina, da togliere»
FWK idx  31   'Capitolo 2'      ← «Capitolo 2 da eliminare»
FWK idx  31   '32'              ← «numero di pagina presente nel file»
Wil idx  71   '72'              ← il numero di pagina
Fab idx 126   'CAPITOLO'        ← «CAPITOLO … non ci dovrebbe essere»
```

## 3. Che cosa si perde, e va guardato

### A. Una esclusione non richiesta — **decide una persona, non io**

```
BiD idx 287   'punti di riferimento'   esce dal corpo, e nessuno l'aveva chiesto
```

Ricorre su **6 pagine su 20 a un solo slot**, quindi il ramo delle testatine la
prende. Ma le altre «testatine» trovate su quella finestra sono:

```
Benessere · DETTAGLI · Influenza Criminale · Influenza Occulta · Scene: · Sicurezza · TRATTI
```

Sono **etichette di una scheda ripetuta**, non testatine. È il debito delle schede
per la **quinta** volta, e con un profilo nuovo: il ramo regge quando i campi si
spostano col contenuto — `Stamina` di DrM sta su 31 slot — e cade quando la scheda
ha campi a **posizione fissa**. Spostare la finestra sulla pagina la concentra su
una corsa di schede, e il diluente sparisce.

> Se `punti di riferimento` è contenuto, **la barra B cade** e questa modifica si
> ritira. Non lo decido io: è la barra che ha già fatto cadere due clausole
> d'arredo, e vale solo se la giudica una persona.

### B. Tre titoli su Wil, scambiati con due

```
prima   ### ◊COME STAI CUCINANDO IL MOSTRO?  · ◊COME STAI CONTRIBUENDO… · ◊COS'ALTRO SERVIRETE…
dopo    ### IL BANCHETTO  ·  ### PREPARARE IL BANCHETTO
```

Il conto va da tre a due. I due nuovi sono quelli che il giudizio ha chiesto; i
tre vecchi sono domande di scheda, che nessuno aveva segnalato né come giuste né
come sbagliate.

### C. Otto voci d'elenco false su Fab

```
- 2   - 2   - 2   - 3   - 2   - 2   - 2   - 3
```

Cifre sole promosse a voci, sulla pagina che è una tabella. **La barra E della v1
non le vede**: era scritta «le voci non devono calare», e queste salgono. È un
veto nella moneta sbagliata, scritto da me, ed è la seconda volta in questa
sessione.

## 4. Pass/fail, riscritte

### A. Il contenuto si conserva — **invariata**

> Nessuna pagina perde testo dal corpo **e** dal review insieme.

### B. L'arredo non porta via contenuto — **in attesa di giudizio**

> Cade se una sola cosa uscita dal corpo è giudicata contenuto.

Aperta su `punti di riferimento`. Le altre cinque sono richieste esplicite.

### C. I due titoli — **passa**

### D. Le voci d'elenco, nella moneta giusta

> Non basta che non calino: le voci **aggiunte** vanno guardate, e una voce che è
> una cifra sola non è una voce.

Riscritta qui perché la v1 era cieca per costruzione. Al momento: **8 false su
Fab**, e la barra è violata.

## 5. Il problema aperto che questo giro apre con un nome

**`prose_sizes` non è invariante di scala.** Finché il taglio al salto più grande
resta, il confine prosa/titolo dipende da quante pagine gli si danno — e un
meccanismo document-level che cambia col campione non è document-level. È il
prerequisito di qualunque ritorno all'ambito documento.
