# Le schede a una coppia per riga — criterio scritto PRIMA (passo 2 di 3)

## Da dove parte
Dopo il passo 1 (accettato, `RISULTATI_SEPARA_RIQUADRI.txt`) su Daggerheart
mancano ancora i 18 ambienti. I loro riquadri esistono, uno per scheda, ma il
criterio «almeno due righe con almeno due coppie» non li prende: le loro righe
portano **una** coppia ciascuna (`Impulses: …`, `Difficulty: 11`,
`Potential Adversaries: …`).

Perche' il criterio chiedeva due coppie per riga lo dice la docstring di
`markdown_ir.righe_a_campi`: «una riga con uno solo puo' essere prosa che
comincia in grassetto».

## La modifica, dichiarata prima
Un riquadro e' una scheda se contiene almeno **due righe con almeno una
coppia** etichetta/valore (`pila2.etichette`, invariata). E' la lettura larga
dello stesso appunto (`State.md:903`, «campi etichetta:valore»).

Parametro `min_coppie` di `markdown_ir.righe_a_campi` e `regioni_di_pagina`,
default 2, che riproduce tutti i giri precedenti; `--una-coppia` lo porta a 1.
Nient'altro cambia: stessa separazione del passo 1, stessa regola di
appartenenza, tabelle ancora escluse (sono il passo 3).

## Il rischio, detto prima
La guardia che si toglie esisteva per la prosa che comincia in grassetto. Un
riquadro con due capoversi in grassetto — un box di regole, un elenco
`✦ **Voce:** …` — diventa scheda, e il criterio non ha modo di escluderlo. La
misura lo conta e lo mostra.

## Misura
`confini_dal_riquadro.py --separa --senza-tabelle`, con e senza
`--una-coppia`, sui due manuali. Verita' invariata.

## Predizioni
- **P1** Daggerheart: almeno 16 dei 18 ambienti diventano prese, e ogni
  regione presa comincia dal nome.
- **P2** i 129 avversari restano presi, 129 dal nome.
- **P3** la riga di prosa di idx 2 resta mancata: non sta in un riquadro.
- **P4** Dragonbane: le 4 schede restano prese dal nome.
- **P5** nascono regioni scheda senza riga-verita': al piu' 10 su
  Daggerheart e al piu' 5 su Dragonbane, oltre alle 2 gia' note
  (AZIONI, GRUB).

## Accettazione
Il passo si accetta se P1, P2, P3 e P4 reggono e se, **al giudizio a vista
dell'utente**, nessuna delle regioni nuove senza riga-verita' e' prosa. Le
regioni nuove si mostrano con l'immagine della pagina. Se una e' prosa, il
criterio non basta, e va detto che cosa la distingue prima di cambiarlo
(`AGENTS.MD` §20). P5 si riporta.
