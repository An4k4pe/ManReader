"""Tests for read-only co-referenced candidate inventory diagnostics."""

from __future__ import annotations

import inspect
import json
import unittest
from typing import cast
from unittest.mock import patch

from geometry_model import PageGeometry
from page_analysis_co_reference_candidate_diagnostics import (
    dump_co_referenced_page_candidate_inventory,
)
from page_analysis_model import (
    PAGE_ANALYSIS_SCHEMA_VERSION,
    PageAnalysis,
    PageAnalysisProvenance,
    RegionCandidate,
)
from primitive_model import (
    DrawingPrimitive,
    ImageOccurrencePrimitive,
    NormalizedPrimitivePage,
    TextPrimitive,
)


def _page() -> NormalizedPrimitivePage:
    return NormalizedPrimitivePage(
        schema_version="1.0",
        source_capture_id="capture-1",
        source_id="source-1",
        page_id="page-1",
        page_index=7,
        page_geometry=PageGeometry(
            width=100.0,
            height=200.0,
            unit="pt",
            coordinate_system="top_left_y_down",
        ),
        capture_to_canonical_transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        text_primitives=(
            TextPrimitive(
                primitive_id="left",
                bbox=(0.0, 60.0, 20.0, 70.0),
                text="Left",
                source_observation_id="obs:left",
            ),
            TextPrimitive(
                primitive_id="right",
                bbox=(80.0, 80.0, 100.0, 90.0),
                text="Right",
                source_observation_id="obs:right",
            ),
        ),
        image_primitives=(
            ImageOccurrencePrimitive(
                primitive_id="edge",
                bbox=(0.0, 0.0, 80.0, 20.0),
                source_observation_id="obs:edge",
            ),
        ),
        drawing_primitives=(
            DrawingPrimitive(
                primitive_id="covering",
                bbox=(0.0, 0.0, 100.0, 200.0),
                source_observation_id="obs:covering",
            ),
        ),
    )


def _analysis(
    page: NormalizedPrimitivePage,
    *,
    producer_name: str,
    generation_id: str,
    candidate: RegionCandidate,
) -> PageAnalysis:
    return PageAnalysis(
        schema_version=PAGE_ANALYSIS_SCHEMA_VERSION,
        generation_id=generation_id,
        page_id=page.page_id,
        provenance=PageAnalysisProvenance(
            source_id=page.source_id,
            source_capture_id=page.source_capture_id,
            source_page_id=page.page_id,
            source_primitive_schema_version=page.schema_version,
            producer_name=producer_name,
            producer_version="0.1",
            configuration_id=f"{producer_name}-config",
        ),
        candidates=(candidate,),
    )


class CoReferencedPageCandidateDiagnosticsTests(unittest.TestCase):
    def test_public_signature_is_keyword_only_for_candidate_producers(self) -> None:
        signature = inspect.signature(dump_co_referenced_page_candidate_inventory)

        self.assertEqual(tuple(signature.parameters), ("primitive_page", "candidate_producers"))
        self.assertIs(
            signature.parameters["candidate_producers"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

    def test_single_and_all_producers_produce_json_compatible_inventory(self) -> None:
        page = _page()

        singleton = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band",),
        )
        all_producers = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=(
                "singleton-side-band",
                "local-fragment-side-band",
                "page-edge-visual",
                "page-covering-visual",
            ),
        )

        self.assertEqual(singleton["diagnostic_kind"], "co-referenced-candidate-inventory")
        self.assertEqual(singleton["page_id"], page.page_id)
        self.assertEqual(singleton["page_index"], page.page_index)
        self.assertEqual(singleton["source_capture_id"], page.source_capture_id)
        self.assertEqual(singleton["candidate_producers"], ["singleton-side-band"])
        self.assertEqual(len(cast(list[object], singleton["analysis_streams"])), 1)
        self.assertEqual(
            all_producers["candidate_producers"],
            [
                "singleton-side-band",
                "local-fragment-side-band",
                "page-edge-visual",
                "page-covering-visual",
            ],
        )
        self.assertEqual(len(cast(list[object], all_producers["analysis_streams"])), 4)
        self.assertEqual(json.loads(json.dumps(all_producers)), all_producers)
        self.assertFalse(_contains_key(all_producers, "schema_version"))

    def test_canonical_stream_order_candidate_order_and_generation_ids(self) -> None:
        page = _page()
        result = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=(
                "page-covering-visual",
                "singleton-side-band",
                "page-edge-visual",
                "local-fragment-side-band",
            ),
        )
        streams = cast(list[dict[str, object]], result["analysis_streams"])

        self.assertEqual(
            [stream["candidate_producer"] for stream in streams],
            [
                "local-fragment-side-band",
                "page-covering-visual",
                "page-edge-visual",
                "singleton-side-band",
            ],
        )
        generation_by_key = {
            cast(str, stream["candidate_producer"]): cast(str, stream["generation_id"])
            for stream in streams
        }
        self.assertEqual(
            generation_by_key,
            {
                "singleton-side-band": "diagnostic-singleton-side-band-analysis:7",
                "local-fragment-side-band": "diagnostic-local-fragment-side-band-analysis:7",
                "page-edge-visual": "diagnostic-page-edge-visual-analysis:7",
                "page-covering-visual": "diagnostic-page-covering-visual-analysis:7",
            },
        )
        singleton_stream = next(
            stream
            for stream in streams
            if stream["candidate_producer"] == "singleton-side-band"
        )
        candidates = cast(list[dict[str, object]], singleton_stream["candidates"])
        self.assertEqual(
            [
                cast(dict[str, str], candidate["candidate_reference"])["candidate_id"]
                for candidate in candidates
            ],
            ["candidate:side-band:left", "candidate:side-band:right"],
        )
        self.assertEqual(
            set(cast(dict[str, str], candidates[0]["candidate_reference"])),
            {
                "producer_name",
                "producer_version",
                "configuration_id",
                "generation_id",
                "candidate_id",
            },
        )
        self.assertEqual(
            cast(dict[str, str], candidates[0]["candidate_reference"])["producer_name"],
            "page_analysis.singleton_side_band",
        )

    def test_input_order_does_not_change_inventory_or_mutate_page(self) -> None:
        page = _page()
        before = page
        first = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("page-edge-visual", "singleton-side-band"),
        )
        second = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band", "page-edge-visual"),
        )

        self.assertEqual(first, second)
        self.assertEqual(page, before)

    def test_rejects_invalid_page_and_candidate_producer_inputs(self) -> None:
        page = _page()
        invalid_values = (
            (cast(tuple[str, ...], ()), "candidate_producers"),
            (cast(tuple[str, ...], ["singleton-side-band"]), "tuple"),
            (cast(tuple[str, ...], ("",)), "candidate_producers"),
            (cast(tuple[str, ...], (cast(str, object()),)), "candidate_producers"),
            (cast(tuple[str, ...], ("unknown",)), "unknown"),
            (
                ("singleton-side-band", "singleton-side-band"),
                "duplicate",
            ),
        )
        for candidate_producers, token in invalid_values:
            with self.subTest(candidate_producers=candidate_producers), self.assertRaisesRegex(
                ValueError,
                token,
            ):
                dump_co_referenced_page_candidate_inventory(
                    page,
                    candidate_producers=candidate_producers,
                )
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_co_referenced_page_candidate_inventory(
                cast(NormalizedPrimitivePage, object()),
                candidate_producers=("singleton-side-band",),
            )

    def test_executes_only_requested_producers(self) -> None:
        page = _page()
        calls: list[str] = []
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        original_builders = diagnostics._BUILDERS.copy()

        def tracked(name: str):
            def build(
                primitive_page: NormalizedPrimitivePage,
                *,
                generation_id: str,
            ) -> PageAnalysis:
                calls.append(name)
                return original_builders[name](
                    primitive_page,
                    generation_id=generation_id,
                )

            return build

        with patch.dict(
            diagnostics._BUILDERS,
            {name: tracked(name) for name in original_builders},
            clear=True,
        ):
            dump_co_referenced_page_candidate_inventory(
                page,
                candidate_producers=("page-edge-visual", "singleton-side-band"),
            )

        self.assertEqual(set(calls), {"singleton-side-band", "page-edge-visual"})
        self.assertEqual(len(calls), 2)

    def test_references_are_stream_scoped_for_shared_candidate_ids_and_objects(self) -> None:
        page = _page()
        shared_candidate = RegionCandidate(
            candidate_id="shared",
            page_id=page.page_id,
            bbox=(0.0, 60.0, 20.0, 70.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("left",),
        )
        first = _analysis(
            page,
            producer_name="alpha",
            generation_id="first",
            candidate=shared_candidate,
        )
        second = _analysis(
            page,
            producer_name="beta",
            generation_id="second",
            candidate=shared_candidate,
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        with patch.dict(
            diagnostics._BUILDERS,
            {
                "singleton-side-band": lambda *_args, **_kwargs: first,
                "local-fragment-side-band": lambda *_args, **_kwargs: second,
            },
            clear=False,
        ):
            result = dump_co_referenced_page_candidate_inventory(
                page,
                candidate_producers=(
                    "singleton-side-band",
                    "local-fragment-side-band",
                ),
            )

        streams = cast(list[dict[str, object]], result["analysis_streams"])
        references = [
            cast(dict[str, str], cast(list[dict[str, object]], stream["candidates"])[0]["candidate_reference"])
            for stream in streams
        ]
        self.assertEqual([reference["candidate_id"] for reference in references], ["shared", "shared"])
        self.assertNotEqual(references[0]["producer_name"], references[1]["producer_name"])


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
