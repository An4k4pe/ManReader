# Esito di `Criterio_RotturaParagrafo_v2.md` — **regge, sul tetto**

**Stato in una riga**: il confronto A/B cieco dà **12 a 2 con 4 pari**, la
conservazione tiene su tutte e 40 le pagine, i tre controlli a vista passano. Il
criterio regge su tutte e tre le clausole — ma il vecchio vince su **esattamente
2** pagine, che è il tetto: una in più e sarebbe caduto.

---

## 1. Il §4 — il confronto A/B

18 coppie sulle 20 pagine del primario, mai giudicate da nessuno prima. Due
pagine (SV idx 198, BoB idx 62) escono **identiche** fra le due versioni e sono
state escluse: fra due file uguali non c'è niente da giudicare. Le coppie
giudicabili sono quindi 18 e non 20, il che rende la barra **più severa** di come
era stata scritta — «almeno 10» su 18 invece che su 20. Non è stata toccata.

| | |
| --- | --- |
| **nuovo vince** | **12** |
| **vecchio vince** | **2** |
| pari | 4 |

> Barra del §4: nuovo ≥ 10 **e** vecchio ≤ 2. **REGGE.**

L'assegnazione A/B è stata estratta a sorte per pagina col seed `20260825`,
dichiarato nella v1 del criterio prima che il codice esistesse, e la chiave non è
stata aperta finché tutte e 18 le risposte non erano date.

**Il margine sulla seconda condizione è nullo.** Va citato così: il criterio ha
retto con il vecchio esattamente sul tetto, non con due pagine di margine.

### 1-bis. Le 18 risposte e la chiave

Il §1 riportava solo l'aggregato, e il numero non era ricontrollabile da nessuno.
La lacuna si è vista quando la cartella di lavoro è stata ripulita e il file
della chiave è sparito: quelle risposte esistevano **solo nella conversazione**.

**La chiave è però riproducibile dal solo materiale committato**, e lo è stata:
il seed `20260825` sta nel criterio, l'ordine delle pagine in
`Campione_FormaMancante_v1.md` righe 21-40, e le due pagine identiche sono
nominate qui sopra. `scripts/build_ab_comparison.py` estrae un numero casuale
**solo** per le pagine non identiche, quindi la sequenza dipende unicamente da
quei tre dati. Riprodotta e verificata: **18 su 18 identiche**.

| # | pagina | A | B | risposta | vince |
| --- | --- | --- | --- | --- | --- |
| 01 | Lan idx 20 | vecchio | NUOVO | B | **NUOVO** |
| 02 | SV idx 3 | NUOVO | vecchio | A | **NUOVO** |
| 03 | Dag idx 251 | NUOVO | vecchio | B | vecchio |
| 04 | Wil idx 72 | vecchio | NUOVO | B | **NUOVO** |
| 05 | Kul idx 219 | NUOVO | vecchio | uguali | pari |
| 06 | Lan idx 364 | NUOVO | vecchio | A | **NUOVO** |
| 07 | DIE idx 399 | vecchio | NUOVO | B | **NUOVO** |
| 08 | DIE idx 382 | vecchio | NUOVO | B | **NUOVO** |
| 09 | Vil idx 208 | vecchio | NUOVO | B | **NUOVO** |
| 10 | SV idx 369 | vecchio | NUOVO | uguali | pari |
| 11 | Fab idx 171 | NUOVO | vecchio | A | **NUOVO** |
| 12 | Fab idx 286 | vecchio | NUOVO | uguali | pari |
| 13 | DrM idx 172 | vecchio | NUOVO | B | **NUOVO** |
| 14 | DrM idx 184 | NUOVO | vecchio | A | **NUOVO** |
| 15 | Lan idx 116 | vecchio | NUOVO | B | **NUOVO** |
| 16 | Fab idx 118 | vecchio | NUOVO | uguali | pari |
| 17 | DrW idx 272 | NUOVO | vecchio | B | vecchio |
| 18 | Fab idx 142 | vecchio | NUOVO | B | **NUOVO** |

Le due sconfitte, righe 03 e 17, hanno la causa verificata nel §5.

## 2. Il §5 — l'errore squalificante

> conservazione: **OK su tutte e 40 le pagine**

Multiinsieme dei caratteri di tutti i nodi `text.paragraph` identico prima e
dopo, spazi e trattini esclusi.

**Trattini: 71 prima, 71 dopo, calo zero.** Il criterio si aspettava un calo
proporzionale alle giunzioni nuove, e non c'è. La spiegazione regge ed è
verificabile: le giunzioni che la regola nuova aggiunge cadono su inizi
**maiuscoli**, che non sono punti di sillabazione — quelli la regola vecchia li
univa già, perché la continuazione di una parola spezzata comincia in minuscola.

## 3. Il §6 — i tre controlli a vista

| controllo | paragrafi vecchio → nuovo | giudizio |
| --- | --- | --- |
| DB p.99 | 39 → 28 | non peggiora |
| DrW p.97 | 44 → 31 | non peggiora |
| Fab p.248 | 16 → 14 | non peggiora |

Giudizio dell'utente sulle tre: «il nuovo mi sembra un miglioramento netto».

Il terzo controllo era stato **aggiunto in v2 dopo aver visto il difetto** dei
glifi simbolici, e dichiarato come tale: rendeva il criterio più severo, non più
permissivo.

## 4. La regola, come è stata implementata

> Si rompe dove cambia il blocco di sorgente, a meno che la riga successiva non
> cominci con un carattere minuscolo **del font del corpo**.

Tre segnali già presenti nella pipeline, **zero parametri**: `block_index` dal
`source_observation_id`, il carattere iniziale della riga successiva, e il
`font_name` di quel carattere.

**Una deviazione dalla lettera del criterio, dichiarata.** Il §1 diceva «la moda
dei `font_name` delle **primitive** testuali». Contando le primitive, il font del
corpo di DB p.99 risulta `Hideout-Bold`: una pagina di schede ha molte righe
corte in grassetto e poche righe lunghe di prosa. Pesando per **caratteri** dà
`Hideout-Regular`, ed è quello giusto. Misurato contro le etichette dell'utente
su quella pagina: **37 giunzioni corrette su 43 contando le primitive, 40
contando i caratteri.** Il vincolo che conta — desunto dalla pagina, mai un
elenco — regge in entrambi i casi.

**Il ruolo del test lessicale si è rovesciato.** Prima *imponeva* una rottura
quando la riga dopo non era minuscola; ora può solo *vietarne* una che il confine
di blocco ha già proposto. Il suo modo di fallire passa da «rompe troppo» a
«rompe troppo poco».

## 5. Il residuo, misurato e con la causa verificata

> **La regola non può rompere dentro un blocco.**

È l'unica causa delle due sconfitte, verificata su entrambe.

**Dag idx 251.** Le cinque voci `• Successo Critico: diminuisce di 3`, `•
Successo con Speranza…` stanno **tutte dentro `b0004`**, e titolo e sottotitolo
dentro `b0000`. Il blocco non cambia mai, quindi nulla si rompe e la pagina esce
da 46 paragrafi a 17. La regola vecchia le prendeva perché `•` non è minuscola.

**DrW idx 272.** Tracciate le giunzioni una per una: a `12→13` la regola **rompe
correttamente** sul glifo `á` (blocco cambia, font `DrawSteelGlyphs-Regular` ≠
corpo `BerlingskeSlab-Regular`); a `13→14` il veto tiene giusto la continuazione
in minuscola del corpo. Le voci `é` e `í` si perdono a `14→15` e `15→16`, dove il
blocco `b0006` **non cambia**. **Il segnale del font non è in difetto**: non viene
mai consultato lì.

Il difetto è quindi uno solo, nominabile e circoscritto: **gli elenchi le cui
voci vivono dentro un unico blocco di sorgente**. Vale anche per il box a rientro
sospeso di DB p.99, dove i blocchi sono sfalsati di una riga rispetto alle voci.

**Non è stato corretto**, ed è una scelta: il §3 del criterio impone che cambiare
il meccanismo dopo aver visto l'esito richieda un criterio nuovo. È la regola che
in questo giro ha impedito quattro volte di tarare su ciò che si aveva davanti.

## 6. Che cosa è stato misurato e scartato

**La variante «frase chiusa»**: rompere anche quando la frase precedente finisce
con `.;!?` e la successiva comincia in maiuscola. Recupera il box di DB p.99 —
da 40 a **42 giunzioni su 43** — e su SV p.181 rispezza la prosa a due colonne,
da 17 paragrafi a 22 contro i 23 della regola vecchia. Compra due giunzioni su
una struttura di una pagina e ne perde cinque di prosa corretta. **Scartata.**

**Il candidato tipografico della v1** — la riga che arriva al margine destro
continua — era già caduto in progettazione: su DB p.99 le righe che continuano
arrivano a 38,2 larghezze di carattere di scarto e quelle che chiudono partono da
0,0. Dichiarato allora, e vale ancora, che quella misura **non falsifica** la
regola: l'etichetta usata era un proxy inaffidabile proprio dove serviva.

## 7. Limiti dichiarati

**Il design ha iterato tre volte su pagine ispezionate** — tipografica, blocco,
blocco+veto — e ogni passo è nato da un fallimento su una pagina guardata. È il
modo in cui questo progetto si è già avvitato, ed è la ragione per cui il
primario non è mai stato aperto e la barra è stata fissata prima. La quarta
iterazione, il font, è arrivata dalla stessa strada e per questo il §6 del
criterio le ha attaccato un controllo dedicato.

**La cecità è parziale.** L'A/B toglie il sapere *quale* versione è nuova, non il
sapere *che cosa* si sta cercando. Il giudizio è di una persona sola.

**I numeri del giro precedente sono ora falsi.** La distribuzione delle quote di
paragrafi corti di `Esito_FormaMancante_v1.md` §6 — mediana 23,1%, minimo 6,7%,
massimo 74,3% — e il **rango 3 su 38** di Wil idx 244 sono proprietà della
segmentazione vecchia. Vanno **rifatti, non ricopiati**, e chi li citasse dopo
questo commit citerebbe una pipeline che non esiste più.

**La base di E-B è cambiata** per costruzione: il confronto `--base` verifica
l'elenco dei paragrafi. L'ordine di lettura **non** cambia — la sequenza delle
righe di sorgente è la stessa, cambia solo il raggruppamento — ma non è stato
verificato in questo giro, ed è la prima cosa da controllare se qualcosa non
torna.

## 8. Verifiche

Ruff verde sui file toccati; gli 83 rilievi sull'intero repo sono **pre-esistenti
su HEAD**, verificato con uno stash. Suite **1372 test**, un solo fallimento, che
è quello ambientale già a verbale in Milestone 38 (`test_runs_table_candidate_for_known_dag_page`
cerca `Dag.pdf` nella root, assente dal worktree). `git diff --check` pulito.
`basedpyright` in questo worktree non risolve il venv e il suo esito qui non è
autoritativo.

**Un test è stato cambiato, e non per farlo passare.**
`test_builds_the_three_entries_of_a_hanging_indent_box` asseriva le tre voci
separate della regola vecchia; ora asserisce il paragrafo unico, e la sua
docstring porta il perché: 40 giunzioni su 43 contro 33, e la variante che
recupererebbe quel box misurata e scartata. Il test è diventato il verbale del
costo, non l'impronta del codice.

## 9. Che cosa resta aperto

Gli elenchi dentro un blocco solo (§5), che ora hanno una causa verificata e
nessuna correzione. **L'emissione dello stile inline** — grassetto e corsivo —
che è il difetto misurato su 13 pagine su 20 in `Esito_FormaMancante_v1.md` e
richiede a `NodeIR2` di portare lo stile invece di una stringa nuda;
`primitive_normalizer.py:98` scrive ancora `font_traits=()`. Il colore delle note
a margine e il loro ancoraggio. Il cancello di emissione sulle full art. La
deduplicazione degli span identici. E i due porting del §10 del criterio, di cui
la conservazione dei caratteri richiede prima una decisione su che cosa significhi
conservare quando l'emettitore toglie un trattino di proposito.
