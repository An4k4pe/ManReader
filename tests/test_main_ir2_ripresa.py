"""La ripresa del main IR 2: stato, pagine gia' fatte, indice asset riusabile."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from ir2_model import DocumentIR2, IR2Provenance, NodeIR2, PageIR2  # noqa: E402
from ir2_serialization import document_ir2_to_dict  # noqa: E402
from main_ir2 import (  # noqa: E402
    _asset_da_disco,
    _impronta_del_codice,
    _pagina_su_disco,
    _stato_atteso,
)

_CAMPI = [
    "digest", "destinazione", "cartella", "nome_file", "pagine", "occorrenze",
    "prima_pagina", "estensione_minore_pt", "nota_nel_corpo",
    "risorsa_memorizzata", "metodo",
]


def _pagina_serializzata(directory: Path, *, con_esclusi: bool = True) -> None:
    """Scrive su disco cio' che una corsa precedente avrebbe lasciato."""

    nodo = NodeIR2(
        node_id="page:0001:text:b0000:l0000:s0000",
        order=0,
        kind="text.paragraph",
        primitive_ids=("primitive:text:text:b0000:l0000:s0000",),
        page_ids=("page:0001",),
        text="Un paragrafo qualunque.",
    )
    documento = DocumentIR2(
        provenance=IR2Provenance(
            source_id="s", generation_id="g", producer_names=("uno",)
        ),
        pages=(PageIR2(page_id="page:0001", nodes=(nodo,)),),
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "document_ir2.json").write_text(
        json.dumps(document_ir2_to_dict(documento)), encoding="utf-8"
    )
    if con_esclusi:
        (directory / "excluded_ir2.json").write_text(
            json.dumps(["page:0001:text:b0000:l0000:s0000"]), encoding="utf-8"
        )


def _indice(percorso: Path, righe: list[dict[str, str]]) -> None:
    with percorso.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CAMPI)
        writer.writeheader()
        writer.writerows(righe)


class StatoTest(unittest.TestCase):
    def test_lo_stato_verifica_la_sorgente_senza_copiarla(self) -> None:
        # `AGENTS.MD` §Sorgente vuole la sorgente verificata prima del resume.
        # Verificarla basta: duplicare duecento megabyte no.
        with tempfile.TemporaryDirectory() as temporanea:
            pdf = Path(temporanea) / "finto.pdf"
            pdf.write_bytes(b"%PDF-1.4 contenuto")
            sorgente = _stato_atteso(pdf, 20, False)["sorgente"]
            self.assertEqual(sorgente["original_name"], "finto.pdf")
            self.assertEqual(sorgente["size_bytes"], len(b"%PDF-1.4 contenuto"))
            self.assertEqual(len(str(sorgente["sha256"])), 64)
            self.assertFalse((Path(temporanea) / "source").exists())

    def test_le_opzioni_entrano_nello_stato(self) -> None:
        # Riprendere con una finestra diversa unirebbe pagine misurate su ambiti
        # diversi: e' una fusione silenziosa, e lo stato deve poterla vedere.
        with tempfile.TemporaryDirectory() as temporanea:
            pdf = Path(temporanea) / "finto.pdf"
            pdf.write_bytes(b"x")
            self.assertNotEqual(
                _stato_atteso(pdf, 20, False)["opzioni"],
                _stato_atteso(pdf, 30, False)["opzioni"],
            )
            self.assertNotEqual(
                _stato_atteso(pdf, 20, False)["opzioni"],
                _stato_atteso(pdf, 20, True)["opzioni"],
            )

    def test_lo_stesso_contenuto_da_lo_stesso_stato(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            uno = Path(temporanea) / "a.pdf"
            uno.write_bytes(b"identico")
            due = Path(temporanea) / "a2.pdf"
            due.write_bytes(b"identico")
            self.assertEqual(
                _stato_atteso(uno, 20, False)["sorgente"]["sha256"],
                _stato_atteso(due, 20, False)["sorgente"]["sha256"],
            )


class ImprontaDelCodiceTest(unittest.TestCase):
    """L'impronta chiude la trappola che la prima versione dello stato aveva:
    correggere un producer e riprendere sulle pagine calcolate da quello vecchio."""

    def test_e_stabile_a_parita_di_codice(self) -> None:
        self.assertEqual(_impronta_del_codice(), _impronta_del_codice())

    def test_e_un_digest_sha256(self) -> None:
        self.assertEqual(len(_impronta_del_codice()), 64)
        int(_impronta_del_codice(), 16)

    def test_entra_nello_stato(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            pdf = Path(temporanea) / "finto.pdf"
            pdf.write_bytes(b"x")
            stato = _stato_atteso(pdf, 20, False)
            self.assertEqual(
                stato["codice"]["sha256"], _impronta_del_codice()
            )

    def test_cambiare_un_modulo_del_progetto_la_cambia(self) -> None:
        # La prova che conta: se il codice cambia, l'impronta se ne accorge.
        # Si tocca un modulo gia' caricato e lo si rimette com'era.
        modulo = PROJECT_ROOT / "document_asset_policy.py"
        originale = modulo.read_bytes()
        prima = _impronta_del_codice()
        try:
            modulo.write_bytes(originale + b"\n# tocco per la prova\n")
            self.assertNotEqual(prima, _impronta_del_codice())
        finally:
            modulo.write_bytes(originale)
        self.assertEqual(prima, _impronta_del_codice())


class PaginaSuDiscoTest(unittest.TestCase):
    def test_una_pagina_gia_resa_si_rilegge(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            scratch = Path(temporanea)
            _pagina_serializzata(scratch / "00007")
            pagina = _pagina_su_disco(scratch, 7)
            self.assertIsNotNone(pagina)
            assert pagina is not None
            self.assertEqual(pagina.page_index, 7)
            self.assertEqual(pagina.page_id, "page:0001")
            self.assertEqual(len(pagina.excluded_node_ids), 1)

    def test_una_pagina_mai_resa_da_None(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            self.assertIsNone(_pagina_su_disco(Path(temporanea), 7))

    def test_un_artefatto_illeggibile_si_rifa(self) -> None:
        # Meglio ricalcolare che fidarsi di un file mezzo scritto.
        with tempfile.TemporaryDirectory() as temporanea:
            scratch = Path(temporanea)
            (scratch / "00007").mkdir()
            (scratch / "00007" / "document_ir2.json").write_text("{ non json")
            self.assertIsNone(_pagina_su_disco(scratch, 7))

    def test_senza_esclusi_la_pagina_vale_lo_stesso(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            scratch = Path(temporanea)
            _pagina_serializzata(scratch / "00003", con_esclusi=False)
            pagina = _pagina_su_disco(scratch, 3)
            self.assertIsNotNone(pagina)
            assert pagina is not None
            self.assertEqual(pagina.excluded_node_ids, frozenset())


class AssetDaDiscoTest(unittest.TestCase):
    def _riga(self, **override: str) -> dict[str, str]:
        riga = dict.fromkeys(_CAMPI, "")
        riga.update(
            digest="md5:a", destinazione="content", cartella="images",
            nome_file="md5_a.png", nota_nel_corpo="si",
        )
        riga.update(override)
        return riga

    def test_un_indice_completo_si_riusa(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            out = Path(temporanea)
            (out / "images").mkdir()
            (out / "images" / "md5_a.png").write_bytes(b"x")
            _indice(out / "asset_index.csv", [self._riga()])
            righe, note = _asset_da_disco(out / "asset_index.csv", out)
            self.assertIsNotNone(righe)
            self.assertEqual(note, frozenset({"md5:a"}))

    def test_un_indice_che_nomina_un_file_assente_non_si_riusa(self) -> None:
        # Riprendere con mezza cartella darebbe note che puntano nel vuoto:
        # peggio che rifare l'estrazione, che e' lenta ma non fragile.
        with tempfile.TemporaryDirectory() as temporanea:
            out = Path(temporanea)
            _indice(out / "asset_index.csv", [self._riga()])
            righe, note = _asset_da_disco(out / "asset_index.csv", out)
            self.assertIsNone(righe)
            self.assertIsNone(note)

    def test_una_riga_senza_file_non_invalida_l_indice(self) -> None:
        # I gradienti e le strisce sottili stanno nell'indice **senza** file:
        # e' la copertura di AGENTS.MD §Coverage, non un indice rotto.
        with tempfile.TemporaryDirectory() as temporanea:
            out = Path(temporanea)
            _indice(
                out / "asset_index.csv",
                [self._riga(
                    digest="md5:g", destinazione="no_stored_resource",
                    cartella="", nome_file="", nota_nel_corpo="no",
                )],
            )
            righe, _ = _asset_da_disco(out / "asset_index.csv", out)
            self.assertIsNotNone(righe)

    def test_un_indice_assente_o_vuoto_da_None(self) -> None:
        with tempfile.TemporaryDirectory() as temporanea:
            out = Path(temporanea)
            self.assertEqual(_asset_da_disco(out / "manca.csv", out), (None, None))
            _indice(out / "vuoto.csv", [])
            self.assertEqual(_asset_da_disco(out / "vuoto.csv", out), (None, None))


if __name__ == "__main__":
    unittest.main()
