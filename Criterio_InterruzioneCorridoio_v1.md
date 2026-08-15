# Criterio di accettazione — interruzione del corridoio, nel consumer

Scritto **prima** di implementare e **prima** di guardare gli output, come
`Criterio_GiunzioneFettaVerticale_v1.md` e per la stessa ragione. Il commit che
introduce questo file non contiene implementazione.

---

## 1. Cosa si costruisce, e dove

Il consumer taglia l'estensione delle bande dove qualcosa **attraversa** il
corridoio. **`column_band` non si tocca**: nessuna soglia nuova nel producer,
nessun cambio ai criteri di ammissione, nessun gutter nuovo. La regola può solo
accorciare o spezzare ciò che il producer ha già emesso.

Sta nel consumer perché richiede candidati di **altri** producer, e `AGENTS.MD`
§Layout e candidati — ratificato in Milestone 24 e 30 — assegna quella
combinazione al consumer o a Resolution, mai a un producer.

## 2. La regola

**Attraversa il corridoio → lo interrompe. Lo costeggia → no.**

Attraversare significa coprire per intero l'intervallo x del gutter. Costeggiare
significa arrivarci accanto senza coprirlo: su DrW p.97 l'immagine finisce a
x 299 e il gutter comincia a 299, e **non deve** interrompere.

Cosa attraversa, e da dove viene:

| sorgente | conta | perché |
| --- | --- | --- |
| candidato `embedded_visual` | **sì** | è il producer che dice dove sono le figure, con soglie ratificate in Milestone 27/28 |
| candidato `page_covering_visual` | **mai** | è il fondo pagina; contarlo bloccherebbe tutto — la trappola già vista con `--widen-bands` |
| `DrawingPrimitive` più basso della riga di testo più bassa **della pagina** | **sì** | non può contenere testo, quindi è un separatore e non una regione. Soglia desunta dalla pagina, non fissata |
| `DrawingPrimitive` più alto di così | **no** | è una regione, e le regioni devono arrivare da `embedded_visual`. Se una non arriva, è un buco di quel producer, e va chiuso lì invece di costruire qui un secondo rilevatore di visuali |
| testo | già coperto | il corridoio esiste solo dove il testo non copre l'intervallo x: un testo che attraversa lo interrompe già oggi |

I puntini di Dag p.164 sono `DrawingPrimitive` ad altezza 0,00 e larghi 480pt:
né testo né immagine, terza categoria. Rientrano nella terza riga.

## 3. Spezzare, non troncare

Un'interruzione **divide** la banda in due bande con gli stessi gutter, non la
tronca alla prima interruzione.

Non è una preferenza, è la classe di errore. Troncare butta fuori banda tutto
ciò che sta sotto l'interruzione: se lì le colonne proseguono davvero, quelle
primitive tornano all'ordinamento `(y0, x0)` e si mescolano riga per riga —
cioè **un falso negativo su regione multicolonna**, l'errore non recuperabile
(State.md:82). Spezzare non ha quel modo di fallire: sotto l'interruzione le
colonne restano separate.

## 4. Predizioni pre-registrate

Non concorrono a pass/fail. Servono a poter sbagliare.

- **DrW p.97: uscita identica.** Misurati 0 attraversamenti (0 candidati
  `embedded_visual` attraversano, 11 costeggiano; 0 filetti). `page_bands.md`
  deve restare **byte per byte** quello di adesso. Se cambia, la definizione di
  "attraversa" non è quella che credo.
- **Dag p.164: `TIRI DEGLI AVVERSARI` esce dalla colonna sinistra.** La banda
  y 0-324 si spezza a y 287,19 e il titolo (y 301,8) finisce nella parte sotto,
  dove la colonna destra è vuota.

## 5. Regola di accettazione

Precondizioni: gli invarianti della fetta (conservazione multiset, integrità dei
riferimenti) passano su tutte le varianti; `page.md` resta invariato.

Il giro regge se, giudicato a vista dall'utente:

- **A1 — nessun falso negativo su regione multicolonna reale.** Nessuna pagina
  in cui la regola faccia sparire una separazione di colonne che esisteva, con
  le due colonne che tornano a concatenarsi riga per riga.
- **A2 — nessuna regressione** su una pagina che oggi `page_bands.md` rende
  correttamente.

I falsi positivi — bande spezzate dove non serviva — si contano e non fanno
fallire, con la stessa precisazione del criterio precedente: qui non c'è nessuna
regola di Resolution a valle, quindi arrivano intatti nel markdown.

## 6. Cosa si sa già, e che non va spacciato per altro

- **Raggio d'azione misurato prima dell'implementazione: 47 bande su 277 (17%)
  su quattro manuali, accorciamento mediano 141pt, massimo 657pt.** È un raggio
  d'azione, **non** un'accuratezza: nessuna di quelle bande è stata guardata.
  Il 17% è il motivo per cui questa regola va dietro un flag e non accesa.
- Il contributo degli `embedded_visual` attraversanti **non è misurato**: sulle
  due pagine di prova è zero.
- Le pagine di prova sono ancore di sviluppo. Nessuna affermazione di
  accuratezza può uscire da questo giro.

## 7. Dopo

Come il criterio precedente: l'esito si scrive, e **nessun altro giro viene
proposto dall'interno di questo**. Se cade, si scrive cosa è caduto e su quale
pagina.
