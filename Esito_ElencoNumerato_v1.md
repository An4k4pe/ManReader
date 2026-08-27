# Esito di `Criterio_ElencoNumerato_v1.md` — **precisione perfetta, copertura al 68%**

**Stato in una riga**: sulle **36 righe del corpus, tutte giudicate**, la regola
non sbaglia **nemmeno una** di quelle che riconosce, e ne **manca 7** di quelle
che avrebbe dovuto prendere. Il veto §4.A è a zero in entrambe le direzioni:
**cade** sulla seconda.

---

## 1. Il confronto, riga per riga

| | |
| --- | ---: |
| righe che aprono con una cifra | **36** |
| giudicate **voce** dall'etichettatore | 22 |
| riconosciute dalla regola | 15 |
| **riconosciute ma non erano voci** | **0** |
| **scartate ma lo erano** | **7** |
| `incerto` | 0 |

**Nessun campione**: sono tutte le righe del corpus in una finestra di 20 pagine
per manuale. Non c'è errore di campionamento da dichiarare, e questo esito non ha
bisogno della riserva statistica che gli altri di questo giro hanno dovuto
portare.

## 2. La direzione che regge, e regge davvero

**Zero falsi positivi su 15.** Le righe riconosciute — BiD `1.`–`4.`, FW `1.`–`7.`,
SV `1.`–`4.` — sono tutte elenchi numerati veri, e l'etichettatore le ha
confermate una per una.

**Il caso insidioso è stato scartato tutte e quattro le volte**, ed è il risultato
di cui vale la pena parlare. Una riga può cominciare con una cifra e un punto
senza aprire niente, perché la cifra è **la fine della frase precedente** spezzata
a capo:

| manuale | la riga prima finisce con | la riga che comincia con la cifra |
| --- | --- | --- |
| DB | `…con una sciagura al livello di potere` | `3. Ogni tentativo conta…` |
| DB | `…ti protegge dal freddo (pag.` | `54) fino al termine…` |
| Lan | `…aumenta il valore del Dado Carica di` | `1. Quando arrivi a 6…` |
| Vil | `…ho tirato 1 e` | `3. Ho una complicazione!` |

Una regola che prendesse «cifra più punto a inizio riga» avrebbe spezzato quattro
frasi a metà. **Gli interi consecutivi sono ciò che lo impedisce**, e
l'etichettatore è arrivato alla stessa lettura in modo indipendente, riga per
riga, dal solo contesto.

Scartate correttamente anche le **10 testatine** `8. BESTIARIO` di DIE.

## 3. La direzione che cade: 7 titoli di sezione numerati

| riga | manuale | testo |
| --- | --- | --- |
| 09 | DIE | `1. ASPETTO E PERSONALITÀ` |
| 10 | DIE | `2. ASPETTO, PERSONALITÀ E SENTIMENTI` |
| 11 | DIE | `3. ECHI COMPLETI` |
| 32 | Vil | `4. NARRATE I RISULTATI` |
| 33 | Vil | `1. SEGNA IL TUO RETAGGIO` |
| 34 | Vil | `2. SPINGITI OLTRE I LIMITI` |
| 35 | Vil | `3. AFFRONTA UNA PROVA OSCURA` |

Tutte e sette sono **titoli di sezione numerati**: numero, titolo in maiuscolo su
una riga propria, e sotto il paragrafo che lo spiega.

**Perché la regola le manca, ed è per costruzione**: su DIE i tre stanno in
blocchi `b0005`, `b0009`, `b0012` — non consecutivi; su Vil stanno su **pagine
diverse**, `126`, `129`, `129`, `130`. Il vincolo di blocco e pagina, che è
esattamente ciò che scarta le testatine di DIE e le quattro frasi spezzate, scarta
anche questi.

> **Non è stato ritoccato**, e il criterio lo impone: «se cade verso "scartata e
> lo era", la regola è troppo stretta, e si riporta quanto manca senza allargarla
> nello stesso giro».

### E sono una classe, non sette casi

Un numero, un titolo su riga propria, un paragrafo sotto. Renderli come voci
d'elenco sarebbe **meglio di adesso** ma non giusto: quello che vogliono è la resa
a **titolo**, che questo progetto non emette ancora — `ir2_markdown` lo dichiara,
e `Esito_Elenchi_v1.md` aveva già registrato `Capitolo 6` e `**Cavaliere del
Drago**` che escono come prosa.

**La copertura di questo criterio è quindi legata a un fascicolo che non è
questo.** Allargare il vincolo di blocco per prenderli produrrebbe elenchi dove
servono titoli, e romperebbe la direzione che oggi regge perfettamente — le
testatine `8. BESTIARIO` di DIE stanno anch'esse in blocco `b0000` di pagine
diverse, cioè nella **stessa** configurazione dei sette che mancano.

Quella è la ragione vera per cui non si allarga: non è prudenza procedurale, è che
il segnale che separa un titolo numerato da una testatina ripetuta **non è la
posizione**, ed è lo stesso genere di scoperta che ha fatto cadere il criterio
degli elenchi puntati.

## 4. Una nota sul protocollo, la terza volta che compare

L'etichettatore ha chiuso scrivendo che le righe 09-11 e 32/35 erano «le uniche
chiamate di **giudizio**, non di lettura». Sono esattamente le sette che decidono
questo esito, e sono state etichettate `voce` netta con la riserva **in prosa**.

Non cambia il verdetto — quelle righe sono davvero elenchi o titoli, non prosa —
ma il §4 del protocollo dice che un dubbio in prosa è un `incerto`, e con sette
`incerto` il giro avrebbe portato la questione all'utente invece che a un
conteggio. È la terza volta in questo giro che il canale viene aggirato, e va
scritto nel protocollo come regola più forte, non ripetuto come rilievo.

## 5. Che cosa questo pezzo ha spedito

Su FW p.168 le sette voci escono come elenco ordinato invece che schiacciate in un
paragrafo. Il numero **non si rinumera**: si tiene quello del manuale, perché un
elenco che continua da una pagina prima e comincia da `4.` riscritto `1.` direbbe
una cosa falsa.

E il giudizio esaustivo si è dimostrato la scelta giusta: **i 7 errori stanno
tutti nella lista delle scartate**, che un campione delle sole riconosciute non
avrebbe mai mostrato. Con 36 casi, guardarli tutti costa meno che difendere un
campione.

## 6. Conseguenza

Il criterio **non è scaricato**. La regola è **sicura ma stretta**: si può
spedire, perché non sbaglia mai nella direzione che distrugge testo, e lascia
scoperti sette titoli numerati che oggi restano paragrafi — cioè esattamente come
stavano prima.

Il fascicolo che sblocca questa copertura è **i titoli**, non gli elenchi.
