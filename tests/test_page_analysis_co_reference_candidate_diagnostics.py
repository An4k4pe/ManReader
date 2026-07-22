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
    dump_co_referenced_page_candidate_pair_measurements,
    dump_co_referenced_page_candidate_primitive_set_measurements,
)
from page_analysis_co_reference_candidate_reference import (
    CoReferencedPageCandidateReference,
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

    def test_pair_signature_same_stream_self_relation_and_exact_measurements(self) -> None:
        signature = inspect.signature(dump_co_referenced_page_candidate_pair_measurements)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "primitive_page",
                "first_candidate_reference",
                "second_candidate_reference",
            ),
        )
        self.assertIs(
            signature.parameters["first_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            signature.parameters["second_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band",),
        )
        references = _inventory_references(inventory)
        first, second = references
        measurements = dump_co_referenced_page_candidate_pair_measurements(
            page,
            first_candidate_reference=first,
            second_candidate_reference=second,
        )
        self.assertEqual(measurements["horizontal_gap"], 60.0)
        self.assertEqual(measurements["vertical_gap"], 10.0)
        self.assertEqual(measurements["horizontal_overlap"], 0.0)
        self.assertEqual(measurements["vertical_overlap"], 0.0)
        self.assertEqual(measurements["x0_delta"], 80.0)
        self.assertEqual(measurements["y0_delta"], 20.0)
        self.assertEqual(measurements["x1_delta"], 80.0)
        self.assertEqual(measurements["y1_delta"], 20.0)
        self.assertEqual(
            set(measurements),
            {
                "diagnostic_kind",
                "page_id",
                "page_index",
                "source_capture_id",
                "first_candidate_reference",
                "second_candidate_reference",
                "first_candidate_bbox",
                "second_candidate_bbox",
                "horizontal_gap",
                "vertical_gap",
                "horizontal_overlap",
                "vertical_overlap",
                "x0_delta",
                "y0_delta",
                "x1_delta",
                "y1_delta",
            },
        )
        self.assertFalse(_contains_key(measurements, "schema_version"))
        self.assertEqual(json.loads(json.dumps(measurements)), measurements)

        self_relation = dump_co_referenced_page_candidate_pair_measurements(
            page,
            first_candidate_reference=first,
            second_candidate_reference=first,
        )
        self.assertEqual(self_relation["horizontal_gap"], 0.0)
        self.assertEqual(self_relation["vertical_gap"], 0.0)
        self.assertEqual(self_relation["horizontal_overlap"], 20.0)
        self.assertEqual(self_relation["vertical_overlap"], 10.0)
        self.assertEqual(self_relation["x0_delta"], 0.0)
        self.assertEqual(self_relation["y0_delta"], 0.0)
        self.assertEqual(self_relation["x1_delta"], 0.0)
        self.assertEqual(self_relation["y1_delta"], 0.0)

    def test_pair_executes_only_required_streams_and_uses_public_measurement(self) -> None:
        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band", "page-edge-visual"),
        )
        singleton_reference = _reference_for_producer(
            inventory,
            "page_analysis.singleton_side_band",
        )
        edge_reference = _reference_for_producer(
            inventory,
            "page_analysis.page_edge_visual",
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        original_builders = diagnostics._BUILDERS.copy()
        calls: list[tuple[str, str]] = []

        def tracked(name: str):
            def build(
                primitive_page: NormalizedPrimitivePage,
                *,
                generation_id: str,
            ) -> PageAnalysis:
                calls.append((name, generation_id))
                return original_builders[name](
                    primitive_page,
                    generation_id=generation_id,
                )

            return build

        with (
            patch.dict(
                diagnostics._BUILDERS,
                {name: tracked(name) for name in original_builders},
                clear=True,
            ),
            patch.object(
                diagnostics,
                "measure_co_referenced_page_candidate_pair",
                wraps=diagnostics.measure_co_referenced_page_candidate_pair,
            ) as measure,
        ):
            result = dump_co_referenced_page_candidate_pair_measurements(
                page,
                first_candidate_reference=singleton_reference,
                second_candidate_reference=edge_reference,
            )

        self.assertEqual(
            {name for name, _generation_id in calls},
            {"singleton-side-band", "page-edge-visual"},
        )
        self.assertEqual(len(calls), 2)
        measure.assert_called_once()
        self.assertEqual(result["diagnostic_kind"], "co-referenced-candidate-pair-measurements")

    def test_pair_same_producer_with_different_generations_executes_twice(self) -> None:
        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band",),
        )
        reference = _inventory_references(inventory)[0]
        first = CoReferencedPageCandidateReference(
            reference.producer_name,
            reference.producer_version,
            reference.configuration_id,
            "generation-a",
            reference.candidate_id,
        )
        second = CoReferencedPageCandidateReference(
            reference.producer_name,
            reference.producer_version,
            reference.configuration_id,
            "generation-b",
            reference.candidate_id,
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        original = diagnostics._BUILDERS["singleton-side-band"]
        calls: list[str] = []

        def tracked(
            primitive_page: NormalizedPrimitivePage,
            *,
            generation_id: str,
        ) -> PageAnalysis:
            calls.append(generation_id)
            return original(primitive_page, generation_id=generation_id)

        with patch.dict(
            diagnostics._BUILDERS,
            {"singleton-side-band": tracked},
        ):
            dump_co_referenced_page_candidate_pair_measurements(
                page,
                first_candidate_reference=first,
                second_candidate_reference=second,
            )

        self.assertEqual(calls, ["generation-a", "generation-b"])

    def test_pair_rejects_invalid_references_without_fallback(self) -> None:
        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band", "local-fragment-side-band"),
        )
        singleton_reference = _reference_for_producer(
            inventory,
            "page_analysis.singleton_side_band",
        )
        local_reference = _reference_for_producer(
            inventory,
            "page_analysis.local_fragment_side_band",
        )
        invalid_references = (
            (
                CoReferencedPageCandidateReference(
                    "unknown", "0.1", "config", "generation", "candidate"
                ),
                "producer_name",
            ),
            (
                CoReferencedPageCandidateReference(
                    singleton_reference.producer_name,
                    "wrong",
                    singleton_reference.configuration_id,
                    singleton_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "producer_version",
            ),
            (
                CoReferencedPageCandidateReference(
                    singleton_reference.producer_name,
                    singleton_reference.producer_version,
                    "wrong",
                    singleton_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "configuration_id",
            ),
            (
                CoReferencedPageCandidateReference(
                    local_reference.producer_name,
                    local_reference.producer_version,
                    local_reference.configuration_id,
                    local_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "candidate_id",
            ),
        )
        for invalid_reference, token in invalid_references:
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                dump_co_referenced_page_candidate_pair_measurements(
                    page,
                    first_candidate_reference=invalid_reference,
                    second_candidate_reference=singleton_reference,
                )
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_co_referenced_page_candidate_pair_measurements(
                cast(NormalizedPrimitivePage, object()),
                first_candidate_reference=singleton_reference,
                second_candidate_reference=singleton_reference,
            )
        with self.assertRaisesRegex(ValueError, "first_candidate_reference"):
            dump_co_referenced_page_candidate_pair_measurements(
                page,
                first_candidate_reference=cast(CoReferencedPageCandidateReference, object()),
                second_candidate_reference=singleton_reference,
            )

    def test_primitive_set_signature_and_payload_structure(self) -> None:
        signature = inspect.signature(
            dump_co_referenced_page_candidate_primitive_set_measurements
        )
        self.assertEqual(
            tuple(signature.parameters),
            (
                "primitive_page",
                "first_candidate_reference",
                "second_candidate_reference",
            ),
        )
        self.assertIs(
            signature.parameters["first_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )
        self.assertIs(
            signature.parameters["second_candidate_reference"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band",),
        )
        first, second = _inventory_references(inventory)
        result = dump_co_referenced_page_candidate_primitive_set_measurements(
            page,
            first_candidate_reference=first,
            second_candidate_reference=second,
        )

        self.assertEqual(
            set(result),
            {
                "diagnostic_kind",
                "page_id",
                "page_index",
                "source_capture_id",
                "first_candidate_reference",
                "second_candidate_reference",
                "first_candidate_primitive_ids",
                "second_candidate_primitive_ids",
                "shared_primitive_ids",
                "first_only_primitive_ids",
                "second_only_primitive_ids",
            },
        )
        self.assertEqual(
            result["diagnostic_kind"],
            "co-referenced-candidate-primitive-set-measurements",
        )
        self.assertEqual(result["page_id"], page.page_id)
        self.assertEqual(result["page_index"], page.page_index)
        self.assertEqual(result["source_capture_id"], page.source_capture_id)
        self.assertFalse(_contains_key(result, "schema_version"))
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_primitive_set_pass_through_with_asymmetric_order_and_self_relation(
        self,
    ) -> None:
        page = _page()
        candidate_a = RegionCandidate(
            candidate_id="a",
            page_id=page.page_id,
            bbox=(0.0, 60.0, 20.0, 70.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("left", "right", "edge"),
        )
        candidate_b = RegionCandidate(
            candidate_id="b",
            page_id=page.page_id,
            bbox=(80.0, 80.0, 100.0, 90.0),
            proposed_structural_kind="layout.page_edge_visual",
            primitive_ids=("right", "covering"),
        )
        analysis_a = _analysis(
            page,
            producer_name="page_analysis.singleton_side_band",
            generation_id="generation-a",
            candidate=candidate_a,
        )
        analysis_b = _analysis(
            page,
            producer_name="page_analysis.page_edge_visual",
            generation_id="generation-b",
            candidate=candidate_b,
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        with patch.dict(
            diagnostics._BUILDERS,
            {
                "singleton-side-band": lambda *_args, **_kwargs: analysis_a,
                "page-edge-visual": lambda *_args, **_kwargs: analysis_b,
            },
            clear=False,
        ):
            reference_a = CoReferencedPageCandidateReference(
                producer_name="page_analysis.singleton_side_band",
                producer_version="0.1",
                configuration_id="page_analysis.singleton_side_band-config",
                generation_id="generation-a",
                candidate_id="a",
            )
            reference_b = CoReferencedPageCandidateReference(
                producer_name="page_analysis.page_edge_visual",
                producer_version="0.1",
                configuration_id="page_analysis.page_edge_visual-config",
                generation_id="generation-b",
                candidate_id="b",
            )

            forward = dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=reference_a,
                second_candidate_reference=reference_b,
            )
            backward = dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=reference_b,
                second_candidate_reference=reference_a,
            )
            self_relation = dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=reference_a,
                second_candidate_reference=reference_a,
            )

        self.assertEqual(forward["first_candidate_primitive_ids"], ["left", "right", "edge"])
        self.assertEqual(forward["second_candidate_primitive_ids"], ["right", "covering"])
        self.assertEqual(forward["shared_primitive_ids"], ["right"])
        self.assertEqual(forward["first_only_primitive_ids"], ["left", "edge"])
        self.assertEqual(forward["second_only_primitive_ids"], ["covering"])

        self.assertEqual(backward["first_candidate_primitive_ids"], ["right", "covering"])
        self.assertEqual(backward["second_candidate_primitive_ids"], ["left", "right", "edge"])
        self.assertEqual(backward["shared_primitive_ids"], ["right"])
        self.assertEqual(backward["first_only_primitive_ids"], ["covering"])
        self.assertEqual(backward["second_only_primitive_ids"], ["left", "edge"])

        self.assertEqual(self_relation["shared_primitive_ids"], ["left", "right", "edge"])
        self.assertEqual(self_relation["first_only_primitive_ids"], [])
        self.assertEqual(self_relation["second_only_primitive_ids"], [])

    def test_primitive_set_cross_stream_candidate_id_collision(self) -> None:
        page = _page()
        candidate_singleton = RegionCandidate(
            candidate_id="shared",
            page_id=page.page_id,
            bbox=(0.0, 60.0, 20.0, 70.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("left", "right"),
        )
        candidate_local_fragment = RegionCandidate(
            candidate_id="shared",
            page_id=page.page_id,
            bbox=(80.0, 80.0, 100.0, 90.0),
            proposed_structural_kind="layout.side_band",
            primitive_ids=("right", "edge"),
        )
        analysis_singleton = _analysis(
            page,
            producer_name="page_analysis.singleton_side_band",
            generation_id="generation-singleton",
            candidate=candidate_singleton,
        )
        analysis_local_fragment = _analysis(
            page,
            producer_name="page_analysis.local_fragment_side_band",
            generation_id="generation-local-fragment",
            candidate=candidate_local_fragment,
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        with patch.dict(
            diagnostics._BUILDERS,
            {
                "singleton-side-band": lambda *_args, **_kwargs: analysis_singleton,
                "local-fragment-side-band": lambda *_args, **_kwargs: analysis_local_fragment,
            },
            clear=False,
        ):
            reference_singleton = CoReferencedPageCandidateReference(
                producer_name="page_analysis.singleton_side_band",
                producer_version="0.1",
                configuration_id="page_analysis.singleton_side_band-config",
                generation_id="generation-singleton",
                candidate_id="shared",
            )
            reference_local_fragment = CoReferencedPageCandidateReference(
                producer_name="page_analysis.local_fragment_side_band",
                producer_version="0.1",
                configuration_id="page_analysis.local_fragment_side_band-config",
                generation_id="generation-local-fragment",
                candidate_id="shared",
            )

            result = dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=reference_singleton,
                second_candidate_reference=reference_local_fragment,
            )

        self.assertEqual(result["first_candidate_primitive_ids"], ["left", "right"])
        self.assertEqual(result["second_candidate_primitive_ids"], ["right", "edge"])
        self.assertEqual(result["shared_primitive_ids"], ["right"])
        self.assertEqual(result["first_only_primitive_ids"], ["left"])
        self.assertEqual(result["second_only_primitive_ids"], ["edge"])

    def test_primitive_set_executes_only_required_streams_and_uses_public_measurement(
        self,
    ) -> None:
        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band", "page-edge-visual"),
        )
        singleton_reference = _reference_for_producer(
            inventory,
            "page_analysis.singleton_side_band",
        )
        edge_reference = _reference_for_producer(
            inventory,
            "page_analysis.page_edge_visual",
        )
        import page_analysis_co_reference_candidate_diagnostics as diagnostics

        original_builders = diagnostics._BUILDERS.copy()
        calls: list[tuple[str, str]] = []

        def tracked(name: str):
            def build(
                primitive_page: NormalizedPrimitivePage,
                *,
                generation_id: str,
            ) -> PageAnalysis:
                calls.append((name, generation_id))
                return original_builders[name](
                    primitive_page,
                    generation_id=generation_id,
                )

            return build

        with (
            patch.dict(
                diagnostics._BUILDERS,
                {name: tracked(name) for name in original_builders},
                clear=True,
            ),
            patch.object(
                diagnostics,
                "measure_co_referenced_page_candidate_primitive_sets",
                wraps=diagnostics.measure_co_referenced_page_candidate_primitive_sets,
            ) as measure,
        ):
            result = dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=singleton_reference,
                second_candidate_reference=edge_reference,
            )

        self.assertEqual(
            {name for name, _generation_id in calls},
            {"singleton-side-band", "page-edge-visual"},
        )
        self.assertEqual(len(calls), 2)
        measure.assert_called_once()
        self.assertEqual(
            result["diagnostic_kind"],
            "co-referenced-candidate-primitive-set-measurements",
        )

    def test_primitive_set_rejects_invalid_references_without_fallback(self) -> None:
        page = _page()
        inventory = dump_co_referenced_page_candidate_inventory(
            page,
            candidate_producers=("singleton-side-band", "local-fragment-side-band"),
        )
        singleton_reference = _reference_for_producer(
            inventory,
            "page_analysis.singleton_side_band",
        )
        local_reference = _reference_for_producer(
            inventory,
            "page_analysis.local_fragment_side_band",
        )
        invalid_references = (
            (
                CoReferencedPageCandidateReference(
                    "unknown", "0.1", "config", "generation", "candidate"
                ),
                "producer_name",
            ),
            (
                CoReferencedPageCandidateReference(
                    singleton_reference.producer_name,
                    "wrong",
                    singleton_reference.configuration_id,
                    singleton_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "producer_version",
            ),
            (
                CoReferencedPageCandidateReference(
                    singleton_reference.producer_name,
                    singleton_reference.producer_version,
                    "wrong",
                    singleton_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "configuration_id",
            ),
            (
                CoReferencedPageCandidateReference(
                    local_reference.producer_name,
                    local_reference.producer_version,
                    local_reference.configuration_id,
                    local_reference.generation_id,
                    singleton_reference.candidate_id,
                ),
                "candidate_id",
            ),
        )
        for invalid_reference, token in invalid_references:
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, token):
                dump_co_referenced_page_candidate_primitive_set_measurements(
                    page,
                    first_candidate_reference=invalid_reference,
                    second_candidate_reference=singleton_reference,
                )
        with self.assertRaisesRegex(ValueError, "primitive_page"):
            dump_co_referenced_page_candidate_primitive_set_measurements(
                cast(NormalizedPrimitivePage, object()),
                first_candidate_reference=singleton_reference,
                second_candidate_reference=singleton_reference,
            )
        with self.assertRaisesRegex(ValueError, "first_candidate_reference"):
            dump_co_referenced_page_candidate_primitive_set_measurements(
                page,
                first_candidate_reference=cast(CoReferencedPageCandidateReference, object()),
                second_candidate_reference=singleton_reference,
            )


def _inventory_references(
    inventory: dict[str, object],
) -> list[CoReferencedPageCandidateReference]:
    streams = cast(list[dict[str, object]], inventory["analysis_streams"])
    return [
        CoReferencedPageCandidateReference(
            **cast(dict[str, str], candidate["candidate_reference"])
        )
        for stream in streams
        for candidate in cast(list[dict[str, object]], stream["candidates"])
    ]


def _reference_for_producer(
    inventory: dict[str, object],
    producer_name: str,
) -> CoReferencedPageCandidateReference:
    return next(
        reference
        for reference in _inventory_references(inventory)
        if reference.producer_name == producer_name
    )


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
