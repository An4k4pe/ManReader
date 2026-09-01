import json
import unittest

from capture_model import (
    BackendAnnotationObservation,
    BackendDrawingObservation,
    BackendImageObservation,
    BackendLinkObservation,
    BackendPageCapture,
    BackendTextObservation,
    CaptureError,
    DrawingCommand,
)
from capture_serialization import (
    CAPTURE_SERIALIZATION_SCHEMA,
    backend_page_capture_from_dict,
    backend_page_capture_to_dict,
)
from geometry_model import PageGeometry

GEOMETRIA = PageGeometry(
    width=595.0, height=842.0, unit="pt", coordinate_system="top_left_y_down"
)


def _cattura_completa() -> BackendPageCapture:
    """Una cattura con **tutti** i tipi di osservazione, campi opzionali inclusi."""

    return BackendPageCapture(
        schema_version="1",
        capture_id="capture:1",
        backend_name="pymupdf",
        backend_version="1.24",
        source_id="source:1",
        page_id="page:0007",
        page_index=6,
        page_geometry=GEOMETRIA,
        source_rotation_degrees=90,
        crop_box=(0.0, 0.0, 595.0, 842.0),
        media_box=(0.0, 0.0, 595.0, 842.0),
        text_observations=(
            BackendTextObservation(
                observation_id="text:b0000:l0000:s0000",
                bbox=(10.0, 20.0, 100.0, 32.0),
                text="Un testo con àccenti e \t tabulazione",
                font_name="Serif",
                font_size=11.5,
                font_flags=4,
                color=(0.1, 0.2, 0.3, 1.0),
                direction=(1.0, 0.0),
            ),
            BackendTextObservation(
                observation_id="text:b0000:l0001:s0000",
                bbox=(10.0, 40.0, 100.0, 52.0),
                text="senza opzionali",
            ),
        ),
        image_observations=(
            BackendImageObservation(
                observation_id="image:i0000",
                bbox=(0.0, 0.0, 200.0, 300.0),
                resource_ref="xref:12",
                content_digest="md5:abc",
                pixel_width=400,
                pixel_height=600,
                placement_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
                has_alpha=True,
                has_stored_resource=True,
            ),
            BackendImageObservation(
                observation_id="image:i0001",
                bbox=(5.0, 5.0, 15.0, 15.0),
                has_stored_resource=False,
            ),
        ),
        drawing_observations=(
            BackendDrawingObservation(
                observation_id="drawing:d0000",
                bbox=(0.0, 0.0, 50.0, 50.0),
                commands=(
                    DrawingCommand(
                        kind="l",
                        points=((0.0, 0.0), (50.0, 50.0)),
                        bbox=(0.0, 0.0, 50.0, 50.0),
                        orientation=1,
                    ),
                    DrawingCommand(kind="re"),
                ),
                stroke_width=0.5,
                stroke_color=(0.0, 0.0, 0.0, 1.0),
                fill_color=(1.0, 1.0, 1.0, 1.0),
                stroke_opacity=0.9,
                fill_opacity=0.8,
                is_closed=True,
            ),
        ),
        link_observations=(
            BackendLinkObservation(
                observation_id="link:l0000",
                bbox=(1.0, 2.0, 3.0, 4.0),
                target_kind="uri",
                uri="https://example.invalid",
            ),
        ),
        annotation_observations=(
            BackendAnnotationObservation(
                observation_id="annot:a0000",
                bbox=(1.0, 2.0, 3.0, 4.0),
                annotation_kind="Text",
                content="una nota",
            ),
        ),
        backend_order_kind="extraction",
        backend_order=("text:b0000:l0000:s0000", "image:i0000"),
        errors=(
            CaptureError(
                code="parziale", message="qualcosa", observation_id="image:i0001",
                recoverable=False,
            ),
        ),
    )


class RoundTripTest(unittest.TestCase):
    def test_una_cattura_completa_torna_identica(self) -> None:
        cattura = _cattura_completa()
        ritorno = backend_page_capture_from_dict(
            backend_page_capture_to_dict(cattura)
        )
        self.assertEqual(ritorno, cattura)

    def test_passa_anche_da_json_vero(self) -> None:
        # Il giro che conta e' su disco: `json.dumps` degrada le tuple a liste,
        # ed e' li' che una ricostruzione ingenua si rompe.
        cattura = _cattura_completa()
        testo = json.dumps(backend_page_capture_to_dict(cattura), ensure_ascii=False)
        self.assertEqual(
            backend_page_capture_from_dict(json.loads(testo)), cattura
        )

    def test_le_tuple_tornano_tuple_e_non_liste(self) -> None:
        ritorno = backend_page_capture_from_dict(
            json.loads(json.dumps(backend_page_capture_to_dict(_cattura_completa())))
        )
        self.assertIsInstance(ritorno.text_observations, tuple)
        self.assertIsInstance(ritorno.text_observations[0].bbox, tuple)
        self.assertIsInstance(ritorno.drawing_observations[0].commands, tuple)
        self.assertIsInstance(ritorno.drawing_observations[0].commands[0].points, tuple)
        self.assertIsInstance(ritorno.backend_order, tuple)

    def test_una_cattura_minima_torna_identica(self) -> None:
        minima = BackendPageCapture(
            schema_version="1", capture_id="c", backend_name="b",
            backend_version="1", source_id="s", page_id="page:0001",
            page_index=0, page_geometry=GEOMETRIA,
        )
        self.assertEqual(
            backend_page_capture_from_dict(backend_page_capture_to_dict(minima)),
            minima,
        )

    def test_il_fatto_sulla_risorsa_memorizzata_sopravvive(self) -> None:
        # E' il campo aggiunto per distinguere un'immagine da un raster che il
        # renderer sintetizza: se non attraversasse, a valle si tornerebbe ciechi.
        ritorno = backend_page_capture_from_dict(
            backend_page_capture_to_dict(_cattura_completa())
        )
        self.assertIs(ritorno.image_observations[0].has_stored_resource, True)
        self.assertIs(ritorno.image_observations[1].has_stored_resource, False)


class RifiutiTest(unittest.TestCase):
    def test_una_chiave_sconosciuta_e_un_errore(self) -> None:
        # Un artefatto scritto da una versione futura non si legge a meta'.
        dato = backend_page_capture_to_dict(_cattura_completa())
        dato["campo_futuro"] = 1
        with self.assertRaisesRegex(ValueError, "unexpected keys"):
            backend_page_capture_from_dict(dato)

    def test_una_chiave_sconosciuta_dentro_un_osservazione(self) -> None:
        dato = backend_page_capture_to_dict(_cattura_completa())
        osservazioni = dato["text_observations"]
        assert isinstance(osservazioni, list)
        osservazioni[0]["novita"] = True
        with self.assertRaisesRegex(ValueError, "unexpected keys"):
            backend_page_capture_from_dict(dato)

    def test_uno_schema_di_serializzazione_diverso_si_rifiuta(self) -> None:
        dato = backend_page_capture_to_dict(_cattura_completa())
        dato["serialization_schema"] = "capture-serialization-99"
        with self.assertRaisesRegex(ValueError, "unsupported serialization schema"):
            backend_page_capture_from_dict(dato)

    def test_lo_schema_dichiarato_e_quello_scritto(self) -> None:
        dato = backend_page_capture_to_dict(_cattura_completa())
        self.assertEqual(dato["serialization_schema"], CAPTURE_SERIALIZATION_SCHEMA)

    def test_un_bbox_di_lunghezza_sbagliata_si_rifiuta(self) -> None:
        dato = backend_page_capture_to_dict(_cattura_completa())
        osservazioni = dato["text_observations"]
        assert isinstance(osservazioni, list)
        osservazioni[0]["bbox"] = [1.0, 2.0, 3.0]
        with self.assertRaisesRegex(ValueError, "four numbers"):
            backend_page_capture_from_dict(dato)

    def test_un_dato_che_non_e_un_dizionario_si_rifiuta(self) -> None:
        with self.assertRaises(ValueError):
            backend_page_capture_from_dict([])  # type: ignore[arg-type]

    def test_una_cattura_che_non_e_una_cattura_si_rifiuta(self) -> None:
        with self.assertRaises(ValueError):
            backend_page_capture_to_dict({})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
