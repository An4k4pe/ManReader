# Criterio — il titolo che **sta sopra** il paragrafo, e non è più grande di lui

## 0. La diagnosi precedente era sbagliata, e va detto per prima cosa

`Esito_Titoli_v3.md` §2.A chiama «titoli **in linea**» i undici titoli mancati, e
scrive che stanno «sulla stessa riga tipografica del testo che aprono». **È
falso**, e la sorgente lo dice in chiaro. Su Apo idx 79:

```
b0001 l0000   dim 10,6  Calluna-Semibold   x 56,8→177,5   LA DONNA DI CENDRES
b0001 l0001   dim 11,6  ArnoPro-Regular    x 56,7→383,8   Nonostante alcune remore, Gabriel obbedì…
b0001 l0002   dim 11,6  ArnoPro-Regular    x 56,7→366,8   eradicò il culto, screditando…
```

Il titolo è **una riga sorgente sua**, la prima del suo blocco, e sta **sopra** il
paragrafo. Rilievo dell'utente: «io li vedo sopra i paragrafi». Non è mai stato un
problema di righe fuse: è che **la resa** li attacca al paragrafo, perché niente
dice al costruttore di rompere lì.

### E il carattere: chi lo vede più grande ha ragione

Ho riferito che su Apo il titolo è a 10,6 e il corpo a 11,6, e ne ho concluso che
il titolo è «più piccolo del corpo». **La dimensione nominale è più piccola; le
lettere sul foglio non lo sono.** Sono due font diversi, e il titolo è tutto in
maiuscolo:

| | dimensione | riquadro | font | cosa si vede |
| --- | ---: | ---: | --- | --- |
| `LA DONNA DI CENDRES` | 10,6 | 12,70 | Calluna-Semibold | **maiuscole**, alte quanto il font le fa |
| il corpo accanto | 11,6 | 14,47 | ArnoPro-Regular | minuscole, alte quanto la **x** |

Un'altezza di maiuscola a 10,6 in un font batte un'altezza di minuscola a 11,6 in
un altro: il punto tipografico misura il corpo del carattere, non l'inchiostro. La
regola della dimensione **non può vedere** questi titoli, e non perché siano
piccoli: perché sta misurando la cosa sbagliata.

**Perché non misuro direttamente l'inchiostro.** Perché l'altezza dell'inchiostro
di un testo tutto maiuscolo *è* l'altezza delle maiuscole, e misurarla sarebbe il
riconoscimento dal MAIUSCOLO travestito da geometria — l'errore del vecchio
renderer che `Criterio_Titoli_v1.md` §5 ha messo fuori legge. Il segnale onesto è
un altro, ed è quello che l'utente indica.

## 1. La regola

> Una riga sorgente è un **titolo**, anche quando la sua dimensione non supera la
> prosa, se **tutte** e quattro:
>
> 1. il **font che la governa** — quello della maggioranza dei suoi caratteri — è
>    diverso dal font che governa il **resto del suo blocco**;
> 2. nel suo blocco **la segue** almeno una riga, e quella riga è governata dal
>    font del blocco: il titolo deve intestare qualcosa;
> 3. **finisce prima del margine destro del suo blocco**, e ci finisce prima di
>    quanto le righe del blocco si concedano da sole: lo scarto dal margine è
>    **maggiore del più grande scarto** fra le righe interne del blocco;
> 4. non è già un titolo per dimensione, e non è già tolta dal corpo come
>    **arredo**.

Nessuna delle quattro è un numero tarato. Il margine, la raggedness e il font sono
tutti fatti **del blocco che si sta guardando**.

### 2 e 3 non sono ridondanti, e una misura lo dimostra

Su Vil idx 131 il blocco `b0001` ha la sua **seconda** riga interamente in
`ArnoPro-Bold` mentre il blocco è governato da `ArnoPro-Regular`. La condizione 1
la promuoverebbe:

```
b0001 l0000  Calluna-Bold      x 56,8→ 88,5   DONI                    ← titolo
b0001 l0001  ArnoPro-Bold      x 56,7→391,2   I doni sono aspetti…    ← NON titolo
b0001 l0002  ArnoPro-Bold/Reg  x 56,7→391,0   imparare – a padroneggiare…
b0001 l0003  ArnoPro-Regular   x 56,7→383,0   un'arma a doppio taglio…
```

Il margine del blocco è 391,2. `DONI` si ferma a 88,5 — scarto **302,7**. La riga
in grassetto si ferma a 391,2 — scarto **zero**, cioè **riempie la misura**: è
prosa che va a capo, e il grassetto è un'enfasi del redattore.

Lo scarto interno del blocco è 8,2 (la riga `l0003`). 302,7 lo supera, 0 no.

> **È il controllo geometrico che l'utente ha chiesto**, ed è quello che separa il
> titolo dal grassetto: non basta che il font cambi, deve anche **finire presto**.

### I quattro casi che la regola deve prendere

```
Apo idx 79  b0001  LA DONNA DI CENDRES     10,6 Calluna-Semibold  scarto 206,3  su raggedness 0,0
Apo idx 79  b0004  L'ARRIVO DELL'OSCURITÀ  10,6 Calluna-Semibold  scarto 196,1  su raggedness 14,5
Vil idx131  b0001  DONI                    11,6 Calluna-Bold      scarto 302,7  su raggedness 8,2
Vil idx131  b0003  EFFETTI                 10,6 Calluna-Semibold  scarto 292,8  su raggedness 0,0
```

## 2. Il livello

Questi titoli non hanno un rango di dimensione: la loro dimensione è **dentro** la
prosa, e la scala dei ranghi comincia sopra. Prendono il livello **subito sotto il
più profondo assegnato per dimensione**, con lo stesso tetto di tre di
`Criterio_Titoli_v3.md`.

È una scelta dichiarata e non misurata: un titolo che il documento compone più
piccolo del corpo non è un capitolo, e metterlo al livello 1 sarebbe peggio che
metterlo in fondo. **La gerarchia resta il debito che è**, e l'utente l'ha
rimandata esplicitamente.

## 3. Il campione

Le righe che **questo ramo aggiunge** — non quelle che la dimensione già trova —
su tutti i manuali fuori dai due esclusi. Se sono più di 30 se ne sorteggiano 30,
seed **`20261101`**.

Restano fuori dalla popolazione **DrM** e **DrW**, come in `Criterio_Titoli_v3.md`
§3 e per la stessa ragione già dichiarata: il loro corpo misurato è il testo di
scheda. Ciò che il ramo fa su quei due si riporta a parte, coi suoi numeri.

## 4. Pass/fail

### A. Veto — cade a una riga sola

> Cade se **una sola** riga promossa da questo ramo non è un titolo.

Il ramo **aggiunge** e basta: non può togliere niente a nessuno, quindi il veto è
in una direzione sola. Etichette **titolo** / **non titolo** / **incerto**, seed di
controllo **`20261102`**, materiale con la **pagina intera** e tutte le occorrenze.
Una riserva scritta accanto a un'etichetta netta vale `incerto`.

### B. Barra di copertura — i quattro casi nominati

> I quattro titoli del §1 devono essere trovati tutti e quattro.

Sono i casi per cui la regola è scritta. Se non li prende non ha fatto il suo
lavoro, qualunque cosa faccia altrove.

### C. Regressione — la dimensione non cambia

> I titoli che il ramo per dimensione già trova devono restare identici, in numero
> e in livello, su tutti i sedici manuali.

### D. La giunzione

> Nessuna riga promossa può stare **dentro** un paragrafo: si guarda il testo
> sopra e sotto ogni promozione, e una promozione che spezza una frase a metà fa
> cadere il ramo.

È lo stesso bersaglio del §4.D della v3, e qui è più vicino: la regola promuove
righe che stanno dentro blocchi di prosa.

### E. Gli altri meccanismi

> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A**: si riporta quale riga e perché, e **non** si aggiunge una condizione
  nello stesso giro. Il ramo si ritira.
- **B**: la regola non serve a niente e si ritira, anche se A passa.
- **C**: la modifica ha toccato ciò che funzionava, ed è un difetto
  d'implementazione, non del criterio.

## 5. Che cosa resta fuori

- **La gerarchia.** Il livello del §2 è una collocazione, non un albero.
- **Le schede mostro**, ancora, e ancora dichiarate prima.
- **Il titolo davvero in linea**, `Titolo: paragrafo` sulla stessa riga sorgente.
  Non l'ho misurato e non lo tratto: la diagnosi che diceva che questi lo fossero
  era sbagliata, e non ne scrivo un'altra senza guardare prima.
