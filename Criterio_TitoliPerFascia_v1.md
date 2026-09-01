# Criterio — i titoli per fascia. Il corpo è dove sta la **massa**, non dove finisce la coda

## 0. Che cosa cade di `Criterio_Titoli_v3.md`

Non la regola di riga, che resta. Cade **l'ancora**: la v3 chiama titolo una riga
«maggiore della più grande dimensione di prosa», e `prose_sizes` decide che cosa è
prosa **tagliando al salto più grande fra le mediane di lunghezza riga**, senza
guardare **quanta scrittura** ogni dimensione porti.

Due difetti misurati, non predetti.

**A. L'ancora è un outlier.** Su Dag, `min(prose_sizes)` sul documento intero è
**2,8 pt**. Quella dimensione ha righe lunghe — mediana 55 caratteri, quindi la
regola ha ragione a chiamarla prosa — ma porta **2011 caratteri su 1.340.284**,
lo 0,15%. Su sette manuali su otto l'ancora cade su una dimensione che porta
**meno dell'1%** del testo:

```
man   dimensioni  moda   % moda  top4 %   min(prose)  massa del min
Dag           97   9.0    42.8%   86.1%          2.8         0.021%
Fab           49  10.0    86.3%   97.3%          9.8         0.073%
FWK           49  12.0    71.4%   89.1%          9.6         0.297%
Wil           98  10.0    61.2%   88.3%          8.2         0.044%
BoB           71  10.0    79.5%   96.0%          9.8         0.453%
Apo           20  11.6    72.6%   97.6%          9.0         0.748%
BiD           70   9.5    49.2%   84.8%          9.3         0.317%
Vil           24  11.6    65.8%   96.3%         11.6        65.842%
```

Vil è l'eccezione **per caso**: lì `prose_sizes` restituisce una dimensione sola,
e coincide con la moda.

**B. L'ancora si sposta con la finestra.** `Criterio_AmbitoDeiFatti_v2.md` misura
già che `prose_sizes` non è invariante di scala e sposta la finestra invece di
allargarla. Ma la finestra ha il difetto simmetrico, ed è il rilievo dell'utente:
misurare sui caratteri di una pagina produce livelli che non valgono due pagine
dopo, se quelle erano outlier. Facendo scorrere finestre di 20 pagine su tutto il
libro, **`min(prose_sizes)` assume fino a 8 valori diversi sullo stesso manuale**,
mentre la moda per massa concorda con quella del documento **90 volte su 101**:

```
man    moda doc   finestre   concordi   valori diversi di min(prose)
Dag         9.0         18      12/18                             8
Fab        10.0         18      16/18                             6
FWK        12.0         11      11/11                             2
Wil        10.0         15      15/15                             7
BoB        10.0         23      23/23                             3
BiD         9.5         16      13/16                             6
```

**C. I ranghi si assegnano a dimensioni singole**, quindi decimi diversi fanno
livelli diversi. Misurato sull'uscita attuale: su Dag `28→h1, 28→h2` — **due
livelli alla stessa dimensione** — e su Wil `47→h1, 44→h2, 43→h3, 43→h3`.

## 1. La regola

> **Il corpo.** Le dimensioni si accorpano in **fasce** entro il **4%**. La fascia
> che porta **più caratteri** è il corpo. Una sola per documento, calcolata su
> tutte le pagine.
>
> **I candidati.** Sopra il corpo, le dimensioni si accorpano in fasce entro il
> **6%**. Una fascia è candidata se tutte e quattro:
>
> 1. **è staccata dal corpo**: la sua dimensione minima è almeno `corpo × 1,06`;
> 2. **porta parole**: almeno il **60%** dei suoi testi ha due o più caratteri e
>    contiene una lettera;
> 3. **ha righe corte**: la sua mediana di lunghezza riga è al più **metà** di
>    quella del corpo;
> 4. **compare su almeno tre pagine**.
>
> **I livelli.** Le **tre fasce più grandi** fra le candidate diventano H1, H2, H3
> nell'ordine di dimensione. Oltre la terza è corpo.
>
> La regola di riga della v3 resta invariata e si applica dentro le fasce.

**Perché i filtri 2 e 3 sono due e non uno.** Il 2 toglie la decorazione, che si
riconosce perché porta caratteri singoli: su Fab `'y'` a 172 pt, `'j'` a 32 pt,
`'W'` su 358 pagine, `'12'` su 188 pagine; su BiD `'2'`, `'3'`, `'4'` a 292 pt; su
Dag `'••'` a 24 pt. Il 3 toglie la **prosa più grande**, che il 2 non vede: su Dag
le fasce a 12 e 11 pt sono al 99% parole su 312 e 243 pagine, e il testo è
`'Quando giocate a Daggerheart…'`.

**Perché la guardia 1.** Allargando la tolleranza senza guardia, le fasce vicine
al corpo vengono promosse: a tolleranza 20% Fab dava `H1 = 11-12 pt su 282
pagine`. Con la guardia, la stessa configurazione non produce **nessun** livello.
Il modo di sbagliare passa da «etichetta il corpo come titolo» a «tace», ed è il
verso giusto: perdere un livello è già accettato, mentire dentro il testo no.

**Perché le tre più grandi e non le tre più usate.** Provato e **scartato**: la
frequenza cresce avvicinandosi al corpo, quindi selezionare per uso trascina la
scelta verso la prosa. Su Dag le tre più usate sono `'Quando giocate a
Daggerheart…'`, `'tori a vivere la migliore espe…'`, `'Agilità +1, furto +2'`; su
BiD `'consigli per il giocatore'`, `'EDIZIONE ORIGINALE'`, `'RINGRAZIAMENTI'`. Un
solo manuale ci guadagna — BoB, dove entra la fascia da 216 pagine — e al terzo
posto mette una riga di sommario.

**Il tetto a tre è una decisione dell'utente**, non una misura: compatibilità con
Markdown e lettori. Il costo è dichiarato: BoB ha **quattro** livelli veri e ne
perde uno — la fascia `17,8-18,4` su 216 pagine, `"PASSO DELL'IMPICCATO"`.

## 2. I tre numeri, e che sono scelti

**4%, 6%, 60%, metà.** Nessuno è desunto dal documento: sono tarati a mano su
otto manuali. È il debito di questo criterio e va detto, non nascosto. Ciò che la
misura di sensibilità mostra è che **fra 4% e 8% gli otto manuali danno la stessa
struttura**, e che sopra il 12% si perde: la zona è larga, non un punto.

## 3. Il campione, e le esclusioni dichiarate **prima**

Popolazione: le righe che la regola nuova promuove a H1/H2/H3, e quelle che la v3
promuove, sui manuali ammessi. Sorteggio con seed **`20260901`**, dichiarato qui
prima di guardare.

**Fuori dal campione, e misurato prima di dichiararlo:**

- **DrM** — la regola trova **due sole** fasce candidate (`58 'Monsters'`,
  `24 'CREDITS'`), niente terzo livello;
- **DrW** — il corpo per massa cade a **7,4-7,5 pt**, cioè il testo di scheda, e
  i livelli diventano `16 'MCDM Contractors'` e `14 'Introduction'`.

Sono i due manuali densi di schede che `Criterio_Titoli_v3.md` §3 aveva già
escluso, per la stessa causa di fondo. Il prezzo si paga per intero: ciò che la
regola fa su di loro **si riporta separatamente** nell'esito, con i suoi numeri.

**Dentro il campione e da guardare**: **Kul**, dove i tre livelli sono `'DELLA'`,
`'ORRORI'`, `'SEMIDEI'` — frammenti di un titolo display spezzato in primitive.
Non lo escludo: è un caso che il criterio deve poter fallire.

## 4. Pass/fail

### A. Veto — l'ancora, che è la ragione per cui questo criterio esiste

> Cade se su **un solo** manuale ammesso la fascia del corpo non è la dimensione
> che un lettore riconosce come testo corrente della pagina.

Vincola il caso da cui l'affermazione è nata (`AGENTS.MD` §15): Dag, dove
l'ancora vecchia era 2,8 pt. Giudizio su render di pagina, non sui numeri.

### B. Veto — i livelli

> Cade se **una sola** riga promossa a H1/H2/H3 non è un titolo.

Etichette **titolo** / **non titolo** / **incerto**. Una riserva scritta accanto a
un'etichetta netta conta come `incerto`.

### C. Regressione — non si perde ciò che era guadagnato

> Le 16 righe che il giudizio della v2 ha confermato titoli devono restare
> promosse, e nessuna deve **cambiare livello** rispetto alla v3 senza che il
> cambio sia spiegato.

### D. Nessuna dimensione con due livelli

> Cade se una dimensione riceve due livelli diversi, che è il difetto C del §0.

Verificabile a macchina, senza giudizio.

### E. Regressione degli altri meccanismi

> `check_eb.py` 9/10 con la sola differenza a verbale; `check_list_regression.py`
> e `check_numbered_lists.py` invariati.

### Se cade

- **A**: il corpo per massa non regge, e cade tutto il criterio — non si ritocca
  la tolleranza per farlo passare.
- **B** verso «promossa e non lo era»: si riporta il caso e **non** si aggiunge un
  quinto filtro nello stesso giro.
- **D**: è un difetto di costruzione, si corregge e si rimisura.

## 5. Che cosa resta fuori

- **La gerarchia**: i livelli restano ranghi di dimensione, non un albero.
- **L'arredo**, che continua a togliere numeri di pagina e testatine dalle fasce
  candidate — su FWK la fascia a 20 pt contiene `'appartenenza'`,
  `'archetipi di compagnia'`, `'terrapolis'` **e** i folii `'58'`, `'76'`, `'92'`.
  I due meccanismi sono complementari e girano entrambi.
- **Le schede mostro come categoria**, debito aperto e ora dichiarato due volte.
- **Il quarto livello di BoB**, perso per decisione sul tetto.
