# Esito di `Criterio_TitoloImpilato_v1.md` — **passa, e ripara più di Kul**

Scritto il 9 settembre 2026, dopo la misura e `check_eb.py`.

## 0. Stato in una riga

Tutti i veti passano. La regola unisce **43 titoli** su cinque manuali, e la
figura che ripara non è quella da cui il lavoro era partito.

## 1. I veti

| veto | esito |
| --- | --- |
| **A** — le colonne affiancate di BoB | **passa**: 555 titoli prima, 555 dopo, nessuna delle 22 unita |
| **B** — il bersaglio su cinque manuali | **passa**, 5 su 5 |
| **C** — il giudizio sui nuovi | **passa**: 15 su 16 nel campione, e il sedicesimo non è di questa regola |
| **D** — la copertura | **passa** |
| **E** — `check_eb.py` | **9/10**, sola Fab idx 126 già a verbale |

### A — il caso che aveva ucciso il tentativo precedente

`Esito_TitoloComposto_v1.md` §2 aveva ritirato il meccanismo B perché incollava
`'sgattaiolare' + 'ESEMPI'` e le sue dieci sorelle. **Restano separate**, e la
ragione non è una taratura: hanno **avanzamento negativo**, cioè la seconda riga
comincia più in alto della prima perché sta in un'altra colonna che il blocco ha
messo insieme. «Sotto» contro «accanto».

### B — il bersaglio, che si è allargato

```
Dag  'CAPITOLO UNO: PREPARARSI ALL'AVVENTURA'    80 → 75
BiD  'CAPITOLO 1 le basi'                       540 → 531
Lan  'SEZIONE 0 PER INIZIARE'                   619 → 613
SV   'CAPITOLO 1 LE BASI'                        85 → 75
Kul  'ORRORI DELLA'                             180 → 168
```

**Il guadagno vero non è Kul**: è il **numero di capitolo separato dal titolo**,
che su Dag, BiD, Lan e SV spezzava in due **ogni apertura di capitolo** — nel
markdown `# CAPITOLO 1` seguito da `## le basi`, due voci d'indice dove ce n'è
una.

### C — il giudizio

Campione di 16 sui 43 nuovi, seed `20260902`. Quindici sono titoli veri:
`'SEZIONE 3 SCONTRI TRA MECH'`, `'capitolo 3 ASTRONAVI ED EQUIPAGGI'`,
`'CREATURE DELLA PRIGIONE'`, `'ANGELI CADUTI SEMIDEI E ARCONTI'`,
`'GUIDA ALLA CITTÀ DI doskvol'`.

Il sedicesimo è `Kul idx 174 'DEMIURGO DEMIURGO IL FALSO DIO'`, con `DEMIURGO`
raddoppiato. **Non è un difetto di questa regola**: è una delle **5 coppie
quasi-identiche** che `Criterio_TitoloComposto_v1.md` §5 aveva dichiarato fuori
dalla sovrastampa — due su Kul — perché prenderle vorrebbe una tolleranza
geometrica cablata. L'unione l'ha reso **visibile dentro un titolo** invece che su
una riga a sé; non l'ha creato.

## 2. La regola, e perché i suoi confini non sono tarati

Tre confini, ognuno dentro un vuoto misurato su 114 coppie candidate dei sedici
manuali — dentro nessuno dei tre cade un solo caso:

| confine | vuoto | separa |
| --- | --- | --- |
| sovrapposizione ≥ **0,22** | 0,167 → 0,264 | interlinea normale da negativa |
| sovrapposizione < **1,00** | 0,871 → 1,025 | impilato da affiancato |
| avanzamento ≤ **1,50** | 1,182 → 3,898 | titolo che continua da paragrafo sotto |

Il quarto, **avanzamento > 0**, non è una soglia ma un **verso**, ed è quello che
regge il veto A.

**Le costanti stanno nel codice col loro vuoto accanto**, non nude: chi le trova
fra sei mesi vede subito se ha davanti un numero tarato o un numero misurato.

## 3. Una scelta d'implementazione che valeva la pena dichiarare

Il confronto geometrico è fra la riga e **quella originale che la precede**, non
fra la riga e l'unione accumulata. Su Kul `ORRORI DELLA GNOSI` sono tre righe: dopo
aver unito le prime due la scatola dell'unione è larga quanto entrambe, e misurare
la terza contro quella darebbe rapporti diversi da quelli misurati. Le 114 coppie
erano contate su righe consecutive, e l'implementazione le conta uguale.

## 4. Il costo, dichiarato prima e confermato

Sotto 0,22 restano spezzate cinque unioni giuste:

```
DIE  'GOBLIN' + '(E HOBGOBLIN)'      'GUARDIE' + '(E SOLDATI)'
     'HALFLING' + '(E GNOMI)'        'ALBERI' + '(TREANT E DRIADI)'
BoB  'LA CREATURA' + 'CON LE CORNA'
```

Una parentetica composta con interlinea **normale** non si distingue da
un'intestazione seguita da altro, e su questo asse non si può distinguere. Cinque
perse contro quarantatré guadagnate.

## 5. Che cosa resta aperto

- **`GNOSI`** su Kul resta orfano: sta a 102 pt e 102 non forma una fascia perché
  compare su meno di tre pagine. Il filtro delle tre pagine protegge dalle fasce
  inventate e nel farlo esclude le parole più grandi dei titoli display, che per
  costruzione compaiono poche volte. `ORRORI DELLA GNOSI` esce come
  `ORRORI DELLA` più `GNOSI`.
- **Le 5 coppie quasi-identiche** della sovrastampa, di cui una ora visibile in
  `'DEMIURGO DEMIURGO IL FALSO DIO'`.
- **`REALTAÀ`**, corruzione del testo sorgente.
- **Le schede**, nella chat dedicata. **Il debito del font**, aperto.
