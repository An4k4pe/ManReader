import io
import unittest

import fitz
from PIL import Image

from primitive_model import ImageOccurrencePrimitive
from pymupdf_asset_extraction import (
    METHOD_STORED,
    METHOD_STORED_WITH_MASK,
    extract_occurrence_raster,
    extract_stored_raster,
    stored_resource_xref,
)


def _png_with_alpha() -> bytes:
    """Un quadrato opaco con un angolo trasparente: la maschera si vede o no."""

    image = Image.new("RGBA", (40, 40), (200, 30, 30, 255))
    for x in range(20):
        for y in range(20):
            image.putpixel((x, y), (200, 30, 30, 0))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def _document_with_a_masked_image() -> fitz.Document:
    document = fitz.open()
    page = document.new_page(width=200, height=200)
    page.insert_image(fitz.Rect(20, 20, 100, 100), stream=_png_with_alpha())
    # Ricarico dai byte: l'inserimento diventa una risorsa vera con la sua SMask.
    return fitz.open("pdf", document.tobytes())


def _occurrence(index: int = 0) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=f"primitive:image:image:i{index:04d}",
        bbox=(20.0, 20.0, 100.0, 100.0),
        source_observation_id=f"image:i{index:04d}",
    )


class MaskCompositingTest(unittest.TestCase):
    def test_a_masked_image_comes_out_with_real_transparency(self) -> None:
        # Il difetto che si vedeva a occhio: senza questa composizione la base
        # esce su un rettangolo nero. Su Dag riguarda il 98% delle immagini.
        with _document_with_a_masked_image() as document:
            page = document[0]
            extracted = extract_occurrence_raster(document, page, _occurrence())
            self.assertIsNotNone(extracted)
            assert extracted is not None
            payload, extension, method = extracted
            self.assertEqual(extension, "png")
            self.assertEqual(method, METHOD_STORED_WITH_MASK)
            image = Image.open(io.BytesIO(payload))
            self.assertIn("A", image.getbands())
            alpha = image.convert("RGBA").getchannel("A")
            self.assertEqual(alpha.getpixel((2, 2)), 0)
            self.assertEqual(
                alpha.getpixel((image.width - 2, image.height - 2)), 255
            )

    def test_an_unmasked_image_keeps_its_stored_bytes_untouched(self) -> None:
        # Senza maschera non si ricodifica: nessuna perdita che il PDF non avesse
        # gia'. E' cio' che il legacy invece fa, con JPEG q=85 su tutto.
        document = fitz.open()
        page = document.new_page(width=200, height=200)
        opaque = Image.new("RGB", (30, 30), (10, 120, 200))
        buffer = io.BytesIO()
        opaque.save(buffer, "PNG")
        page.insert_image(fitz.Rect(0, 0, 60, 60), stream=buffer.getvalue())
        reloaded = fitz.open("pdf", document.tobytes())
        try:
            xref = stored_resource_xref(reloaded[0], _occurrence())
            extracted = extract_stored_raster(reloaded, xref)
            self.assertIsNotNone(extracted)
            assert extracted is not None
            payload, _extension, method = extracted
            self.assertEqual(method, METHOD_STORED)
            self.assertEqual(
                payload, reloaded.extract_image(xref)["image"]
            )
        finally:
            reloaded.close()
            document.close()


def _document_with_a_hand_attached_mask(
    base: Image.Image, mask_size: tuple[int, int]
) -> tuple[fitz.Document, int]:
    """Base e maschera agganciate a mano, per costruire i due casi difficili.

    `insert_image` non espone una `/SMask` separata, quindi la si aggancia
    nell'xref. E' l'unico modo di riprodurre in un test i due difetti che il
    corpus ha mostrato e che hanno fatto crashare due pagine intere.
    """

    document = fitz.open()
    page = document.new_page(width=300, height=300)
    buffer = io.BytesIO()
    base.save(buffer, "JPEG" if base.mode == "CMYK" else "PNG")
    page.insert_image(fitz.Rect(0, 0, 100, 80), stream=buffer.getvalue())

    mask = Image.new("L", mask_size, 200)
    for x in range(mask_size[0] // 2):
        for y in range(mask_size[1] // 2):
            mask.putpixel((x, y), 0)
    mask_buffer = io.BytesIO()
    mask.save(mask_buffer, "PNG")
    page.insert_image(fitz.Rect(200, 200, 260, 250), stream=mask_buffer.getvalue())

    reloaded = fitz.open("pdf", document.tobytes())
    xrefs = [t[0] for t in reloaded[0].get_images(full=True)]
    reloaded.xref_set_key(xrefs[0], "SMask", f"{xrefs[1]} 0 R")
    final = fitz.open("pdf", reloaded.tobytes())
    return final, [t[0] for t in final[0].get_images(full=True)][0]


class HardMaskTest(unittest.TestCase):
    """I due casi che hanno rotto BiD idx 287 e Wil idx 71, e li hanno rotti
    davvero: non una differenza, un crash che uccideva la pagina intera."""

    def test_a_cmyk_base_is_converted_instead_of_losing_its_mask(self) -> None:
        # Wil e' tutto `ICCBased(CMYK, Coated FOGRA39)`: PNG non ha il CMYK e
        # `tobytes("png")` alza ValueError. Senza conversione, 583 immagini
        # mascherate tornerebbero sul rettangolo nero.
        document, xref = _document_with_a_hand_attached_mask(
            Image.new("CMYK", (40, 32), (10, 200, 30, 5)), (40, 32)
        )
        try:
            extracted = extract_stored_raster(document, xref)
            self.assertIsNotNone(extracted)
            assert extracted is not None
            payload, extension, method = extracted
            self.assertEqual(extension, "png")
            self.assertEqual(method, METHOD_STORED_WITH_MASK)
            self.assertIn("A", Image.open(io.BytesIO(payload)).getbands())
        finally:
            document.close()

    def test_a_mask_of_another_size_is_scaled_not_discarded(self) -> None:
        # Su BiD 4 immagini mascherate su 5 hanno la maschera a un'altra
        # risoluzione: e' legale, il PDF la campiona sull'area. `fitz.Pixmap`
        # alza `FzErrorArgument`, che NON deriva da RuntimeError ne' ValueError.
        document, xref = _document_with_a_hand_attached_mask(
            Image.new("RGB", (40, 32), (200, 10, 10)), (20, 16)
        )
        try:
            extracted = extract_stored_raster(document, xref)
            self.assertIsNotNone(extracted)
            assert extracted is not None
            payload, extension, method = extracted
            self.assertEqual(extension, "png")
            self.assertEqual(method, METHOD_STORED_WITH_MASK)
            image = Image.open(io.BytesIO(payload))
            self.assertEqual(image.size, (40, 32))
            self.assertIn("A", image.getbands())
        finally:
            document.close()


class NoStoredResourceTest(unittest.TestCase):
    def test_xref_zero_means_there_is_nothing_to_extract(self) -> None:
        # I gradienti e le maschere morbide che `get_image_info` riporta come
        # immagini: il renderer li sintetizza, la sorgente non li conserva.
        with fitz.open() as document:
            self.assertIsNone(extract_stored_raster(document, 0))

    def test_a_negative_xref_is_treated_the_same(self) -> None:
        with fitz.open() as document:
            self.assertIsNone(extract_stored_raster(document, -1))

    def test_a_non_integer_xref_is_refused(self) -> None:
        with fitz.open() as document, self.assertRaises(ValueError):
            extract_stored_raster(document, "4")  # type: ignore[arg-type]


class ObservationIndexTest(unittest.TestCase):
    def test_the_index_comes_from_the_observation_id(self) -> None:
        with _document_with_a_masked_image() as document:
            self.assertGreater(
                stored_resource_xref(document[0], _occurrence(0)), 0
            )

    def test_an_index_past_the_page_is_refused(self) -> None:
        with _document_with_a_masked_image() as document, self.assertRaises(ValueError):
            stored_resource_xref(document[0], _occurrence(99))

    def test_an_unparseable_observation_id_is_refused(self) -> None:
        primitive = ImageOccurrencePrimitive(
            primitive_id="primitive:image:x",
            bbox=(0.0, 0.0, 10.0, 10.0),
            source_observation_id="image:senza-indice",
        )
        with _document_with_a_masked_image() as document, self.assertRaises(ValueError):
            stored_resource_xref(document[0], primitive)


if __name__ == "__main__":
    unittest.main()
