# La scheda e il suo nome in IR 2 — esito (passo 3a)

Criterio: `Criterio_SchedaInIR2_v1.md`, registrato prima dei giri «dopo». Base:
`main_ir2.py` a `f2d3df8`, sugli stessi intervalli, prima di qualunque modifica.
Le pagine si citano per **indice 0-based** (`idx`); dove compare il numero
stampato e' letto da `page.get_label()`, non dedotto.

## In breve

| | esito |
| --- | --- |
| R3, la condizione: nessuna pagina senza schede cambia | **REGGE** in sei giri su sei (tre intervalli, con e senza `--tabelle`) |
| R1, conteggi | **REGGE**: 130 su Daggerheart 36-56, 6 su Dragonbane, come predetto |
| R2, nomi | **REGGE**: 130 su 130 e 6 su 6, controllati sul testo dei titoli |
| R4, conservazione | **REGGE sull'IR**; la misura e' emendata, vedi sotto |
| R5, tabelle attraverso una scheda | 50 su Daggerheart, 6 su Dragonbane, 6 su DB, non costruite |
| R6, E-B | **REGGE**: 9 identiche su 10, la sola differenza e' Fab idx 126, gia' a verbale |
| R7, test | 1698 test verdi (1671 di prima + 27), 7 skipped; Ruff e BasedPyright puliti sui file nuovi |

**Tre emendamenti alla regola del nome**, dichiarati qui e trovati dal controllo
su DB, che il criterio non prediceva.

**Giudizio a vista dell'utente**, 11 settembre 2026, sulle sei pagine prima e
dopo mostrategli (Daggerheart idx 38 e 49, Dragonbane idx 29 e 33, DB idx 120 e
107, quest'ultima il falso positivo `ATTRIBUTI DEI PNG`): «sembrano buoni come
risultati». Non gli e' stata mostrata una pagina di controllo, che il criterio
chiedeva: la non-regressione e' coperta dal confronto byte a byte di R3, e va
detto che il giudizio non l'ha vista.

## Il controllo che ha trovato il difetto

Al primo giro DB 95-125 ha fatto cadere R4 su una pagina (idx 99, stampata 98).
Due righe di prosa diventavano titoli -- `#### penetranti che brillano di un
giallo malaticcio. La loro` e `#### lezza, possono essere…` -- e il taglio fra
le due rompeva la ricongiunzione di `bel-lezza`: il trattino ricompariva.

Il riquadro di quella pagina e' un'illustrazione (x 0-422, y 106-791) con sopra
anche prosa, e contiene due righe a campi: per il riconoscimento e' una scheda.
Il difetto e' **nella regola del nome**, e sono due:

1. **Righe non contigue.** La riga 9 entrava nel nome della riga 2 perche' le
   righe 3-8, fuori dal riquadro, non interrompevano la corsa. Avevo scelto di
   non esigere la contiguita' nell'ordine di lettura: era sbagliato.
2. **La prima riga era prosa.** Il primo tentativo -- «il nome non e' nel font
   del corpo della pagina» -- **e' caduto**: su quella pagina il font del corpo,
   quello che porta piu' caratteri, e' `Hideout-Regular` della tabella degli
   attacchi, e la descrizione e' in `MinionPro-Regular`. Misurato, non dedotto.

Misurata invece la condizione dei titoli di `Criterio_Titoli_v3.md`, «l'unica
alla sua dimensione dentro il suo blocco», portata alla scheda: **lo stile del
nome non ricompare nella scheda fuori dal nome.**

| | nomi | stile che ricorre |
| --- | --- | --- |
| Daggerheart | 130 | 0 |
| Dragonbane | 6 | 0 |
| DB | 6 | 3: la prosa di idx 99 (`MinionPro-Regular` 10, in 4 righe), `Ramo Basso` a idx 122 (etichetta di riga di una tabella, ricorre in `Nido di Vespe`), `PIPISTRELLO VAMPIRO` a idx 96 (34 pt, lo stile di `ANIMALI COMUNI` nella stessa regione) |

Terzo difetto, visto negli stessi dati: **il livello del nome scavalcava quello
per dimensione**, e a idx 97 `# **RAGNO GIGANTE**` (h1) diventava `####
**RAGNO GIGANTE**`, mentre `# **TROLL**` restava h1. Cambia quindi una scelta
che avevo dichiarato all'utente: un nome che e' gia' un titolo per dimensione
**mantiene il suo livello**; il livello «uno sotto la fascia piu' profonda» vale
per i nomi che titoli non sono.

**Emendamenti** (`AGENTS.MD` §20): contiguita' delle righe del nome; stile del
nome unico nella scheda, al posto della condizione sul font del corpo, che viene
tolta; livello per dimensione non scavalcato. Reggono senza sapere se il
meccanismo poi passa: la prima e' un difetto, la seconda e' la regola dei titoli
gia' in vigore nel progetto, la terza evita di declassare un titolo di sezione.
Dove sbagliano, sbagliano verso **nessun titolo** invece che verso un titolo
falso. **DB e' ora speso per la regola del nome**: la verifica su un manuale
fresco resta da fare, ed e' il terzo manuale sigillato.

## I numeri, a codice definitivo

Senza `--tabelle` (il default):

| | regioni | pagine con scheda | con nome | cambiate | titoli nuovi |
| --- | --- | --- | --- | --- | --- |
| Daggerheart 36-56 | 130 | 15 | 15 | 15 | 130, tutti h3 |
| Dragonbane intero | 6 | 6 | 6 | 6 | 6, tutti h3 |
| DB 95-125 | 7 | 7 | 3 | 2 | 2, h4: `IL CAVALIERE BRIGANTE`, `ATTRIBUTI DEI PNG` |

Con `--tabelle`: stesse regioni; cambiano 15, 6 e 6 pagine; le tabelle non
costruite perche' attraversano una scheda sono 50, 6 e 6.

Su Daggerheart i nomi escono uguali a quelli del giro prima degli emendamenti,
titolo per titolo, compresi quelli su due righe (`FALLEN WARLORD:
UNDEFEATED CHAMPION`, `VOLCANIC DRAGON: ASHEN TYRANT`).

## R3: la formulazione era sbagliata

R3 diceva «cambiano **esattamente** le pagine dove il riconoscimento trova almeno
una scheda». La meta' che decide -- nessuna pagina senza schede cambia -- regge
ovunque. L'altra regge su Daggerheart e Dragonbane e non su DB: quattro schede
senza nome (il nome sta fuori dal riquadro, come a idx 100, o la regola lo
scarta) e una il cui nome era gia' un titolo (idx 97, `RAGNO GIGANTE`) non hanno
niente da cambiare in 3a, e le loro pagine restano identiche, che e' l'esito
giusto. La formulazione si emenda qui, dichiarata: cambiano **solo** pagine con
una scheda, e cambiano tutte quelle con un nome nuovo da titolare.

## R4: la misura

Il criterio chiedeva i caratteri del **Markdown**, tolti `#` e `*`. Con le
tabelle accese quella misura conta come persi i `|` e i `---` di una tabella non
costruita, che sono sintassi. Quella che decide e' sui caratteri del **testo
dell'IR** -- nodi e celle -- in `scripts/compare_stat_block_innesto.py`.

Sull'IR regge ovunque tranne su Dragonbane con le tabelle, idx 29 e idx 33:
quattro trattini, **tutti di fine riga dentro una cella** -- `spa-`,
`Successiva-`, `Personag-` a idx 29, `fanta-` a idx 33, verificati sulle celle
del giro prima. Nella cella restavano; diventando paragrafo il costruttore li
ricongiunge. E' lo stesso emendamento che E-B fa gia'
(`Criterio_ParagrafoDaRiga_v1.md` §3).

## Falsi positivi visti

`AZIONI` (Dragonbane idx 13) e `ATTRIBUTI DEI PNG` (DB idx 107) sono box di
regole con due righe a due coppie. Come titolo il loro nome si legge bene, ma in
3b la nota direbbe «sfondo della scheda AZIONI»: va affrontato li'. `GRUB`
(Dragonbane idx 32) e' una scheda di PNG, anche se la verita' a quattro schede
non la contava.

## Per rifare

    git worktree add <cartella-base> f2d3df8     # le uscite «prima», senza toccare il worktree di lavoro
    ./venv/bin/python <cartella-base>/main_ir2.py <pdf> --out <prima> --pages <intervallo> [--tabelle]
    ./venv/bin/python main_ir2.py <pdf> --out <dopo> --pages <intervallo> [--tabelle] --processi 1 2> <dopo>.log
    ./venv/bin/python scripts/compare_stat_block_innesto.py <prima>/document.md <dopo>/document.md <dopo>.log
    ./venv/bin/python scripts/check_eb.py --pdf-dir <cartella dei PDF>

Intervalli: Daggerheart SRD `36-56`, Dragonbane Quickstart intero, DB `95-125`.
`--processi 1` perche' le righe `schede:` escano nell'ordine delle pagine. Il
confronto marca le pagine col numero del commento `<!-- page:NNNN -->`, che e'
l'indice piu' uno.

## R6, E-B

`scripts/check_eb.py` sul codice definitivo: **9 identiche su 10**, 577 s. La
sola differenza e' **Fab idx 126**, con le stesse lunghezze del verbale (base
797, nuovo 789): il ridisegno deduplicato di `Criterio_ConfrontoEB_v4.md` §4,
gia' a verbale dal 30 agosto 2026. Nessuna differenza nuova. Due giri su codice
intermedio avevano dato lo stesso esito.

## Aperto

La nota dello sfondo (3b) e le righe dentro la scheda (3c); gli ambienti di
Daggerheart a una coppia per riga; le schede il cui nome sta fuori dal riquadro;
la provenienza del titolo sul nodo; il terzo manuale.
