# Esito — il ramo **cade**, e cade sulle schede per la quarta volta

**Stato in una riga**: la barra di copertura passa **4 su 4**, la regressione è
**zero su 16**, e il veto cade — non su una riga, su **novanta**. Il ramo è
ritirato dal costruttore nello stesso commit che lo misura.

---

## 1. Le tre barre

| barra | esito |
| --- | --- |
| **B** — i quattro casi nominati | **passa, 4 su 4** |
| **C** — la dimensione non cambia | **passa, 16 manuali su 16, differenza zero** |
| **A** — veto | **CADE** |

### B passa, e si vede

```
### **LA DONNA DI CENDRES**            ### **DONI**
                                       **I doni sono aspetti del tuo retaggio…**
Nonostante alcune remore, Gabriel…
                                       ### **EFFETTI**
### **L'ARRIVO DELL'OSCURITÀ**
                                       Usare un dono attiva un effetto positivo…
```

Su Vil `DONI` era attaccato al paragrafo **dall'unione delle righe a pari
dimensione**: `DONI` e le quattro righe che seguono sono tutte a 11,6 nello stesso
blocco, e `merge_wrapped` se lo mangiava. È da lì che veniva
`**DONI I doni sono aspetti…**` in un grassetto solo.

### C passa

Il ramo per dimensione produce esattamente gli stessi titoli, prima e dopo, su
tutti e sedici. La rottura forzata dei gruppi non tocca la scala dei ranghi.

## 2. Perché A cade

**242 righe promosse** dentro la popolazione campionabile. Non ho avuto bisogno
del giudizio cieco: le righe che non sono titoli si leggono a occhio nella misura.

```
FW  idx157   Non dire mai semplicemente "subisci Svantaggio".      prosa, prima frase di un riquadro
Kul idx113   alle Dormienti.                                        coda di paragrafo
Wil idx148   Raro. Ottieni (1) Ferito o, se questo pasto…           prosa in una cella
Wil idx148   [D] ≤ 4   /   [D] ≥ 5                                  celle di tabella
DIE idx195   Base:  /  Elite:  /  Eroe:                             etichette di scheda, 48 volte
Fab idx175   Furia (3 livelli): Frenesia, Sopportazione (2 LA)      riga di tabella, 29 volte
```

E la dispersione dice dove sta il danno:

| manuale | aggiunte | | manuale | aggiunte |
| --- | ---: | --- | --- | ---: |
| **Wil** | **84** | | Apo | 30 |
| **DIE** | **48** | | Vil | 30 |
| **Fab** | **29** | | Dag | 16 |
| | | | Kul, SV, FW | 2, 2, 1 |
| | | | BiD, BoB, DB, FWK, Lan | **0** |

Su Apo e Vil il ramo fa quello per cui è scritto. Su Wil, DIE e Fab produce
**161 righe** che sono celle di scheda, righe di tabella e prose spezzate.

> **È il quarto meccanismo che cade sulle schede.** Il primo è stato il produttore
> di tabelle, il secondo la ricorrenza di posizione, il terzo il giudizio degli
> elenchi — nove voci su quattordici erano i gradi di potere di DrM — e questo è
> il quarto. `Criterio_Titoli_v3.md` §3 aveva tolto dal campione **DrM e DrW**,
> e la mossa era giusta sull'asse sbagliato: il problema non è il manuale, è la
> **pagina**. Wil 148 è una scheda d'area, DIE 195 una scheda mostro, Fab 175 una
> tabella di classe, e stanno tutte e tre dentro manuali che il criterio conta.

Ridisegnare la popolazione adesso è esattamente ciò che `AGENTS.MD` §15 vieta e
che io stesso ho scritto nel §3 del criterio. Il ramo cade con la popolazione che
si è dichiarato.

## 3. L'ipotesi che sembrava salvarlo, misurata e scartata

Guardando i falsi positivi si vede un candidato ovvio: i casi buoni cambiano
**famiglia** di carattere, i cattivi solo **peso**.

```
Apo   CallunaSans-Semibold / ArnoPro-SmText     ← famiglia diversa, è un titolo
Vil   Calluna-Bold        / ArnoPro-Regular     ← famiglia diversa, è un titolo
FW    ACaslonPro-Regular  / ACaslonPro-Italic   ← stesso ceppo,  NON è un titolo
Fab   PTSans-NarrowBold   / PTSans-Narrow       ← stesso ceppo,  NON è un titolo
```

**Misurata su tutti e sedici, non separa**: 152 promozioni cambiano famiglia, 90
cambiano peso, e ci sono controesempi da tutte e due le parti.

```
famiglia diversa e NON titolo:  Kul 'alle Dormienti.'  GrenzeGotisch-Regular / Bonyland-Regular
                                Wil 'Incendi.'         Zedou-Bold / GaramondPremrPro-Med
solo il peso e SÌ titolo:       Dag 'Il potere di Sprout'    QuestaSans-Bold / QuestaSans-Regular
                                SV  'PATTUGLIA DI CONFINE'   Exo2-ExtraBold / Exo2-Regular
                                Fab 'Base' / 'Avanzato' / 'Superiore'
```

L'ho misurata **dopo** la caduta e la riporto come ipotesi scartata, non come
condizione aggiunta: il §4 del criterio dice di non aggiungere condizioni nello
stesso giro, ed è la regola che impedisce di girare intorno a una misura finché
non passa.

## 4. Che cosa resta vero anche se il ramo cade

**La diagnosi precedente era sbagliata e la correzione tiene.**
`Esito_Titoli_v3.md` §2.A chiamava «titoli in linea» undici titoli mancati. Non lo
sono: su Apo `LA DONNA DI CENDRES` è `b0001 l0000`, una riga sorgente sua, la
prima del suo blocco, sopra il paragrafo. Undici righe della statistica dei titoli
erano classificate su una causa che non esiste.

**E la dimensione nominale non misura quello che l'occhio vede.** 10,6 in
`Calluna-Semibold` tutto maiuscolo contro 11,6 in `ArnoPro-Regular` minuscolo: il
punto tipografico misura il corpo del carattere, non l'inchiostro. Chi guarda la
pagina e dice «il titolo è più grande» sta leggendo bene; è la misura che leggeva
male.

Questi due fatti valgono per qualunque v2, e sono il guadagno del giro.

## 5. Che cosa resta in albero

`headings_above_a_paragraph` resta in `document_heading_policy.py` e
`scripts/measure_headings_above_paragraphs.py` la misura su tutto il corpo. Il
costruttore **non la chiama**: è la stessa forma con cui è ritirata la clausola
del testo ripetuto nell'arredo — la regola resta leggibile e rimisurabile, e non
tocca la resa.
