# Esito di `Criterio_TitoloComposto_v1.md` — **A adottato, B ritirato**

Scritto l'8 settembre 2026, dopo la misura sui manuali.

## 0. Stato in una riga

Il meccanismo **A**, la sovrastampa, passa e viene adottato. Il meccanismo **B**,
l'unione a corpi diversi, **cade sul veto D**: produce 83 unioni e la maggioranza
è sbagliata. Kul resta frammentato ma non più raddoppiato.

Decisione dell'utente dell'8 settembre 2026, chiesta prima della misura e
applicata dopo: «preferisco piccoli errori che un enorme errore di titoli
lunghissimi».

## 1. Meccanismo A — la sovrastampa. **Passa, adottato.**

> Veto A: su Kul idx 168 la riga a 86 pt deve essere `ORRORI` e non
> `ORRORI ORRORI`; su Vil `'Valois Valois'` → `'Valois'`; su Wil
> `'◈ villaggio di lala villaggio di lala'` → una volta sola.

**Passa.** Su Kul idx 162 l'uscita è `ANGELI CADUTI SEMIDEI E ARCONTI`, dove
prima erano `ANGELI ANGELI CADUTI CADUTI`, `SEMIDEI SEMIDEI` e
`E ARCONTI E ARCONTI` a tre livelli diversi.

**Una correzione a metà strada, a verbale.** Avevo implementato la sovrastampa
**fra righe**, mentre il criterio la dichiara **fra primitive**. Sembrava
equivalente e non lo è:

```
l0000: ['ANGELI' @ (34.9625, 42.9375, 192.1955, 152.3325)]
l0001: ['ANGELI' @ (34.9625, 42.9375, 192.1955, 152.3325), ' ' @ (192.29, …)]
```

La seconda riga è la stessa primitiva **più uno spazio in coda**: le bbox di
**riga** non coincidono, quelle di **primitiva** sì. È il motivo per cui la misura
delle 816 coppie identiche era giusta e la mia prima implementazione non trovava
niente. Spostato dove il criterio lo dichiara — nella composizione del testo della
riga — funziona.

**La primitiva non si scarta**: smette solo di contribuire al testo, quindi resta
coperta da un nodo e `AGENTS.MD` §Coverage regge. Il veto C lo protegge.

## 2. Meccanismo B — l'unione a corpi diversi. **Cade.**

> Veto D, metà nuova: cade se un titolo vero è stato unito a un altro che non gli
> apparteneva.

**83 unioni prodotte**, e il campione sorteggiato ne mostra la natura:

```
SBAGLIATE
BoB idx 204 st.193  'RELAZIONI I PRESCELTI'                         due sezioni distinte
BoB idx 300 st.289  'sgattaiolare ESEMPI'                           azione + intestazione
BoB idx 166 st.155  'orologio da 8 MIGLIORARE LE MISSIONI'
BiD idx  71 st. 64  'ABILITÀ SPECIALI DEL GUANTO gambetto di torre' intestazione + 1ª voce
BiD idx 237 st.230  'ESEMPIO DI CREAZIONE inventare un lanciafiamme'

GIUSTE
Kul idx 226         'CREATURE DELLA PRIGIONE'   da 'DELLA' + 'PRIGIONE' + 'CREATURE'
Wil idx  80         'ZUPPA DI TAGLIATELLE E P O L P E T T E'
BiD idx 134 st.127  'CAPITOLO 4 il colpo'
```

**La diagnosi, che è il risultato che resta.** «Solo lo stesso blocco» impedisce
di fondere i titoli **fratelli**, e `Criterio_Titoli_v3.md` §2 lo dichiarava con
la sua misura: su DB `ANIMISMO`, `ELEMENTALISMO` e `MENTALISMO` sono adiacenti,
**della stessa dimensione**, ognuno nel suo blocco. Ma un'**intestazione e ciò che
introduce** hanno dimensioni **diverse** e stanno spesso nello **stesso** blocco.

Il vincolo che rendeva sicura la regola vecchia era la **pari dimensione**, non il
blocco. Toglierlo la scopre, e il blocco da solo non la ripara.

**La lunghezza invece non è il problema**, e va detto perché era il timore
dichiarato dall'utente. Misurato su nove manuali, il titolo più lungo cresce solo
su Kul (32 → 42 caratteri) e BiD (63 → 64); altrove è identico. Il vincolo del
blocco contiene la lunghezza. **Il danno è nel numero, non nella misura.**

## 3. Il veto B, che cade per una ragione sua

> Su Kul idx 168 le tre righe devono formare `ORRORI DELLA GNOSI` al livello di
> 102 pt.

**Cade anche prima del giudizio**: si ottiene `ORRORI DELLA` più un `GNOSI`
orfano. `GNOSI` sta a **102 pt**, e 102 non forma una fascia candidata perché
compare su **meno di tre pagine** — il filtro `MIN_PAGES`.

**È una caduta che dice una cosa utile e va a verbale**: il filtro delle tre
pagine protegge dalle fasce inventate, e nel farlo esclude proprio le **parole più
grandi dei titoli display**, che per costruzione compaiono poche volte perché sono
il nome di un capitolo. Chi vorrà chiudere Kul del tutto riparte da qui.

## 4. Che cosa resta in albero

Il meccanismo B **non lascia codice**: la sua diagnosi sta nel docstring di
`merge_wrapped`, che è dove qualcuno la cercherà prima di riprovarci. Un parametro
che nessuno passa sarebbe una trappola, una spiegazione no.

## 5. Che cosa resta aperto

- **Kul frammentato**: `ORRORI`, `DELLA`, `GNOSI` restano tre titoli. Non più
  raddoppiati, ma tre.
- **`REALTAÀ`**, la À doppia: corruzione del testo sorgente, fuori da entrambi i
  meccanismi.
- **Le 5 coppie quasi-identiche** (3 Wil, 2 Kul), che vorrebbero una tolleranza
  geometrica cablata.
- **Le schede**, nella chat dedicata. **Il debito del font**, aperto.
