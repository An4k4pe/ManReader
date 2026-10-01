# Decisioni di formato: Fabula Ultima (Fab.pdf)

Ricavate dai render di p. 12, 40, 46, 72, 94, 116, 128, 129, 132, 163, 179, 181, 217, 305, 317, 324–326
(indici PDF; il numero stampato è l'indice − 2). Valgono per tutti i lotti.

## Glifi che la bozza non risolve da sola
Il profilo ha una resa per carattere, ma tre caratteri sono usati da font diversi con sensi diversi.
- `[glifo:a]` → nella riga delle affinità è **aria** (2ª casella) o **ombra** (4ª); a inizio di una voce di
  attacco è `[distanza]`; a p. 94 è l'icona della riga (Aria, Ombra); a p. 305 e 324 «a distanza (`[distanza]`)».
- `[glifo:b]` → **fulmine** (3ª casella) o **veleno** (9ª); a p. 94 l'icona della riga.
- `✦` → vuol dire **marziale** ovunque, **tranne** nella riga delle affinità (5ª casella) e a p. 94, dove è
  l'icona di **terra**: lì si toglie.
- Una `S` isolata davanti al nome di un'azione di un PNG (e «Il simbolo S» a p. 325) → `[azione]`.
  Le `u` isolate a p. 35 («somme u sottrazioni u …») → `→`.
- Spazi che la bozza aggiunge dopo i simboli: `【 INT + VOL】` → `【INT + VOL】`, `(✚ 5)` → `(✚5)`,
  `(✦ )` → `(✦)`, `】 ,` → `】,`. Le parentesi `【 】` restano, sono testo del manuale.
- Il rombo del manuale è `•`: a inizio riga è un punto elenco (`- `), a metà riga è un separatore e resta ` • `.
- Legenda delle icone tenute come simbolo: `✦` marziale, `⚡` incantesimo offensivo, `✚` abilità acquisibile
  più volte, `⚠` promemoria in testa alla pagina, `→` «poi».

## Titoli
- Livello dal segnalibro (pagine dei segnalibri = indici PDF). Classi e PNG del bestiario sono a livello 3.
- Fascia sfumata con svolazzo a sinistra (RUOLI NEL GIOCO, GUARDIA, 5. AFFINITÀ AL DANNO): è un **titolo**,
  non un riquadro; la bozza la rende `> *[Nota manoscritta]* **TITOLO**`, da correggere. Solo 18 su 81 sono
  nei segnalibri: per le altre, un livello sotto l'ultimo titolo con segnalibro.
- PNG senza segnalibro (i profili dei boss d'esempio, p. 317): un livello sotto il titolo che li contiene.
- Testate, linguette laterali (CAPITOLO 3 / PREMI START) e numeri di pagina non si riportano.
- Testo doppio per l'ombra tipografica (p. 2): una volta sola.

## Profilo di un PNG (bestiario e boss): struttura identica per tutti
```
### GHIGLIOPENDRA
**Liv 5 • BESTIA**

Centopiedi di grandi dimensioni … un attimo dopo.

**Tratti tipici:** lenta, pesante, resiliente, territoriale.

| DES | INT | VIG | VOL | PV | PM | Iniz. | DIF | D. MAG |
|---|---|---|---|---|---|---|---|---|
| d8 | d6 | d10 | d8 | 60 • 30 | 45 | 7 | +2 | +1 |

| fisico | aria | fulmine | ombra | terra | fuoco | ghiaccio | luce | veleno |
|---|---|---|---|---|---|---|---|---|
|  |  |  | RS | RS | VU | VU |  |  |

**ATTACCHI BASE**
- [mischia] **Mandibola** • 【DES + VIG】 • 【TM + 5】 danni da **veleno** e il bersaglio subisce lo status **debole**.
- [distanza] **Stridio** • 【DES + VOL】 • 【TM + 5】 danni da **aria** e …

**INCANTESIMI**
- [incantesimo] **Ignis** ⚡ • 【INT + VOL】+3 • 10 × B PM • Fino a tre creature • Istantanea.
  Ciascun bersaglio colpito subisce 【TM + 20】 danni da **fuoco**.
  **Opportunità:** ciascun bersaglio colpito subisce lo status **scosso**.

**ALTRE AZIONI**
- [azione] **Immersione** • Lo spinalodonte si immerge …

**REGOLE SPECIALI**
- **Volante** • Vedi pag. **309** per la spiegazione dettagliata di questa Abilità.
```
- Le nove icone delle affinità ci sono sempre e sempre in quest'ordine: l'intestazione è fissa, nella cella va
  la sigla (VU, RS, IM, AS) che nel render segue l'icona colorata; icona grigia = cella vuota. Nella bozza la
  sigla segue la sua icona ma resta attaccata a quella dopo (`RSghiaccio` = fuoco RS, poi ghiaccio):
  **controllare le sigle sul render**.
- `PV 60 • 30` resta in una cella sola. Sezioni assenti nel profilo non si aggiungono.
- p. 94: la colonna Icona della tabella dei danni ha `[icona]` in ogni cella.

## Classi (p. 178–221)
- Titolo della classe dal segnalibro; `ANCHE: …` riga in grassetto sotto il titolo; la frase in corsivo sul
  disegno è una citazione: `> *Non è facile riuscire a ingannare il destino.*`
- Le domande nel riquadro in testa: elenco puntato dentro `> [!note]`.
- BENEFICI GRATUITI… e ABILITÀ… : un livello sotto la classe. Ogni abilità un livello sotto ancora, con il
  contatore nel titolo:
```
##### ARCANUM DI EMERGENZA (✚6)
Finché sei in **Crisi**, il costo per evocare i tuoi Arcana è ridotto di 【LA × 5】 Punti Mente.
```

## Incantesimi e Arcana
Una voce per incantesimo; le etichette sono l'intestazione della tabella, che non si ripete come riga a sé:
```
**Lux** ⚡ • **PM:** 10 × B • **Bersaglio:** Fino a tre creature • **Durata:** Istantanea

Concentri la tua forza interiore … danni da **luce**.

**Opportunità:** Ciascun bersaglio colpito subisce lo status **confuso**.
```
Arcana (p. 181): titolo un livello sotto GLI ARCANA, poi le etichette verticali come campi:
```
##### ARCANUM DEL CIELO
**Domini:** nebbia, pioggia, tempeste.

**FUSIONE:** Hai Resistenza ai danni da **aria** e **fulmine**. …

**CONGEDO:** **Tempesta.** Scegli un qualsiasi numero di creature …
```

## Equipaggiamento (armi, armature, scudi, accessori)
Tabella GFM con le colonne dell'intestazione più un'ultima colonna senza titolo per la riga sotto il nome.
Le categorie (Arcane, Archi…) in grassetto sopra la propria tabella. Il segnaposto dell'icona, se c'è, nella
prima cella prima del nome.
```
**Da Fuoco**

| ARMI | COSTO | PRECISIONE | DANNO | |
|---|---|---|---|---|
| **Pistola** ✦ | 250 z | 【DES + INT】 | 【TM + 8】 **fisico** | Una mano • Distanza • Nessuna Qualità. |
```

## Riquadri e blocchi ripetuti
- Riquadri numerati in sequenza (p. 32, 108, 305): elenco numerato `1.` con il testo e gli elenchi interni
  rientrati; il cerchio e lo svolazzo sono ornamento.
- Fondo colorato con «Esempio:» o esempio di gioco (p. 40, 46): `> [!example]`, una battuta di dialogo per riga.
  Fondo colorato con «Attenzione:» o senza etichetta: `> [!note]`.
- Riquadri con titolo in fascia (tabelle d6 di p. 223): `> [!note] CERCATORI`, voci come elenco numerato, la
  domanda in corsivo rientrata sotto la voce.
- La riga con `⚠` in testa alla pagina (p. 169, 217): paragrafo a sé, in cima alla pagina.
- Sequenze con la freccia (p. 64): una riga, `**Turno PG** → **Turno PNG** → …`.
