"""Tirare fuori i byte di un asset da un PDF, con la sua trasparenza.

Adattatore di backend, allo stesso piano di `pymupdf_capture`: il PDF entra solo
qui, e il catalogo (`document_asset_catalogue`) non lo vede mai.

**La maschera va applicata, e non applicarla e' il difetto che si vede a occhio.**
Nei PDF il canale alfa e' un oggetto separato -- `/SMask` -- e
`Document.extract_image` restituisce **solo la base**: dove la maschera dice
«trasparente», la base porta nero. Misurato il 31 agosto 2026 su Dag: **1264
immagini su 1293, il 98%, hanno una SMask**, quindi quasi ogni illustrazione
ritagliata usciva su un rettangolo nero. E' lo stesso difetto che la pipeline
legacy ha tuttora in `extractor._raster_image_bytes_for_debug`, verificato
eseguendo `main.py Dag.pdf --pages 199-201`: otto file, tutti JPEG RGB, due
illustrazioni su fondo nero e zero trasparenza.

**Senza maschera i byte memorizzati escono intatti.** Se il PDF conserva un JPEG
esce quel JPEG, senza ricodifica: nessuna perdita che il documento non avesse
gia'. Il legacy invece ricodifica **tutto** in JPEG q=85 -- su Dag, 179 immagini
che il PDF conserva senza perdita e 1114 gia' JPEG che perdono una seconda
generazione. Qui non succede.

**Con maschera si passa per forza a PNG**: il JPEG non ha un canale alfa. Il file
cresce -- misurato, 239 KB -> 1452 KB su un'illustrazione di Dag, e la cartella di
Dag da 68 MB a 305 MB. E' il prezzo della trasparenza, non una scelta di qualita':
i pixel restano quelli del documento, e nessun formato restituisce dettaglio che
il PDF non ha. Tagliare i margini trasparenti recupererebbe il 7%, misurato su
quaranta file: non vale la complicazione.

**Cio' che questo modulo NON fa: la fotografia della regione di pagina.** Il
ripiego `rasterized_clip` di `scripts/prototype_vertical_slice_page` rende la
pagina dentro il riquadro dell'occorrenza, e quindi ci mette dentro il testo:
misurato su Fab, dodici campioni su dodici erano screenshot di paragrafi e
tabelle. Non e' l'asset, e un asset che non c'e' non si inventa -- si dichiara
assente e resta nel catalogo.
"""

from __future__ import annotations

from typing import cast

import fitz

from primitive_model import ImageOccurrencePrimitive

# I tre modi, e non sono intercambiabili.
METHOD_STORED = "stored"
METHOD_STORED_WITH_MASK = "stored+mask"


def extract_stored_raster(
    document: fitz.Document,
    xref: int,
) -> tuple[bytes, str, str] | None:
    """Il raster di una risorsa incorporata, con la sua maschera se ce l'ha.

    Restituisce ``(byte, estensione, metodo)``, o ``None`` se ``xref`` non
    identifica una risorsa -- che e' il caso dei raster che il renderer
    sintetizza da gradienti e maschere morbide, e per cui non c'e' niente da
    estrarre.
    """

    if not isinstance(xref, int) or isinstance(xref, bool):
        raise ValueError("xref must be an int")
    if xref <= 0:
        return None

    info = document.extract_image(xref)
    if not info:
        return None

    mask_xref = cast(int, info.get("smask") or 0)
    if mask_xref > 0:
        composed = _compose_with_mask(document, xref, mask_xref)
        if composed is not None:
            return composed, "png", METHOD_STORED_WITH_MASK
        # Maschera inservibile davvero: meglio la base intatta che niente, e il
        # metodo dichiara quale delle due si e' avuta invece di far finta.
        return cast(bytes, info["image"]), cast(str, info["ext"]), METHOD_STORED

    return cast(bytes, info["image"]), cast(str, info["ext"]), METHOD_STORED


def _compose_with_mask(
    document: fitz.Document, xref: int, mask_xref: int
) -> bytes | None:
    """Base piu' maschera, riscalando la maschera se ha un'altra taglia.

    **La maschera non ha sempre la risoluzione della base**, ed e' legale: il
    PDF la campiona sulla stessa area, non sugli stessi pixel. Misurato sul
    corpus: succede su **BiD, 4 immagini mascherate su 5**, e su nessuno degli
    altri sette manuali.

    `fitz.Pixmap(base, mask)` in quel caso solleva `FzErrorArgument` -- «color
    and mask pixmaps must be the same size» -- che **non deriva da RuntimeError
    ne' da ValueError**, ma da `FzErrorBase`. Un `except (RuntimeError,
    ValueError)` non lo prende, e la pagina intera muore: e' cosi' che questa
    funzione ha rotto BiD idx 287, e la barra E-B l'ha vista subito.

    Riscalare e' il rimedio giusto e non un ripiego: buttare la maschera
    riporterebbe l'illustrazione sul rettangolo nero, che e' il difetto che
    questa funzione esiste per chiudere.
    """

    base = fitz.Pixmap(document, xref)
    mask = fitz.Pixmap(document, mask_xref)

    # **Il CMYK va convertito, altrimenti la trasparenza si perde in silenzio.**
    # I manuali pronti per la stampa conservano le immagini in CMYK -- Wil e'
    # tutto `ICCBased(CMYK, Coated FOGRA39)` -- e PNG non ha il CMYK:
    # `tobytes("png")` alza `ValueError: unsupported colorspace`. Senza questa
    # conversione **583 immagini mascherate di Wil** ricadrebbero sulla base e
    # tornerebbero sul rettangolo nero, che e' il difetto da chiudere.
    # La conversione a RGB e' una trasformazione di colore, e va dichiarata:
    # e' quello che fa qualunque visualizzatore, ed e' obbligata dal formato.
    if base.colorspace is not None and base.colorspace.n > 3:
        base = fitz.Pixmap(fitz.csRGB, base)

    if (base.width, base.height) == (mask.width, mask.height):
        try:
            return fitz.Pixmap(base, mask).tobytes("png")
        except Exception:  # noqa: BLE001 - vedi FzErrorBase nella docstring
            return None

    from io import BytesIO

    from PIL import Image

    try:
        colour = Image.open(BytesIO(base.tobytes("png"))).convert("RGB")
        alpha = Image.open(BytesIO(mask.tobytes("png"))).convert("L")
        if alpha.size != colour.size:
            alpha = alpha.resize(colour.size, Image.Resampling.LANCZOS)
        colour.putalpha(alpha)
        buffer = BytesIO()
        colour.save(buffer, "PNG")
        return buffer.getvalue()
    except Exception:  # noqa: BLE001 - una maschera illeggibile non ferma la pagina
        return None


def stored_resource_xref(
    page: fitz.Page,
    primitive: ImageOccurrencePrimitive,
    *,
    raw_image_info: list[dict[str, object]] | None = None,
) -> int:
    """L'xref della risorsa di questa collocazione, o 0 se non ne ha.

    L'indice viene dall'``source_observation_id``, che `pymupdf_capture` compone
    nello stesso ordine in cui `get_image_info` elenca le collocazioni: e'
    l'unico aggancio fra la primitiva e la lista del backend, e vale finche' le
    due liste le produce lo stesso adattatore.
    """

    identifier = primitive.source_observation_id
    _, _, index_text = identifier.rpartition(":i")
    if not index_text.isdigit():
        raise ValueError(
            f"unexpected image source_observation_id format: {identifier!r}"
        )
    entries = (
        page.get_image_info(hashes=True, xrefs=True)
        if raw_image_info is None
        else raw_image_info
    )
    index = int(index_text)
    if index >= len(entries):
        raise ValueError(f"image observation {index} is not on this page")
    return int(cast(int, entries[index].get("xref") or 0))


def extract_occurrence_raster(
    document: fitz.Document,
    page: fitz.Page,
    primitive: ImageOccurrencePrimitive,
    *,
    raw_image_info: list[dict[str, object]] | None = None,
) -> tuple[bytes, str, str] | None:
    """Il raster di una collocazione, o None se la sorgente non ne conserva uno."""

    xref = stored_resource_xref(page, primitive, raw_image_info=raw_image_info)
    return extract_stored_raster(document, xref)
