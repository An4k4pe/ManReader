"""La regola delle fasce. `Criterio_TitoliPerFascia_v2.md` §1."""

from __future__ import annotations

import unittest

from document_heading_band_measurements import SizeMassMeasurements
from document_heading_band_policy import (
    HEADING_TOLERANCE,
    MASS_SHARE,
    MAX_LEVEL,
    group_into_bands,
    heading_bands,
)


def _misura(**per_dimensione: tuple[int, int, int, int]) -> SizeMassMeasurements:
    """`dimensione="caratteri,pagine,parole,testi"`, con le pagine come conteggio."""

    caratteri, pagine, parole, testi = {}, {}, {}, {}
    for chiave, (car, pag, par, tes) in per_dimensione.items():
        size = float(chiave.lstrip("s").replace("_", "."))
        caratteri[size] = car
        pagine[size] = frozenset(range(pag))
        parole[size] = par
        testi[size] = tes
    return SizeMassMeasurements(
        characters=caratteri, page_indices=pagine, word_count=parole,
        text_count=testi, sample_texts={},
    )


def _fasce(misura: SizeMassMeasurements, righe: dict):
    """`heading_bands`, che ora ricava il tetto dalla massa da se'."""

    return heading_bands(misura, righe)


class CorpoTest(unittest.TestCase):
    def test_il_corpo_e_la_massa_non_la_coda(self) -> None:
        # E' la ragione per cui il criterio esiste: su Dag `min(prose_sizes)` era
        # 2,8 pt, una dimensione che porta lo 0,15% del testo.
        misura = _misura(s9_0=(1_000_000, 300, 9000, 10000), s2_8=(2000, 5, 40, 50))
        bande = _fasce(misura, {9.0: 55.0, 2.8: 55.0})
        assert bande.body is not None
        self.assertEqual(bande.body.label, "9.0")
        self.assertNotIn(2.8, bande.size_levels)

    def test_senza_niente_da_misurare_tace(self) -> None:
        bande = heading_bands(_misura(), {})
        self.assertIsNone(bande.body)
        self.assertEqual(bande.size_levels, {})
        self.assertEqual(bande.prose_anchor, frozenset())


class FasceTest(unittest.TestCase):
    def test_l_accorpamento_e_relativo_non_assoluto(self) -> None:
        # Quattro punti separano 9 da 13 e non separano 90 da 94: il rango
        # tipografico si legge in proporzione.
        misura = _misura(s94_0=(10, 3, 9, 10), s90_0=(10, 3, 9, 10))
        fasce = group_into_bands(misura, {}, HEADING_TOLERANCE)
        self.assertEqual(len(fasce), 1)
        self.assertEqual(fasce[0].label, "90.0-94.0")

    def test_sopra_esclude_e_non_accorpa(self) -> None:
        misura = _misura(s30_0=(10, 3, 9, 10), s10_0=(10, 3, 9, 10))
        fasce = group_into_bands(misura, {}, HEADING_TOLERANCE, above=10.0)
        self.assertEqual([f.label for f in fasce], ["30.0"])

    def test_la_mediana_di_riga_e_pesata_sui_testi(self) -> None:
        # Una dimensione con quattro righe e una con quattromila non possono
        # pesare uguale: la fascia direbbe la forma della piu' rara.
        misura = _misura(s20_0=(10, 3, 9, 1), s19_5=(10, 3, 9, 999))
        fascia = group_into_bands(misura, {20.0: 90.0, 19.5: 10.0}, HEADING_TOLERANCE)[0]
        self.assertEqual(fascia.label, "19.5-20.0")
        self.assertEqual(fascia.median_line_length, 10.0)


class FiltriTest(unittest.TestCase):
    """I quattro filtri sono congiuntivi e ognuno toglie una cosa diversa."""

    CORPO = {"s10_0": (1_000_000, 300, 9000, 10000)}
    RIGHE = {10.0: 60.0}

    def _livelli(self, **extra: tuple[int, int, int, int]) -> list[str]:
        misura = _misura(**{**self.CORPO, **extra})
        righe = dict(self.RIGHE)
        for chiave in extra:
            righe.setdefault(float(chiave.lstrip("s").replace("_", ".")), 12.0)
        return [b.label for b in _fasce(misura, righe).candidates]

    def test_1_una_fascia_attaccata_al_corpo_non_passa(self) -> None:
        # Senza la guardia, a tolleranza larga Fab dava `H1 = 11-12 pt su 282
        # pagine`: il corpo etichettato come titolo.
        self.assertEqual(self._livelli(s10_5=(50_000, 200, 900, 1000)), [])

    def test_2_la_decorazione_non_passa(self) -> None:
        # `'y'` a 172 pt su Fab, `'2'`/`'3'`/`'4'` a 292 pt su BiD.
        self.assertEqual(self._livelli(s172_0=(300, 40, 0, 300)), [])

    def test_3_la_prosa_piu_grande_non_passa(self) -> None:
        # Il filtro 2 non la vede: e' fatta di parole. La riga lunga la tradisce.
        misura = _misura(**self.CORPO, s13_0=(90_000, 300, 900, 1000))
        self.assertEqual(
            [b.label for b in _fasce(misura, {10.0: 60.0, 13.0: 58.0}).candidates], []
        )

    def test_4_una_fascia_su_due_pagine_non_e_un_rango(self) -> None:
        self.assertEqual(self._livelli(s30_0=(300, 2, 290, 300)), [])

    def test_una_fascia_che_passa_tutti_e_quattro_diventa_titolo(self) -> None:
        self.assertEqual(self._livelli(s30_0=(3000, 40, 2900, 3000)), ["30.0"])


class LivelliTest(unittest.TestCase):
    CORPO = {"s10_0": (1_000_000, 300, 9000, 10000)}

    def _misura_quattro(self) -> SizeMassMeasurements:
        return _misura(
            **self.CORPO,
            s60_0=(3000, 40, 2900, 3000), s40_0=(3000, 40, 2900, 3000),
            s30_0=(3000, 40, 2900, 3000), s20_0=(3000, 40, 2900, 3000),
        )

    RIGHE = {10.0: 60.0, 60.0: 12.0, 40.0: 12.0, 30.0: 12.0, 20.0: 12.0}

    def test_la_quarta_fascia_ACCORPA_su_h3_e_non_torna_prosa(self) -> None:
        # E' il difetto A del §0 della v2. La v1 scartava tutto oltre la terza, e
        # il costo misurato era dal 74% al 97% dei titoli di ogni manuale.
        bande = _fasce(self._misura_quattro(), self.RIGHE)
        self.assertEqual(len(bande.candidates), 4)
        livelli = bande.size_levels
        self.assertEqual(livelli[60.0], 1)
        self.assertEqual(livelli[40.0], 2)
        self.assertEqual(livelli[30.0], 3)
        self.assertEqual(livelli[20.0], MAX_LEVEL)
        self.assertEqual(bande.bands_by_level[3][1].label, "20.0")

    def test_nessun_livello_supera_il_tetto_di_markdown(self) -> None:
        livelli = _fasce(self._misura_quattro(), self.RIGHE).size_levels
        self.assertLessEqual(max(livelli.values()), MAX_LEVEL)

    def test_le_tre_piu_grandi_prendono_i_ranghi_distinti(self) -> None:
        # Selezionare per uso trascinerebbe la scelta verso la prosa, perche' la
        # frequenza cresce avvicinandosi al corpo. Qui `20.0` e' la piu' usata di
        # gran lunga e resta comunque l'ultima.
        misura = _misura(
            **self.CORPO,
            s60_0=(300, 40, 290, 300), s40_0=(400, 40, 390, 400),
            # 1,5% del corpo: sotto la soglia della massa, quindi ancora un
            # titolo -- ma di gran lunga il piu' usato fra i titoli.
            s30_0=(500, 40, 490, 500), s20_0=(15_000, 300, 14_000, 15_000),
        )
        per_livello = _fasce(misura, self.RIGHE).bands_by_level
        self.assertEqual(per_livello[1][0].label, "60.0")
        self.assertEqual(per_livello[2][0].label, "40.0")
        self.assertEqual([b.label for b in per_livello[3]], ["30.0", "20.0"])

    def test_ogni_dimensione_della_fascia_ha_LO_STESSO_livello(self) -> None:
        # Il veto D: su Dag `28,0` era h1 e `27,9` era h2 -- due livelli per
        # quello che sulla pagina e' un titolo solo.
        misura = _misura(
            **self.CORPO,
            s28_0=(2000, 40, 1900, 2000), s27_9=(2000, 40, 1900, 2000),
        )
        bande = _fasce(misura, {10.0: 60.0, 28.0: 12.0, 27.9: 12.0})
        self.assertEqual([b.label for b in bande.candidates], ["27.9-28.0"])
        self.assertEqual(bande.size_levels[28.0], bande.size_levels[27.9])


class TettoDallaMassaTest(unittest.TestCase):
    """Il punto fisso: cio' che e' prosa non e' mai un titolo, e la prosa si
    riconosce dalla **massa**. `Criterio_TettoDallaMassa_v1.md` §1."""

    def test_una_dimensione_con_massa_confrontabile_e_prosa(self) -> None:
        # E' il caso di Fab: 12,0 pt porta il 2,17% del manuale contro l'87% del
        # corpo -- il 2,5% del corpo -- ed e' una citazione d'apertura, non un
        # titolo. Con le mediane di riga restava fuori dalla prosa e passava.
        misura = _misura(
            s10_0=(1_000_000, 300, 9000, 10000),
            s12_0=(25_000, 312, 24_000, 25_000),      # 2,5% del corpo
            s30_0=(500, 40, 490, 500),                # 0,05% del corpo
        )
        bande = _fasce(misura, {10.0: 60.0, 12.0: 18.0, 30.0: 12.0})
        self.assertEqual(bande.ceiling, 12.0)
        self.assertEqual([b.label for b in bande.candidates], ["30.0"])
        self.assertNotIn(12.0, bande.size_levels)

    def test_una_dimensione_rara_e_un_titolo(self) -> None:
        # I titoli sono rari, ed e' cio' che li rende titoli.
        misura = _misura(
            s10_0=(1_000_000, 300, 9000, 10000),
            s30_0=(500, 40, 490, 500),
        )
        bande = _fasce(misura, {10.0: 60.0, 30.0: 12.0})
        self.assertEqual(bande.ceiling, 10.0)
        self.assertEqual([b.label for b in bande.candidates], ["30.0"])

    def test_nessuna_dimensione_promossa_sta_al_tetto_o_sotto(self) -> None:
        misura = _misura(
            s10_0=(1_000_000, 300, 9000, 10000),
            s12_0=(25_000, 312, 24_000, 25_000),
            s13_0=(500, 40, 490, 500), s30_0=(500, 40, 490, 500),
        )
        bande = _fasce(misura, {10.0: 60.0, 12.0: 18.0, 13.0: 12.0, 30.0: 12.0})
        assert bande.ceiling is not None
        for dimensione in bande.size_levels:
            self.assertGreater(dimensione, bande.ceiling)

    def test_il_corpo_entra_nel_tetto_quando_supera_la_prosa(self) -> None:
        # Su BoB la fascia di corpo arriva a 10,2: prendere la sola prosa
        # lascerebbe due decimi di corpo sopra il tetto.
        misura = _misura(
            s10_2=(500_000, 300, 4000, 5000), s10_0=(500_000, 300, 4000, 5000),
            s30_0=(500, 40, 490, 500),
        )
        bande = _fasce(misura, {10.2: 60.0, 10.0: 60.0, 30.0: 12.0})
        self.assertEqual(bande.body.label, "10.0-10.2")
        self.assertEqual(bande.ceiling, 10.2)

    def test_la_soglia_e_quella_dichiarata(self) -> None:
        # Misurato: da 1,5% a 2,0% gli otto manuali danno lo stesso tetto.
        self.assertEqual(MASS_SHARE, 0.018)

    def test_senza_testo_misurato_il_meccanismo_tace(self) -> None:
        bande = heading_bands(_misura(), {})
        self.assertIsNone(bande.ceiling)
        self.assertEqual(bande.size_levels, {})


if __name__ == "__main__":
    unittest.main()
