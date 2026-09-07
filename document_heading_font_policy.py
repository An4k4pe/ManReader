"""Quali facce di carattere intestano, e quale riga e' un titolo per il font.

**IL MECCANISMO E' CADUTO E QUESTO MODULO NON E' COLLEGATO.**
`Esito_TitoliDalFont_v2.md`: il veto delle schede cade con 29 righe su Wil idx
148 (`'[D] <= 4'`, `'Mostri: hutangwa, kala-kala...'`), la filigrana di Fab passa
su 362 pagine, e il volume e' fuori scala -- 5871 righe promosse su Dag contro un
bersaglio di 1900.

**La diagnosi, che e' il motivo per cui resta in albero.** Sotto il tetto della
prosa, «non e' prosa di corpo» e' una popolazione enorme: numeri di pagina,
didascalie, etichette, voci d'indice, celle di scheda, filigrane. Il compositore
usa **le stesse facce** per tutte, perche' fanno lo stesso mestiere tipografico --
stare fuori dal flusso. Quindi il font distingue il **flusso dal non-flusso** e
non distingue le parti del non-flusso **fra loro**: su Dag `PANORAMICA` e `220`
sono entrambe in `EvelethCleanRegular`, ed e' corretto che lo siano.

Chi affrontera' le schede riparte da qui, perche' quel meccanismo dovra'
distinguere proprio dentro il non-flusso.

`Criterio_TitoliDalFont_v2.md` §1. **Politica, non misura**:
`document_heading_font_measurements` conta e non decide, questo decide.

**Il debito che paga.** Su Dag `PANORAMICA` sta a 12,0 pt in
`EvelethCleanRegular` mentre la prosa sta a 12,1 in `QuestaSans-LightItalic`:
sull'asse della dimensione i titoli stanno **sotto** la prosa, e nessuna regola di
misura li puo' raggiungere. Sotto il tetto di Dag stanno anche `INTRODUZIONE`
(1080 righe su 243 pagine) e `DAGGERHEART TEAM` (822 righe su 308).

**Che cosa e' gia' caduto qui, e non si rifa'.** La v1 di questo criterio aveva
come perno il filtro della **famiglia** -- una faccia intesta se la sua famiglia
e' diversa da quella del corpo -- giustificato su un confronto in un manuale solo.
`Esito_TitoloSopraIlParagrafo_v1.md` §3 lo aveva gia' misurato su **sedici**
manuali: 152 promozioni cambiano famiglia, 90 cambiano peso, con controesempi da
entrambe le parti -- `Wil 'Incendi.'` cambia famiglia e non e' un titolo,
`Dag 'Il potere di Sprout'` cambia solo peso e lo e'. Il filtro e' ritirato.

**Che cosa questo modulo NON tratta.** Le **schede**: una cella di scheda sta in
un blocco che non contiene prosa di corpo, quindi passa il guardiano. Le schede
hanno gia' fatto cadere quattro meccanismi e si gestiscono a parte -- indicazione
dell'utente del 7 settembre 2026. Qui sono l'oggetto del **veto principale**, non
di una condizione.
"""

from __future__ import annotations

from collections.abc import Sequence

from document_heading_band_policy import LINE_RATIO, MIN_PAGES, WORD_SHARE
from document_heading_font_measurements import FontMassMeasurements
from document_heading_measurements import SizedLine


def heading_faces(
    measurements: FontMassMeasurements,
    *,
    body_median_line: float | None,
) -> frozenset[str]:
    """Le facce che intestano, dai tre filtri delle fasce sulla nuova popolazione.

    Sono gli **stessi** valori dell'asse della dimensione, e non e' una comodita':
    se il 60% e il mezzo separano decorazione e prosa fra le fasce, separano le
    stesse cose fra le facce, o non separavano neanche prima.

    1. **porta parole** -- toglie i font simbolo, che si riconoscono dai testi di
       un carattere: `Glyphter` e `BodoniOrnamentsITCTT` su Fab hanno mediana 1;
    2. **righe corte** -- toglie la prosa composta in un'altra faccia:
       `MonotypeCorsiva` su Fab ha mediana 49 su un corpo di 55;
    3. **almeno tre pagine** -- una faccia usata una volta non e' una scelta
       tipografica del documento.

    **Senza un corpo misurabile tace**, invece di inventare un rapporto.
    """

    if not body_median_line:
        return frozenset()
    return frozenset(
        font
        for font, lines in measurements.line_count.items()
        if lines
        and measurements.word_share(font) >= WORD_SHARE
        and measurements.median_line_length.get(font, 0.0)
        <= LINE_RATIO * body_median_line
        and len(measurements.page_indices.get(font, frozenset())) >= MIN_PAGES
    )


def font_heading_lines(
    lines: Sequence[SizedLine],
    faces: frozenset[str],
    *,
    ceiling: float | None,
    body_sizes: frozenset[float],
) -> frozenset[int]:
    """Le posizioni delle righe che sono titoli **per il font**. `lines` e' una pagina.

    Due condizioni, e la seconda e' dell'utente (6 settembre 2026):

    1. la riga e' composta **interamente** in una faccia da intestazione e sta al
       tetto della prosa o sotto -- sopra il tetto il titolo lo trova gia' la
       dimensione, e assegnarlo due volte darebbe due livelli alla stessa riga;
    2. il suo **blocco non contiene righe alla dimensione del corpo**.

    **Perche' il blocco e non la faccia**, che era la mia prima stesura: la faccia
    e' una proprieta' **globale** del documento, il blocco e' il **contesto** della
    riga. Una riga dentro un blocco di prosa e' prosa qualunque sia il suo font, e
    cosi' il grassetto che apre un paragrafo resta fuori senza doverlo dedurre
    dalle statistiche della faccia.
    """

    if not faces or ceiling is None:
        return frozenset()

    prose_blocks = {
        line.block for line in lines if line.size in body_sizes
    }
    return frozenset(
        position
        for position, line in enumerate(lines)
        if line.font in faces
        and line.size <= ceiling
        and line.block not in prose_blocks
        and len(" ".join(line.text.split())) > 1
    )
