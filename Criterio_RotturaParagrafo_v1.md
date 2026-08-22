# Criterio — la regola che rompe il paragrafo

Registrato **prima** dell'implementazione e prima di qualunque confronto. Da
committare in un commit **senza codice** (`AGENTS.MD` §15).

Il difetto non è da scoprire: è localizzato, verificato contro il render, e
misurato su un campione cieco. Questo criterio decide **se la correzione migliora
il Markdown**, e impedisce le tre forme in cui potrebbe sembrare di sì senza
esserlo: sistemare il caso che l'ha motivata rompendo l'opposto, perdere testo
mentre si riaggrega, e farsi giudicare da chi sa già quale versione è la nuova.

---

## 1. Il difetto, con la pagina e i numeri

`ir2_builder.py:168`, dentro `breaks_paragraph`:

```python
if not _STARTS_LOWERCASE.match(following):
    return True
```

**Ogni riga di sorgente la cui successiva non comincia in minuscola apre un
paragrafo nuovo.** Scatta su acronimi, parentesi, virgolette, cifre e nomi
propri.

**Verificato contro il render**, DIE pagina 380 (idx 379): sulla pagina «Usa il
Master come tuo personaggio… Il concetto di base del **GM** che interpreta la
versione da Classe…» è **un paragrafo solo**; in uscita si spezza esattamente su
`GM`. Nella stessa pagina si spezza di nuovo su `(nei processi, descritti di
seguito)`, che comincia con una parentesi.

**Misurato su campione cieco** (`Esito_FormaMancante_v1.md`): su 20 pagine
giudicate da una persona, **17 chiedono «spaziature»** — che in un file Markdown
sono righe vuote dentro un periodo, cioè questo difetto.

**La stessa regola era già caduta nella direzione opposta.**
`Criterio_ParagrafoDaRiga_v1.md` §5, esito in `Esito_ParagrafoDaRiga_Par5_v1.md`:
su DB p.99 gli stat block si spezzano **per campo** (`Movimento: 8  Danno Bonus:
—  PF: 8` è una riga sola sulla pagina e diventa tre paragrafi); su DrW p.97 i
glifi dei badge sono **minuscoli per la codifica** — `á` è U+00E1, il simbolo del
bersaglio è la lettera `o` — e vengono letti come prosa che continua.

Falliva in entrambi i versi. Finora se ne conosceva uno.

## 2. Il perimetro

**Si tocca**: `breaks_paragraph` in `ir2_builder.py`, e i suoi test.

**Non si tocca**: nessun producer, nessun modulo `page_analysis_*`, il
normalizzatore, `ir2_model.py`, `ir2_markdown.py`, `ir2_validate.py`, i renderer
legacy. Nessun flag nuovo. Nessuna modifica a `join_lines`, che è la giunzione e
non la decisione.

**Resta fuori, dichiarato**: il grassetto (`primitive_normalizer.py:98`
`font_traits=()`), che è l'altra metà del difetto misurato ma è un cambio di
contratto su `NodeIR2` e non entra qui; l'ancoraggio delle note a margine; il
cancello di emissione sulle full art; la deduplicazione degli span identici.

## 3. Il vincolo sul meccanismo, fissato prima

> La regola nuova **non può essere una lista di eccezioni a quella vecchia**.

Niente elenchi di acronimi, niente «continua anche se comincia con una
parentesi», niente insiemi di caratteri ammessi. È il vincolo più importante di
questo documento, per due ragioni: `AGENTS.MD` §Regole operative punto 7 vieta
l'hardcode su parola come soluzione primaria; e una lista di eccezioni si tara
sulle pagine che si stanno guardando, che è il modo esatto in cui questo progetto
ha già fabbricato quattro risultati non riproducibili.

**La grandezza su cui decide va desunta dal documento**, come i gutter di
`column_band` (Milestone 37, dove soglia di larghezza e support ratio sono cadute
a favore di «righe della pagina») e come il solo criterio sopravvissuto alle otto
falsificazioni dopo Milestone 35.

Il candidato naturale è tipografico e non lessicale — una riga che arriva al
margine destro della sua colonna continua, una che resta corta chiude il
paragrafo — con la tolleranza ricavata dalla distribuzione dei fine-riga del
blocco e non fissata in punti. **Non è imposto qui**: il criterio vincola la
forma della regola, non la sua identità. Se il meccanismo scelto è un altro, deve
comunque rispettare il vincolo di questo §3.

## 4. Il campione e il protocollo, fissati prima

Le pagine esistono già: sono le **40 di `Campione_FormaMancante_v1.md`**, seed
`20260824`, prodotte con la configurazione del §3 di `Criterio_FormaMancante_v3.md`
e non rigenerate.

Si dividono in due insiemi con ruoli **diversi e dichiarati adesso**:

| insieme | pagine | ruolo |
| --- | --- | --- |
| **primario** | le 20 **mai giudicate** (righe 21-40 del campione) | decide il §5 |
| secondario | le 20 già giudicate (righe 1-20) | si riporta, non decide |

Il primario è quello che decide perché sulle 20 già giudicate l'utente ha scritto
lui stesso che cosa non andava, e riconoscerebbe la versione vecchia. Le 20
secondarie restano utili proprio per questo: sono le uniche con una referenza
umana precedente.

**Il confronto è A/B cieco.** Per ogni pagina si producono due `page_ir2.md` —
prima e dopo la correzione — e si presentano come **A** e **B**, con quale dei
due sia il nuovo **estratto a sorte per pagina** con seed `20260825`, dichiarato
qui. L'utente non vede quale sia quale, e per ogni pagina risponde **una** cosa:

> **A si legge meglio** · **B si legge meglio** · **uguali**

Nient'altro. Nessuna causa, nessuna categoria: la domanda è una sola e il giro
precedente ha mostrato che una colonna «causa» su ogni riga fa rispondere a una
domanda diversa da quella posta.

La corrispondenza A/B → vecchio/nuovo si registra prima e non si guarda finché
tutte le risposte non sono date.

## 5. La regola di pass/fail

Sulle **20 pagine del primario**:

> **Regge** se «nuovo» vince su **almeno 10** pagine **e** «vecchio» vince su
> **al più 2**.
>
> **Cade** altrimenti.

Il modello nullo è «la correzione non cambia niente di percepibile», che predice
le vittorie ripartite a caso fra le due etichette. La barra chiede che fra le
pagine decise il nuovo prenda almeno cinque a uno: non è una differenza che il
caso produce, e non è nemmeno un miglioramento marginale spacciato per esito.

**Le due condizioni sono congiunte di proposito.** «Nuovo ≥ 10» da solo si
soddisfa anche peggiorando cinque pagine; il tetto di 2 sulle vittorie del
vecchio è ciò che impedisce di scambiare un difetto con un altro. Se la regola
nuova rompe la prosa mentre ripara gli acronimi, cade lì.

## 6. L'errore squalificante — la conservazione

> **Cade comunque**, qualunque sia il §5, se su **una sola** pagina delle 40 il
> testo emesso non si conserva.

Confronto meccanico fra prima e dopo: il **multiinsieme dei caratteri** di tutti i
nodi `text.paragraph`, ignorando gli spazi **e i trattini**, deve essere
identico. Se non lo è, la riaggregazione ha perso o inventato testo, e nessun
giudizio di leggibilità lo compensa.

I trattini sono ignorati perché `join_lines` ne toglie uno a ogni giunzione di
sillabazione (`ir2_builder.py:197`): unire due righe che prima erano separate
**deve** far sparire dei trattini, ed è il comportamento voluto. Si riporta
quindi anche il **conteggio dei trattini** dai due lati: un calo è atteso e
proporzionale alle giunzioni nuove, un aumento è impossibile e sarebbe un difetto.

**Limite dichiarato**: ignorare i trattini rende invisibile la perdita di un
trattino legittimo, per esempio in una parola composta. È il prezzo di non avere
un invariante di conservazione dei caratteri nel percorso IR 2
(`ir2_validate.py:84` verifica gli **id**, non i caratteri), che resta il porting
aperto del §10 di `Criterio_FormaMancante_v3.md`.

## 7. I due controlli, che il §5 non può vedere

Le pagine su cui la regola vecchia falliva nella direzione **opposta** sono
pagine di sviluppo ed escluse da ogni campione. Vanno guardate lo stesso, e a
vista:

| pagina | che cosa deve NON peggiorare |
| --- | --- |
| **DB p.99** | gli stat block, che la regola vecchia spezzava per campo |
| **DrW p.97** | i badge, i cui glifi sono minuscoli per la codifica |

> **Cade** se una delle due peggiora a giudizio dell'utente.

Non è chiesto che migliorino: una regola tipografica potrebbe non toccarle. È
chiesto che la correzione del caso frequente non paghi sul caso raro, che è
esattamente ciò che è già successo una volta in questo punto del codice.

## 8. Il modello nullo, e la sua debolezza

**Nullo**: la regola lessicale e quella nuova producono Markdown che una persona
non distingue; le «spaziature» dei venti verdetti erano una preferenza generica e
non l'effetto di questa regola.

**Debolezza**: il nullo è falsificabile solo attraverso un giudizio umano, dato da
una persona sola che sa che si sta lavorando sulle spaziature. La cecità A/B
toglie il sapere *quale* versione è nuova, non il sapere *che cosa* si sta
cercando. Le 20 pagine del primario non sono mai state viste, il che toglie il
riconoscimento; non toglie l'aspettativa.

**E la barra non è simmetrica**: chiede 10 a favore e concede 2 contro. Se la
correzione fosse un miglioramento reale ma piccolo — sette pagine su venti — il
criterio la dichiarerebbe caduta. È voluto: sette su venti non giustifica un
cambio che tocca la segmentazione di ogni pagina di ogni manuale.

## 9. Limiti dichiarati prima

**Cambia i numeri già a verbale.** La quota di paragrafi corti, la distribuzione
del §6.C di `Esito_FormaMancante_v1.md` e il rango di Wil idx 244 sono calcolati
sulla segmentazione vecchia. Dopo questo cambio vanno **rifatti, non ricopiati**.
Il rango di Wil idx 244 in particolare — 3 su 38 — è una proprietà della regola
lessicale quanto della pagina.

**E cambia la base di E-B.** Il confronto `--base` di `prototype_ir2_page.py`
verifica l'elenco dei paragrafi: dopo il cambio diverge per costruzione, e le
basi vanno rigenerate. **L'ordine di lettura non cambia**: la sequenza delle
righe di sorgente è la stessa, cambia solo come vengono raggruppate. Questo va
verificato e non assunto — è la prima cosa da controllare se il §6 fallisce.

**`DB` non è nel campione**, per le esclusioni di costruzione già dichiarate in
`Campione_FormaMancante_v1.md`. È il manuale da cui viene il controllo del §7, e
il fatto che compaia lì e non nel campione è una coincidenza da tenere presente,
non una compensazione.

**Il primario è di 20 pagine.** Con la barra del §5 una singola risposta cambiata
non ribalta l'esito, ma tre sì.

## 10. Che cosa NON decide

Non decide il grassetto, che è l'altra metà del difetto misurato e un cambio di
contratto. Non decide niente sulle note a margine, sul loro colore, né sul loro
ancoraggio — e in particolare non apre il detector di marginalia, che
`AGENTS.MD:598` gata. Non tocca l'uscita dallo shadow mode. Non riapre la linea
tabelle, in pausa. Non decide se `text.heading` vada emesso, che
`ir2_model.py:62` riserva a una milestone propria.
