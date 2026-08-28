# Esito di `Criterio_MarcatoreDaFont_v1.md` — **18 su 18, e nessun campione**

**Stato in una riga**: tutte e 18 le voci che la via del font produce su Fab sono
giudicate `elenco`. Zero `non elenco`, zero `incerto`. **Il veto regge**, e le
barre B e C sono state verificate prima del giudizio.

---

## 1. Il veto §4.A — regge

| | |
| --- | ---: |
| voci prodotte dalla via del font | **18** |
| giudicate `elenco` | **18** |
| `non elenco` | 0 |
| `incerto` | 0 |

**Non è un campione**: sono tutte le voci che la regola produce su quel manuale.
Non c'è errore di campionamento da dichiarare, e questo esito non porta la riserva
statistica che gli altri di questo giro hanno dovuto portare.

**L'etichettatore ha confermato il meccanismo senza conoscerlo**, ritagliando e
ingrandendo i render: «su tutte e quattro le pagine la `w` non è disegnata come
una lettera. È un piccolo rombo pieno, in verde d'accento, di corpo minore
rispetto al testo, staccato da un rientro fisso. È il glifo di un font di simboli
mappato sul codepoint `w`». È esattamente ciò che la via del font è stata scritta
per vedere, arrivato dall'immagine.

E ha verificato la parte che decide: «ogni riga, tolto il rombo, inizia con la
maiuscola ed è una frase o una domanda completa e autonoma: non manca nulla».

## 2. Le barre B e C — verificate prima

**§4.B, le zero su DrM e DrW.** La via del font apre `M`, `I`, `R`, `P` su DrM e
`x`, `á`, `í`, `é` su DrW, e la **firma di scala** le riconosce come scale di
valori: **zero voci** su entrambi. Il meccanismo scritto per i badge di tier
coglie anche le abbreviazioni di caratteristica senza essere stato progettato per
farlo, ed è la ragione per cui questa via è sicura — non perché sia precisa.

**§4.C, additiva.** Sui 16 manuali cambia **solo Fab**, da 0 voci a 18. Gli altri
quindici restano identici.

Ci sono volute due condizioni che la misura ha imposto e che il criterio non
aveva:

- **il glifo dev'essere una primitiva a sé** — una prima versione cercava una
  qualunque primitiva con quel carattere sulla pagina, e bastava un `M` isolato
  perché ogni riga che comincia per `M` diventasse voce: **FW passava da 57 a 92**;
- **e dev'essere seguito da spazio** — su FWK `Bruinloa` ha la `B` in un font
  decorativo, primitiva a sé, ed è un **capolettera**: **FWK passava da 136 a 140**.

## 3. Un difetto di copertura, rilevato e reale

L'etichettatore ha osservato che sotto `BENEFICI GRATUITI DELL'ARCANISTA` e
`BENEFICI GRATUITI DELLA CANAGLIA` c'è **una voce puntata sola**, con lo stesso
rombo, che non compare fra le 18.

È la condizione «una corsa di due o più» di `Criterio_ScalaDiValori_v1.md` §1, ed
è **voluta**: una riga sola non è un elenco, ed è ciò che tiene fuori le righe di
costo di DB (`✦ Punti Volontà: 3`, una per riquadro).

> **Ma qui costa**: dove un elenco ha una voce sola, quella voce resta prosa. È un
> difetto di **copertura**, non un falso positivo, e va nominato invece di
> lasciarlo scoprire a chi legge.

## 4. Un rilievo che **non si riproduce**, e la causa è del mio materiale

L'etichettatore ha segnalato che su idx 184 «due elenchi diversi finiscono in uno
solo»: le voci dei benefici e quelle delle domande, separate da un titolo di
sezione, uscirebbero come un elenco unico di sei voci.

**Verificato sulla resa vera, non succede:**

```markdown
- Il tuo campo è qualcosa di diffuso, oppure una disciplina rivoluzionaria?
- Quando usi le tue capacità per creare un oggetto o effetto, che aspetto ha?

### BENEFICI GRATUITI DELL'ARTEFICE

- Aumenti permanentemente i tuoi Punti Inventario massimi di 2.
- Puoi avviare i **Progetti**.
```

Il titolo li separa. **Era un artefatto del materiale che ho preparato io**, che
raggruppava tutte le voci di una pagina in un unico blocco `Come escono:`. È il
terzo giro di fila in cui il materiale è più debole del giudizio, e stavolta ha
prodotto un rilievo su un difetto che non esiste.

Il modo di non ripeterlo è quello già imparato: **il materiale si costruisce dalla
resa della pagina intera**, non ricomposto per voce.

## 5. Che cosa questo giro ha spedito, oltre alle 18 voci

Sulla stessa pagina si vede una cosa chiesta dall'utente e ottenuta di rimbalzo:

```markdown
### **FORMULA SEGRETA** (ç5)
```

Il costo `(ç5)` — un glifo Wingdings2 fra parentesi — è **attaccato al suo
titolo**. Prima usciva come riga a sé, e l'utente aveva scritto: «o lo leggi
vicino al resto del titolo o è incomprensibile». Lo ha chiuso l'unione dei titoli
che vanno a capo di `Criterio_Titoli_v3.md` §2, che non era stata scritta per
questo.

## 6. Verifiche

Suite **1472** test, un solo fallimento, quello ambientale già a verbale.
`check_list_regression.py` e `check_numbered_lists.py` invariati.

## 7. Conseguenza

Il criterio è **scaricato** su tutte e tre le barre: veto a 18 su 18 senza
campionamento, zero su DrM e DrW, additivo sui sedici manuali.

Resta scoperto, dichiarato al §3: **gli elenchi di una voce sola**.
