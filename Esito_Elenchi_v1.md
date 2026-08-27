# Esito di `Criterio_Elenchi_v2.md` — **il veto cade, e non dove l'avevo previsto**

**Stato in una riga**: 14 voci giudicate, **9 `non elenco`, 4 `elenco`, 1
`incerto`**. Il veto del §3.A cade a una sola voce; ne sono cadute nove. Il
meccanismo **non si spedisce**.

Il criterio aveva nominato in anticipo **un** caso capace di romperlo — le righe
`…` di FW — e quello è caduto. Ma è **una** delle nove, e le altre otto vengono
da cause che non avevo previsto.

---

## 1. Il verdetto

| voce | manuale | carattere | esito |
| --- | --- | --- | --- |
| 01 | DrM | `#` | **non elenco** |
| 02 | BoB | `\x8b` | incerto |
| 03 | FWK | `•` | elenco |
| 04 | DrM | `!` | **non elenco** |
| 05 | BoB | `\x8b` | elenco |
| 06 | DrM | `@` | **non elenco** |
| 07 | FWK | `*` | **non elenco** |
| 08 | FW | `•` | elenco |
| 09 | DrM | `!` | **non elenco** |
| 10 | FWK | `•` | elenco |
| 11 | DrM | `!` | **non elenco** |
| 12 | DrM | `#` | **non elenco** |
| U1 | FW | `…` | **non elenco** (d'ufficio) |
| U2 | DB | `✦` | **non elenco** (d'ufficio) |

## 2. La causa principale: il glifo non marca una voce, **porta un valore**

Sei delle nove cadute sono DrM, e sono **la stessa cosa**.

`!`, `@` e `#` su DrM sono in **`DrawSteelGlyphs-Regular`**, un font di simboli, e
compaiono sempre nella stessa terna dentro lo stesso blocco:

```
!	 5 fire damage; m<1] weakened (save ends)
@	 9 fire damage; m<2] weakened (save ends)
#	 11 fire damage; m<3] weakened (save ends)
```

Sono i **tre esiti di un tiro** — `≤11`, `12-16`, `17+` — e il glifo *è* il
valore. Toglierlo non toglie un pallino: toglie la fascia di risultato a cui quel
danno si applica. Verificato sul PDF, non dedotto dal giudizio.

E la regola non si limita a togliere il glifo: **raccoglie in un elenco unico le
righe dello stesso tier prese da abilità diverse**. Sulla voce 09 sono sei righe
`≤11` di sei creature diverse, che diventano un elenco di danni scollegati dove
`2 damage` compare due volte senza che si capisca di chi sia.

> **Le cinque condizioni strutturali del §1 non potevano vederlo.** `@` e `#`
> aprono 45 righe ciascuno, sono al 100% a inizio riga, hanno testo dopo, stanno
> su più pagine, non sono punteggiatura appaiata. Passano tutto a pieni voti.
> Nessuna proprietà di **dove vive** un carattere distingue «segno che marca una
> voce» da «glifo che codifica un numero».

Questo è il limite che il §3.C del criterio aveva descritto in astratto per `…` e
che si rivela **molto più largo** di quel caso.

## 3. Le altre tre cadute, ognuna una cosa diversa

**Voce 07, FWK `*` — la subordinazione si perde.** Le tre righe sono le opzioni
**rientrate** appese all'esito `7-9` di una mossa, dentro una scaletta `10+` /
`7-9` / `1-6`. Nella sorgente il rientro non c'è: l'unica cosa che le marcava come
secondo livello **era l'asterisco**. Togliendolo si mettono alla pari degli esiti,
e non si legge più che valgono solo sul 7-9.

Il criterio dichiarava l'annidamento «fuori scope». Il giudizio dice che non è una
funzione mancante ma **una perdita di contenuto**: appiattire non è neutro.

**Voce U2, DB `✦` — una riga sola non fa elenco.** Nei due riquadri capacità c'è
**una** riga con la stellina, `✦ Punti Volontà: 3`, seguita dal paragrafo che
descrive la capacità. La stellina marca «questa è la riga del costo». L'uscita
produce due trattini identici affiancati che sembrano un elenco di due voci
uguali, e si perde quale capacità costi 3.

La condizione «almeno due righe» del §1 è **per pagina e per marcatore**, non per
elenco: due riquadri con una riga ciascuno la soddisfano.

**Voce U1, FW `…` — il caso previsto.** L'ellissi completa la frase della fascia
introduttiva «Reazioni dell'Agente: Qualcuno…». Tolta, `trascura doveri,
responsabilità, obblighi.` resta un sintagma senza soggetto. E la pagina distingue
di proposito: sopra usa `•` per un elenco vero, qui usa `…`.

## 4. La via d'uscita che il criterio si era lasciato **non basta**

Il §3.A diceva: «se cade solo su `…`, non si butta la regola, si cambia il §2 — il
marcatore si tiene invece di toglierlo».

Non cade solo su `…`, e tenere il marcatore **salva una caduta su nove**:

| caduta | tenere il marcatore la salva? |
| --- | --- |
| DrM (6 voci) | **no** — resta un elenco che sulla pagina non esiste, e `# 11 fire damage` non dice al lettore `17+` |
| FWK 07 | **no** — la subordinazione non si rende comunque |
| DB U2 | **no** — una riga sola non diventa un elenco |
| FW U1 | **sì** |

L'errore non è **che cosa si fa del marcatore**: è **decidere che quelle righe
siano un elenco**. Le due decisioni che il criterio teneva separate cadono
insieme, e cade la prima.

## 5. Che cosa regge

Le 4 voci `elenco` sono elenchi puntati veri, piatti, introdotti da una frase:
FWK `•` di primo livello (03, 10), BoB `\x8b` in colonna di testo (05), FW `•`
(08). Su quelli la trasformazione fa esattamente ciò che promette.

**Il segnale non è inutile: è ambiguo.** Trova i punti elenco veri e trova anche
glifi che non lo sono, e nulla in *dove vivono* li separa.

## 6. Un difetto del mio materiale, che non ha cambiato l'esito

Il campione mostrava le voci **troncate a fine riga fisica** — `Il tuo drago
non-morto è [ingombrante], [pesante], [lento] e` — perché lo costruivo dalle righe
sorgente. Il renderer vero **unisce** le continuazioni: la stessa voce esce
`- Il tuo drago non-morto è ***[ingombrante], [pesante], [lento]*** e
***[rumoroso]***; scegli un'altra opzione:`. Verificato.

L'agente l'ha notato da solo e ha dichiarato di non poterlo verificare.
**Nessuna delle nove motivazioni `non elenco` cita il troncamento** — sono tutte
sui tier, sulla subordinazione, sulla riga singola e sull'ellissi — quindi il
verdetto regge. Ma il materiale era degradato rispetto all'uscita vera, ed è un
difetto mio da non ripetere: il campione va costruito dalla **resa**, non dalla
sorgente.

## 7. La voce `incerto`, e perché è il rilievo migliore del giro

BoB voce 02: i rombi stanno in riquadri divisi in **due colonne**, `RICOMPENSE
MISSIONE:` e `PENALITÀ MISSIONE:`. Le voci sono monche — `Tempo.`,
`Approvvigionamenti.` — e vivono solo grazie all'intestazione di colonna. In un
elenco unico, `Approvvigionamenti. Sempre.` (ricompensa) e `Morale. A volte.`
(penalità) diventano indistinguibili.

L'agente ha scritto: se le intestazioni sopravvivono fra i gruppi è elenco pulito,
se il riquadro le fa cadere è non elenco grave; non ho modo di vederlo, quindi non
decido. **È l'uso giusto di `incerto`**, ed è la correzione al protocollo del giro
scorso che ha funzionato: nessuna etichetta netta con una riserva accanto.

## 8. Che cosa la regola manca, secondo chi ha guardato le pagine

- **DrM non ha nessun elenco puntato vero.** Le righe che lo sembrano sono le
  scalette di tiro e le righe di abilità precedute da un'icona — `★` per i tratti
  passivi, `☠` per le Villain Action — dove l'icona marca **il tipo di abilità**.
  Stesso rischio, stessa causa.
- **Le scalette di esito** (`10+` / `7-9` / `1-6`) sono ordinate e mutuamente
  esclusive: un elenco piatto le rappresenta male.
- **Le tabelle di tiro `D6 / NOME`** su DB non sono elenchi, e vale la pena
  controllare che nessun criterio le raccolga.

## 9. Conseguenza

> **Il meccanismo non si spedisce.** `--elenchi` resta spento di default, che è
> già il suo stato.

Il criterio è **caduto**, non «caduto e da ritarare». Rifare le soglie non
servirebbe: non c'è soglia che separi un glifo che marca una voce da un glifo che
porta un valore, perché la differenza non sta nella posizione ma nel significato.

**Che cosa un criterio successivo avrebbe da usare, e che va scritto prima:**

- la terna **fissa e ripetuta** di glifi diversi dentro lo stesso blocco — `!`
  `@` `#` in quest'ordine, sempre — è la firma di una **scala di valori**, non di
  un elenco. Un elenco ripete **lo stesso** glifo;
- un glifo che compare **una volta sola** per riquadro non apre un elenco;
- il **rientro** distingue i livelli, ed è nelle primitive: la voce 07 si perde
  proprio perché il rientro non è stato guardato;
- le schede mostro sono una categoria a sé, e `State.md` lo dice già.

Nessuna di queste è stata provata. Stanno qui come **input a un criterio**, non
come regola, ed è la stessa distinzione che ha tenuto onesto il terzo ramo
dell'arredo.

## 10. Che cosa questo giro ha comunque prodotto

- La misura di `document_line_start_measurements` è **buona e resta**: i due
  numeri INIZ/TOT sono la risposta giusta alla domanda «dove vive un carattere».
- Il fatto che **il marcatore sia specifico del manuale** — `✦`, `\x8b`, `↳`,
  `⬣`, `◈` — regge, ed è misurato su 16 manuali. Una lista cablata ne prendeva 3.
- La correzione del §5.C della v1 ha eliminato **tutti** i falsi positivi
  strutturali (`.` di Kul, `“` di SV). Quelli che restano non sono strutturali.
- La correzione al protocollo di giudizio ha funzionato: 1 `incerto` usato bene,
  zero riserve in prosa accanto a etichette nette.
