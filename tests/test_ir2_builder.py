import unittest

from ir2_builder import (
    AssetNoteInput,
    body_font,
    breaks_paragraph,
    build_page_ir2,
    group_source_lines,
    join_lines,
)
from primitive_model import TextPrimitive

PAGE = "page:0099"


def _span(block: int, line: int, span: int, text: str, y: float = 0.0, x: float = 0.0):
    observation = f"text:b{block:04d}:l{line:04d}:s{span:04d}"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(x, y, x + 10.0, y + 10.0),
        text=text,
        source_observation_id=observation,
    )


class GroupSourceLinesTest(unittest.TestCase):
    def test_concatenates_spans_without_adding_a_separator(self) -> None:
        # Il caso misurato su DB p.99: gli span portano gia' la loro spaziatura.
        spans = [_span(5, 0, 0, "a "), _span(5, 0, 1, "PERSUADERE"), _span(5, 0, 2, ".")]
        lines = group_source_lines(spans)
        self.assertEqual([line.text for line in lines], ["a PERSUADERE."])

    def test_orders_spans_by_span_index_not_by_arrival(self) -> None:
        spans = [_span(7, 2, 2, " 8"), _span(7, 2, 0, "PF"), _span(7, 2, 1, ":")]
        self.assertEqual([line.text for line in group_source_lines(spans)], ["PF: 8"])

    def test_splits_on_a_new_line_index(self) -> None:
        spans = [_span(3, 0, 0, "prima"), _span(3, 1, 0, "seconda")]
        self.assertEqual(len(group_source_lines(spans)), 2)

    def test_an_unreadable_observation_id_becomes_its_own_line(self) -> None:
        odd = TextPrimitive(
            primitive_id="primitive:text:weird",
            bbox=(0.0, 0.0, 1.0, 1.0),
            text="x",
            source_observation_id="weird",
        )
        self.assertEqual(len(group_source_lines([_span(1, 0, 0, "a"), odd])), 2)


BODY = "PTSans-Narrow"


def _line(block: int, line: int, text: str, font: str = BODY):
    """Una riga di sorgente sola, col font del suo primo carattere."""

    observation = f"text:b{block:04d}:l{line:04d}:s0000"
    primitive = TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(0.0, 0.0, 10.0, 10.0),
        text=text,
        source_observation_id=observation,
        font_name=font,
    )
    return group_source_lines([primitive])[0]


def _font_span(index: int, text: str, font: str):
    observation = f"text:b0001:l0000:s{index:04d}"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(0.0, 0.0, 10.0, 10.0),
        text=text,
        source_observation_id=observation,
        font_name=font,
    )


def _font_line(block: int, line: int, text: str, y: float = 0.0, font: str = BODY):
    """Uno span con un font, per i test che dipendono dal font del corpo."""

    observation = f"text:b{block:04d}:l{line:04d}:s0000"
    return TextPrimitive(
        primitive_id=f"primitive:text:{observation}",
        bbox=(0.0, y, 10.0, y + 10.0),
        text=text,
        source_observation_id=observation,
        font_name=font,
    )


class BodyFontTest(unittest.TestCase):
    def test_counts_characters_and_not_primitives(self) -> None:
        # Il caso misurato su DB p.99: tante righe corte in grassetto contro
        # poche righe lunghe di prosa. Contando le primitive vince il grassetto.
        spans = [_font_span(i, "PF: 8", "Hideout-Bold") for i in range(4)]
        spans.append(_font_span(4, "x" * 200, "Hideout-Regular"))
        self.assertEqual(body_font(spans), "Hideout-Regular")

    def test_no_font_at_all_gives_none(self) -> None:
        self.assertIsNone(body_font([_span(1, 0, 0, "x")]))


class BreaksParagraphTest(unittest.TestCase):
    """`Criterio_RotturaParagrafo_v2.md` §1: blocco, con veto lessicale."""

    def test_inside_one_block_it_never_breaks(self) -> None:
        # Il difetto misurato su DIE p.380: la regola vecchia spezzava qui,
        # perche' `GM` e' maiuscolo. Sulla pagina e' un paragrafo solo.
        previous = _line(3, 3, "qualsiasi altro personaggio richiedera' parecchio impegno")
        following = _line(3, 4, "GM che interpreta la versione da Classe")
        self.assertFalse(breaks_paragraph(previous, following, BODY))

    def test_a_new_block_breaks(self) -> None:
        self.assertTrue(breaks_paragraph(_line(6, 0, "GUERRIERO"), _line(7, 0, "PF: 8"), BODY))

    def test_a_lowercase_body_start_vetoes_the_break(self) -> None:
        # Il salto di colonna misurato su SV p.181: due blocchi, un periodo solo.
        previous = _line(4, 9, "“Ci penso io!” dice Marta. “Flashback a")
        following = _line(5, 0, "quando stavo lavorando sui motori")
        self.assertFalse(breaks_paragraph(previous, following, BODY))

    def test_a_lowercase_glyph_of_another_font_does_not_veto(self) -> None:
        # Fab p.248: il pallino e' la lettera `w` in Wingdings, non una minuscola.
        previous = _line(4, 2, "aggiungi a ogni luogo un dettaglio")
        following = _line(6, 0, "w Gestisci le informazioni.", font="Wingdings-Regular")
        self.assertTrue(breaks_paragraph(previous, following, BODY))

    def test_a_sentence_ending_mid_block_does_not_break(self) -> None:
        # La clausola caduta con la regola lessicale: un paragrafo contiene
        # piu' frasi, e il punto a meta' blocco non lo chiude.
        previous = _line(9, 1, "Il Master ha commesso il crimine.")
        following = _line(9, 2, "E' possibile, tuttavia, che alcune punizioni")
        self.assertFalse(breaks_paragraph(previous, following, BODY))

    def test_does_not_break_on_an_empty_next_line(self) -> None:
        self.assertFalse(breaks_paragraph(_line(1, 0, "qualcosa."), _line(2, 0, ""), BODY))

    def test_without_a_body_font_the_veto_never_applies(self) -> None:
        previous = _line(1, 0, "prima", font="")
        following = _line(2, 0, "seconda", font="")
        self.assertTrue(breaks_paragraph(previous, following, None))


class JoinLinesTest(unittest.TestCase):
    def test_rejoins_a_hyphenated_word(self) -> None:
        self.assertEqual(join_lines("sono dimez-", "zati (per eccesso)"), "sono dimezzati (per eccesso)")

    def test_joins_with_a_single_space_when_there_is_no_hyphen(self) -> None:
        self.assertEqual(join_lines("gli scheletri non", "contano"), "gli scheletri non contano")

    def test_does_not_rejoin_when_the_next_starts_uppercase(self) -> None:
        # La guardia della regex: lettera prima, minuscola dopo.
        self.assertEqual(join_lines("nord-", "Ovest"), "nord- Ovest")


class BuildPageIR2Test(unittest.TestCase):
    def test_a_hanging_indent_box_comes_out_as_one_paragraph(self) -> None:
        """Il costo dichiarato di `Criterio_RotturaParagrafo_v2.md` §8.

        Il box Non-Mostri di DB p.99: dentro di esso i blocchi di sorgente sono
        **sfalsati di una riga** rispetto alle voci -- ``b0003`` porta la fine
        della prima voce e l'inizio della seconda -- quindi il confine di blocco
        non cade mai dove finisce una voce, e il veto lessicale unisce il resto.
        Le tre voci escono come un paragrafo solo.

        Questo test asseriva l'uscita a tre voci della regola lessicale
        precedente. **Non e' stato adattato al codice**: la regola nuova e' stata
        misurata contro le etichette a vista dell'utente sulle 46 righe di quella
        pagina e ne prende 40 giunzioni su 43 contro le 33 della vecchia, il cui
        prezzo erano dieci rotture in piu' che spezzavano ogni scheda per campo.
        La variante che recupera questo box -- rompere anche quando la frase
        precedente e' chiusa e la successiva comincia in maiuscola -- e' stata
        misurata e **scartata**: porta DB p.99 a 42 su 43 ma su SV p.181 rispezza
        la prosa a due colonne, da 17 paragrafi a 22 contro i 23 della regola
        vecchia.
        """

        spans = [
            _font_line(2, 0, "Non-Mostri: in combattimento, gli scheletri non ", y=0),
            _font_line(3, 0, "contano come mostri, ma come normali PNG.", y=10),
            _font_line(3, 1, "Resistenza: tutti i danni sono dimez-", y=20),
            _font_line(4, 0, "zati (arrotondando per eccesso).", y=30),
            _font_line(4, 1, "Immunità: gli scheletri sono immuni alla paura e ", y=40),
            _font_line(5, 0, "a PERSUADERE.", y=50),
        ]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual(
            [node.text for node in page.nodes],
            [
                "Non-Mostri: in combattimento, gli scheletri non contano come mostri, "
                "ma come normali PNG. Resistenza: tutti i danni sono dimezzati "
                "(arrotondando per eccesso). Immunità: gli scheletri sono immuni "
                "alla paura e a PERSUADERE.",
            ],
        )

    def test_a_new_block_in_another_font_still_starts_a_paragraph(self) -> None:
        # Fab p.248: il pallino Wingdings apre una voce, non continua la prosa.
        spans = [
            _font_line(3, 0, "Durante ogni sessione, dovresti attenerti a questi principi:"),
            _font_line(4, 0, "w Ritrai un mondo meraviglioso.", font="Wingdings-Regular"),
            _font_line(6, 0, "w Gestisci le informazioni.", font="Wingdings-Regular"),
        ]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual(len(page.nodes), 3)

    def test_every_primitive_lands_in_exactly_one_node(self) -> None:
        spans = [_span(1, 0, 0, "una frase."), _span(2, 0, 0, "Altra frase.")]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        covered = [pid for node in page.nodes for pid in node.primitive_ids]
        self.assertEqual(sorted(covered), sorted(s.primitive_id for s in spans))

    def test_an_empty_span_is_still_covered(self) -> None:
        spans = [_span(1, 0, 0, "testo"), _span(1, 0, 1, "")]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        covered = {pid for node in page.nodes for pid in node.primitive_ids}
        self.assertIn(spans[1].primitive_id, covered)

    def test_node_id_is_page_qualified_and_derived_from_the_source(self) -> None:
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=[_span(3, 1, 0, "testo")])
        self.assertEqual(page.nodes[0].node_id, "page:0099:text:b0003:l0001:s0000")

    def test_a_source_line_split_across_bands_gets_distinct_node_ids(self) -> None:
        # DB p.53: l'ordinamento a bande separa il glifo di elenco dal suo
        # testo, quindi la stessa riga di sorgente compare due volte. Con la
        # riga come identita' i due nodi collidevano.
        glyph = _span(7, 1, 0, "✦", y=0)
        other = _span(8, 0, 0, "Altra voce.", y=10)
        text = _span(7, 1, 1, "Arrabbiato – INT", y=20)
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=[glyph, other, text])
        ids = [node.node_id for node in page.nodes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_order_is_a_permutation_and_follows_the_received_order(self) -> None:
        spans = [_span(1, 0, 0, "prima.", y=0), _span(2, 0, 0, "Seconda.", y=10)]
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans)
        self.assertEqual([node.order for node in page.nodes], [0, 1])

    def test_interleaves_an_asset_note_at_its_sort_key(self) -> None:
        spans = [_span(1, 0, 0, "prima.", y=0), _span(2, 0, 0, "Seconda.", y=100)]
        note = AssetNoteInput(
            primitive_id="primitive:image:image:i0001",
            digest="md5:abc",
            file_name="md5_abc.png",
            bbox=(0.0, 50.0, 10.0, 60.0),
            occurrence_count=1,
            anchor_index=1,
            proposed_structural_kind="layout.embedded_visual",
            resolution="unresolved",
        )
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=spans, asset_notes=[note])
        self.assertEqual([node.kind for node in page.nodes], [
            "text.paragraph", "asset.note", "text.paragraph",
        ])

    def test_keeps_the_received_order_when_it_contradicts_geometry(self) -> None:
        # Il caso a due colonne: la colonna sinistra si legge prima anche se la
        # destra sta piu' in alto. Una versione precedente riordinava per (y0,x0)
        # e falliva su 4 pagine su 10 del campione cieco.
        left = _span(1, 0, 0, "Sinistra.", y=100)
        right = _span(2, 0, 0, "Destra.", y=10)
        page = build_page_ir2(page_id=PAGE, ordered_text_primitives=[left, right])
        self.assertEqual([node.text for node in page.nodes], ["Sinistra.", "Destra."])

    def test_places_a_note_before_the_first_paragraph_below_it(self) -> None:
        first = _span(1, 0, 0, "Prima.", y=0)
        second = _span(2, 0, 0, "Dopo.", y=100)
        note = AssetNoteInput(
            primitive_id="primitive:image:image:i0001",
            digest="md5:abc",
            file_name="md5_abc.png",
            bbox=(0.0, 50.0, 10.0, 60.0),
            occurrence_count=1,
            anchor_index=1,
        )
        page = build_page_ir2(
            page_id=PAGE, ordered_text_primitives=[first, second], asset_notes=[note]
        )
        self.assertEqual(
            [node.kind for node in page.nodes],
            ["text.paragraph", "asset.note", "text.paragraph"],
        )

    def test_a_note_below_every_paragraph_goes_last(self) -> None:
        span = _span(1, 0, 0, "Testo.", y=0)
        note = AssetNoteInput(
            primitive_id="primitive:image:image:i0001",
            digest="md5:abc",
            file_name="md5_abc.png",
            bbox=(0.0, 900.0, 10.0, 910.0),
            occurrence_count=1,
            anchor_index=99,
        )
        page = build_page_ir2(
            page_id=PAGE, ordered_text_primitives=[span], asset_notes=[note]
        )
        self.assertEqual([node.kind for node in page.nodes], ["text.paragraph", "asset.note"])

    def test_the_note_anchor_is_an_index_not_a_coordinate(self) -> None:
        # Su due colonne la y non dice l'ordine di lettura: la nota di
        # un'immagine della colonna destra deve poter stare fra il testo di
        # destra anche se la sinistra continua piu' in basso.
        left_top = _span(1, 0, 0, "Sinistra alto.", y=100)
        left_bottom = _span(2, 0, 0, "Sinistra basso.", y=400)
        right_top = _span(3, 0, 0, "Destra alto.", y=100)
        right_bottom = _span(4, 0, 0, "Destra basso.", y=400)
        note = AssetNoteInput(
            primitive_id="primitive:image:image:i0",
            digest="d",
            file_name="f.png",
            bbox=(300.0, 350.0, 400.0, 360.0),
            occurrence_count=1,
            anchor_index=3,  # davanti a "Destra basso."
        )
        page = build_page_ir2(
            page_id=PAGE,
            ordered_text_primitives=[left_top, left_bottom, right_top, right_bottom],
            asset_notes=[note],
        )
        self.assertEqual(
            [node.text or "<NOTA>" for node in page.nodes],
            ["Sinistra alto.", "Sinistra basso.", "Destra alto.", "<NOTA>", "Destra basso."],
        )

    def test_dehyphenation_touches_only_the_junction(self) -> None:
        # Un trattino lontano non deve sparire perche' la giunzione corrente
        # ne ha uno.
        self.assertEqual(
            join_lines("un tiro- variabile e i danni sono dimez-", "zati"),
            "un tiro- variabile e i danni sono dimezzati",
        )

    def test_an_empty_page_builds(self) -> None:
        self.assertEqual(build_page_ir2(page_id=PAGE, ordered_text_primitives=[]).nodes, ())


if __name__ == "__main__":
    unittest.main()
