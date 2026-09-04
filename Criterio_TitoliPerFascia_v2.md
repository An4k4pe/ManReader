# Criterio — i titoli per fascia, v2. **Ciò che è prosa non è mai un titolo**

Dichiarato il 2 settembre 2026, **prima** della misura che decide.

## 0. Che cosa cade di `Criterio_TitoliPerFascia_v1.md`

Non le fasce, e non il corpo per massa: `Esito_TitoliPerFascia_v1.md` §2 e §3 li
ha confermati — il corpo è la moda per massa su otto manuali su otto, e la mappa
dimensione→livello è diventata **una sola per documento**, con le occorrenze
instabili di Dag da 241 a 2.

Cadono tre cose, e la terza le spiega tutte.

**A. Il tetto scarta invece di accorpare.** «Oltre la terza è corpo» conta i
**titoli** quando la decisione dell'utente contava i **livelli**. Misurato, il
costo non è «BoB perde un livello» ma dal 74% al 97% dei titoli su ogni manuale:
Dag 2035→50, BiD 1164→68, Wil 1293→100, BoB 1086→229, FWK 394→100.

**B. Il §0.A della v1 misura l'estremo sbagliato.** Chiama «l'ancora»
`min(prose_sizes)` — 2,8 pt su Dag — ma la regola della v3 scrive
`limit = max(prose)`. I due numeri non hanno relazione: includere una dimensione
minuta con righe lunghe non sposta il massimo di un decimo. **La colonna «massa
del min» della tabella del §0.A non dice niente sul meccanismo che critica.**

L'instabilità, invece, è reale anche sull'estremo giusto, ed è la ragione che
resta in piedi. Facendo scorrere finestre di 20 pagine, `max(prose_sizes)` assume

```
Dag  6 valori: 8.0, 8.9, 9.1, 9.2, 10.0, 11.9
Fab  6 valori: 8.0, 9.8, 9.9, 10.0, 12.0, 25.0
BiD  5 valori: 9.0, 9.1, 9.4, 9.5, 9.6
BoB  4 valori: 10.0, 10.1, 11.0, 11.1
```

**C. Le fasce si formano sopra il CORPO invece che sopra LA PROSA**, ed è il
difetto che genera gli altri due. Su Dag il corpo arriva a 9,2 e la prosa a
**12,1**: fra i due c'è spazio per tre fasce che sono prosa e che la v1 ammette
fra le candidate —

```
11.4-12.1  312 pagine  96% parole  riga 0.30  'Quando giocate a Daggerheart, consigliamo di'
10.7-11.3  247 pagine  97% parole  riga 0.30  'tori a vivere la migliore esperienza possibile'
10.0-10.6  111 pagine  99% parole  riga 0.25  'Agilità +1, furto +2'
```

È l'errore che `document_heading_policy` ha **già commesso e già corretto una
volta**, e il suo docstring lo dice: «Non "sopra il corpo" ma "sopra tutta la
prosa"… su Kul 8,0 e 10,0 sono entrambe prosa».

**E il §1 della v1 dichiara che il filtro 3 toglie quelle fasce. Non le toglie.**
I loro rapporti di riga sono 0,30, 0,30 e 0,25, tutti sotto il mezzo: **passano**.
A tenerle fuori dall'uscita era soltanto il tetto. Il difetto A mascherava il
difetto C, e scoprirlo ha richiesto di guardare che cosa stava al quarto rango.

## 1. La regola

> **Il tetto della prosa.** `max(prose_sizes)`, e il massimo della fascia di
> corpo, presi sul **documento intero**. Il tetto è il maggiore dei due.
> **Nessuna dimensione al tetto o sotto può essere un titolo, mai.**
>
> **Il corpo.** Le dimensioni si accorpano in fasce entro il **4%**; la fascia
> che porta più caratteri è il corpo. Serve a due cose e a nessun'altra: entra
> nel tetto, ed è il **denominatore** del filtro 3.
>
> **I candidati.** Sopra il tetto, le dimensioni si accorpano in fasce entro il
> **6%**. Una fascia è candidata se tutte e quattro:
>
> 1. **è staccata dal tetto**: la sua dimensione minima è almeno `tetto × 1,06`;
> 2. **porta parole**: almeno il **60%** dei suoi testi ha due o più caratteri e
>    contiene una lettera;
> 3. **ha righe corte**: la sua mediana di lunghezza riga è al più **metà** di
>    quella del corpo;
> 4. **compare su almeno tre pagine**.
>
> **I livelli.** Le fasce candidate prendono il rango in ordine di dimensione, e
> il rango si **accorpa** sul terzo: `min(rango, 3)`. Oltre la terza fascia il
> titolo resta un titolo e diventa `###`. **Non torna prosa.**
>
> La regola di riga della v3 resta invariata e si applica dentro le fasce.

**Il tetto non è una soglia scelta.** Viene da `prose_sizes`, che taglia al salto
più grande fra le mediane di lunghezza riga: è una proprietà della distribuzione.
Ciò che la v2 cambia non è come si misura la prosa, ma **dove la si applica** —
al documento invece che alla finestra — e **che è invalicabile**.

**Perché il corpo entra comunque nel tetto.** Su BoB `max(prose_sizes)` è 10,0 ma
la fascia di corpo arriva a **10,2**: prendere solo la prosa lascerebbe due
decimi di corpo sopra il tetto. Il maggiore dei due chiude il buco senza
introdurre un numero.

**I filtri sono l'ultima guardia, non il meccanismo.** Indicazione dell'utente del
2 settembre 2026: «il 3 è solo l'ultima guardia contro cose che non dovrebbero
essere titoli e lo diventavano; tutto ciò che viene identificato come prosa non
può essere titolo, mai; i 3 criteri devono lavorare su quello che sta sopra la
prosa». La v1 li faceva lavorare in mezzo alla prosa, e chiedeva loro di
distinguere ciò che il tetto avrebbe già dovuto escludere.

## 2. I numeri scelti a mano, e quelli che non lo sono

**Scelti**: 4%, 6%, 60%, metà, tre pagine. È il debito dichiarato, e la
sensibilità della v1 mostra che fra 4% e 8% gli otto manuali danno la stessa
struttura: la zona è larga, non un punto.

**Non scelti**: il tetto (da `prose_sizes`), il corpo (la fascia di massa
maggiore), il numero di livelli (tre, decisione dell'utente sulla compatibilità
Markdown).

## 3. Il campione, le esclusioni, e **che cosa ho già visto**

Popolazione: le righe che la regola nuova promuove, e quelle che la v3 promuove,
sui manuali ammessi. Sorteggio con seed **`20260902`**, dichiarato qui prima di
guardare.

**Esplorazione già fatta, e va dichiarata** (`AGENTS.MD` §16): simulando fasce
sopra la prosa con tetto che accorpa, **Dag dà 93 righe promosse e Fab 103**, con
cinque e tre fasce candidate. Non ho guardato quali righe siano su nessun altro
manuale, né ho giudicato quelle. Il conteggio non è una sorpresa; il **giudizio**
sì.

**Fuori dal campione**, per le ragioni già misurate in `Criterio_TitoliPerFascia_v1.md`
§3: **DrM** (due sole fasce candidate) e **DrW** (il corpo cade sul testo di
scheda). Ciò che la regola fa su di loro si riporta a parte, con i suoi numeri.

**Dentro e da guardare**: **Kul**, dove i tre livelli sono frammenti di un titolo
display spezzato in primitive. È un caso che il criterio deve poter fallire.

## 4. Pass/fail

### A. Veto — il punto fisso. Verificabile a macchina

> Cade se **una sola** riga promossa ha dimensione minore o uguale al tetto della
> prosa.

È la regola dell'utente resa controllabile senza giudizio. Non ammette eccezioni
e non si emenda: se cade, il tetto è costruito male.

### B. Veto — i livelli

> Cade se **una sola** riga promossa a H1/H2/H3 non è un titolo.

Etichette **titolo** / **non titolo** / **incerto**. Una riserva scritta accanto
a un'etichetta netta conta come `incerto`.

### C. Regressione — i sedici della v2, **con un costo dichiarato prima**

> Le 16 righe che il giudizio della v2 ha confermato titoli devono restare
> promosse, **tranne quelle che stanno al tetto della prosa o sotto**, che si
> contano e si riportano a parte come debito dell'asse del font.

**Perché l'eccezione non è un salvataggio.** Regge senza sapere se il meccanismo
poi passa: discende dalla decisione dell'utente del 2 settembre 2026 — la prosa
non è mai titolo, il font si fa dopo — e quella decisione è stata presa **sapendo
che costa le sottosezioni**, non per far passare questo giudizio. Misurato su Dag
prima di scriverla: `PANORAMICA` sta a 12,0 pt e `TONO E ATMOSFERA` a 11,0, mentre
la prosa `'Quando giocate a Daggerheart…'` sta a **12,1** — sull'asse della
dimensione i titoli stanno **sotto** la prosa, e nessuna regola di misura può
separarli. Ciò che li separa è il font: `EvelethCleanRegular` pesa l'1,1% della
massa contro il 73,1% di `QuestaSans-Light`.

Il numero delle sedici che cadono così **si riporta**, e se è alto è un argomento
per fare presto il criterio del font, non per emendare questo.

### D. Nessuna dimensione con due livelli

> Cade se una dimensione riceve due livelli diversi. Verificabile a macchina.

### E. Regressione degli altri meccanismi

> `check_eb.py` 9/10 con la sola differenza a verbale (Fab idx 126);
> `check_list_regression.py` e `check_numbered_lists.py` invariati.

### Se cade

- **A**: il tetto è costruito male, e cade tutto il criterio. Non si ritocca.
- **B** verso «promossa e non lo era»: si riporta il caso e **non** si aggiunge un
  quinto filtro nello stesso giro.
- **C** sopra il tetto: cade. Sotto il tetto: si conta e si riporta, non cade.
- **D**: difetto di costruzione, si corregge e si rimisura.

## 5. Che cosa resta fuori, e il debito che si apre

- **L'asse del font**, che è il debito che questo criterio contrae
  esplicitamente. Su Dag separa `EvelethCleanRegular` (1,1% della massa, 1407
  testi) dal corpo `QuestaSans-Light` (73,1%), ed è lo stesso asse che
  `Criterio_MarcatoreDaFont_v2.md` usa già per i punti elenco. Vuole un criterio
  suo: infilarlo qui sarebbe il quinto filtro che il §4 vieta.
- **La gerarchia**: i livelli restano ranghi di dimensione, non un albero.
- **L'arredo**, che continua a togliere numeri di pagina e testatine dalle fasce
  candidate. I due meccanismi girano entrambi.
- **Le schede mostro come categoria**, debito aperto e ora dichiarato tre volte.
  Su Dag `CARATTERISTICHE` a 10,0 pt `QuestaSans-Bold` compare **188 volte**: la
  v3 la promuoveva a titolo, questo criterio la lascia nel corpo, e nessuno dei
  due la tratta per quello che è — l'etichetta di un campo di scheda.
