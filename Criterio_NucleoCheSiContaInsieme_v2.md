# Criterio — il nucleo, v2: una scala non è una struttura

Dichiarato il 25 settembre 2026, dopo `Esito_NucleoCheSiContaInsieme_v1.md` e
**prima** della misura della v2.

## 1. Che cosa cambia

Una sola regola in più: **un nucleo le cui etichette, tolte cifre e segni, si
riducono a una sola radice è una scala, e non conta.** `Rango 1:` … `Rango 4:`
sono un campo solo con un grado che sale, non quattro campi. Stessa cosa per i
marcatori numerati `#1:` `#2:` `#3:` di Wilder.

E la variante è **sempre**: la vecchia strada dei riquadri accanto ai nuclei.
Su Wil ha deciso tutto (24 carte AREA meglio contro 21 peggio).

## 2. Che cosa tocca, prima di misurare

La regola filtra i nuclei e basta. Nei nove manuali i nuclei-scala sono due:
`{rango2, rango3, rango4}` su Dag e `{#1, #2, #3}` su Wil. La scala dei `segni` di
Vil si riduce a due radici (`segni`, `segno`) e non viene toccata; su Vil la v1
non cambiava niente.

**Dunque la v2 può cambiare solo Dag e Wil.** Sugli altri sette i nuclei sono
identici alla v1, e la resa — la pipeline è deterministica — è identica alla v1
`sempre` (o `muta`, dove non ci sono nuclei). Si verifica controllando che la
lista dei nuclei non cambi, e si rendono di nuovo solo Dag e Wil.

## 3. Che cosa deve succedere perché passi

**A. Il veto della v1 non c'è più.** Dag idx 324: nessuna cella esce dalle due
tabelle di armi.

**B. I meglio della v1 restano.** DB idx 90 e 119, Dag idx 50 e 361, BiD idx 304,
le 24 carte AREA di Wil.

**C. Nessuna tabella vera perde righe**, su nessuno dei nove: è il veto.

**D. La prosa tagliata**: i paragrafi che cominciano in minuscola non salgono,
**con un'eccezione dichiarata adesso**: l'orfano di Wil idx 148, la seconda riga
del valore di `Mostri:`, è già noto dalla v1 e non dipende dalle scale. Se resta
da solo, è quel caso e va a verbale come tale; se ne compare un altro, è il veto.

**E. Barra.** Test verdi, Ruff pulito, `check_eb.py` 9 su 10 con la sola Fab idx 126.

## 4. La previsione

Dag idx 324 torna intatto e il resto di Dag resta come nella v1 (+77 paragrafi).
Wil come nella v1 `sempre`, più eventuali differenze dove `{#1, #2, #3}` apriva
schede: mi aspetto qualche paragrafo in meno lì. Un solo orfano nuovo, quello
noto.
