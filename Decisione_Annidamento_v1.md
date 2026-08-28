# Decisione — l'annidamento degli elenchi **non si fa**, e questa è la misura

**Decisione dell'utente, 28 agosto 2026**: «se l'annidamento è una cosa rapida
facciamola, altrimenti lasciamo perdere se è una sola occorrenza».

## Quante occorrenze sono

Misurato sui 16 manuali, marcatori e rientro mediano delle loro righe:

| manuale | marcatori |
| --- | --- |
| Apo, BiD, BoB, DB, DIE, Dag, FW, Fab, Lan, Vil, Wil | **uno solo** — l'annidamento non è rappresentabile |
| **FWK** | `•` a x=14, `*` a x=17 — **l'unico annidamento vero** |
| DrM | `!` `@` `#` tutti a x=12 — è una **scala di valori**, già isolata |
| DrW | `á` `é` `í` a x=52 — idem |

> **Undici manuali su sedici hanno un marcatore solo.** L'annidamento è **un
> manuale**.

## E non è una correzione rapida

La barra rossa di `scripts/check_list_regression.py` — due elenchi veri di FWK
persi — **è lo stesso problema**, non uno separato che si possa chiudere a parte.
Su FWK idx 117:

```
b0002  '*'  quattro voci
b0003  '•'  da solo
b0004  '*'  tre voci
b0009  '•'  da solo
b0010  '*'  quattro voci
```

I `•` sono i punti di **primo livello**, ognuno seguito dal proprio sotto-elenco
`*` in un blocco diverso. Ognuno è una corsa di **una** riga, quindi la regola non
li vede. Recuperarli richiede di sapere che `*` è subordinato a `•`, cioè
l'annidamento.

## Conseguenza

**Non si fa**, e le due cose che restano scoperte si dichiarano qui invece di
sparire:

1. Su FWK i punti di primo livello restano prosa. `check_list_regression.py`
   continuerà a dare **CADE** su due voci, ed è **atteso**: la barra resta accesa
   come promemoria, non come difetto da inseguire.
2. Le sotto-opzioni `*` escono allo stesso livello dei loro genitori. È la perdita
   di subordinazione che `Esito_Elenchi_v1.md` §3 aveva già registrato.

**Che cosa la riaprirebbe**: un manuale nuovo con annidamento, o la scoperta che
FWK non è solo. Il segnale per farlo esiste già ed è misurato — il **rientro**,
`•` a x=14 contro `*` a x=17 — quindi la riapertura costa poco. È il giudizio sul
rapporto fra costo e beneficio che è cambiato, non la fattibilità.
