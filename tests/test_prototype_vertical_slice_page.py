"""Tests for the deciding functions of scripts/prototype_vertical_slice_page.py.

Declared exception to the no-test-for-diagnostic-scripts precedent (Milestone
25/26/29/32/35): the two exit-4 invariants tested here are Milestone 36's exit
criterion, not a reported number -- see the module docstring of the script and
State.md for the full rationale.

Only the functions that decide (the two invariant verifiers and the three pure
helpers they and the extraction path depend on) are tested. Producer
composition, the co-reference/Resolution chain, and asset extraction itself
are covered by production tests or require a real PDF, which does not belong
in this test module.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from primitive_model import ImageOccurrencePrimitive, TextPrimitive
from scripts.prototype_vertical_slice_page import (
    _asset_identity,
    _image_index_from_observation_id,
    _strip_asset_markers,
    _verify_content_conservation,
    _verify_reference_integrity,
)


def _text(primitive_id: str, text: str) -> TextPrimitive:
    return TextPrimitive(
        primitive_id=primitive_id,
        bbox=(0.0, 0.0, 10.0, 10.0),
        text=text,
        source_observation_id=f"obs:{primitive_id}",
    )


def _image(
    primitive_id: str,
    *,
    content_digest: str | None = None,
) -> ImageOccurrencePrimitive:
    return ImageOccurrencePrimitive(
        primitive_id=primitive_id,
        bbox=(0.0, 0.0, 10.0, 10.0),
        source_observation_id=f"obs:{primitive_id}",
        content_digest=content_digest,
    )


class VerifyContentConservationTest(unittest.TestCase):
    def test_passes_when_reformatted_with_different_spacing_and_newlines(self) -> None:
        primitives = (_text("t1", "hello"), _text("t2", "world"))
        body = "hello\n\n   world  \n"
        _verify_content_conservation(primitives, body)  # must not raise

    def test_passes_with_an_empty_string_primitive(self) -> None:
        primitives = (_text("t1", ""), _text("t2", "abc"))
        body = "abc\n"
        _verify_content_conservation(primitives, body)  # must not raise

    def test_passes_when_two_runs_are_concatenated_without_a_separator(self) -> None:
        primitives = (_text("t1", "ab"), _text("t2", "cd"))
        body = "abcd\n"
        _verify_content_conservation(primitives, body)  # must not raise

    def test_passes_when_body_has_marker_lines_with_characters_absent_from_input(self) -> None:
        primitives = (_text("t1", "abc"),)
        body = (
            "abc\n"
            "%%VSLICE-ASSET%% primitive_id=x digest=y candidate_id=z asset_file=w.png\n"
        )
        _verify_content_conservation(primitives, body)  # must not raise

    def test_exits_4_when_body_is_missing_a_character(self) -> None:
        primitives = (_text("t1", "abc"),)
        body = "ab\n"
        with self.assertRaises(SystemExit) as context:
            _verify_content_conservation(primitives, body)
        self.assertEqual(context.exception.code, 4)

    def test_exits_4_when_body_has_an_extra_character(self) -> None:
        primitives = (_text("t1", "abc"),)
        body = "abcd\n"
        with self.assertRaises(SystemExit) as context:
            _verify_content_conservation(primitives, body)
        self.assertEqual(context.exception.code, 4)


def _passing_reference_integrity_kwargs(output_dir: Path) -> dict[str, object]:
    asset_path = output_dir / "asset1.png"
    asset_path.write_bytes(b"fake-bytes")
    page_md_body = (
        "some text\n"
        "%%VSLICE-ASSET%% primitive_id=p1 digest=d1 candidate_id=c1 "
        "asset_file=asset1.png\n"
    )
    return {
        "output_dir": output_dir,
        "written_asset_paths": {asset_path},
        "page_md_body": page_md_body,
        "review_md_text": "",
        "occurrence_row_count": 1,
        "image_primitive_count": 1,
        "asset_count": 1,
    }


class VerifyReferenceIntegrityTest(unittest.TestCase):
    def test_passes_on_a_consistent_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = _passing_reference_integrity_kwargs(Path(temporary_directory))
            _verify_reference_integrity(**kwargs)  # type: ignore[arg-type]  # must not raise

    def test_exits_4_when_body_references_a_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = _passing_reference_integrity_kwargs(Path(temporary_directory))
            kwargs["page_md_body"] = (
                str(kwargs["page_md_body"])
                + "%%VSLICE-ASSET%% primitive_id=p2 digest=d2 candidate_id=c2 "
                "asset_file=missing.png\n"
            )
            with self.assertRaises(SystemExit) as context:
                _verify_reference_integrity(**kwargs)  # type: ignore[arg-type]
            self.assertEqual(context.exception.code, 4)

    def test_exits_4_when_only_review_references_a_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = _passing_reference_integrity_kwargs(Path(temporary_directory))
            kwargs["review_md_text"] = "- asset_file=missing_review.png\n"
            with self.assertRaises(SystemExit) as context:
                _verify_reference_integrity(**kwargs)  # type: ignore[arg-type]
            self.assertEqual(context.exception.code, 4)

    def test_exits_4_when_occurrence_row_count_mismatches_image_primitive_count(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = _passing_reference_integrity_kwargs(Path(temporary_directory))
            kwargs["occurrence_row_count"] = 2
            with self.assertRaises(SystemExit) as context:
                _verify_reference_integrity(**kwargs)  # type: ignore[arg-type]
            self.assertEqual(context.exception.code, 4)

    def test_exits_4_when_written_paths_count_mismatches_asset_row_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            kwargs = _passing_reference_integrity_kwargs(Path(temporary_directory))
            kwargs["asset_count"] = 2
            with self.assertRaises(SystemExit) as context:
                _verify_reference_integrity(**kwargs)  # type: ignore[arg-type]
            self.assertEqual(context.exception.code, 4)


class StripAssetMarkersTest(unittest.TestCase):
    def test_removes_a_single_marker_line(self) -> None:
        body = "line1\n%%VSLICE-ASSET%% foo=bar\nline2\n"
        self.assertEqual(_strip_asset_markers(body), "line1\n\nline2\n")

    def test_removes_multiple_marker_lines(self) -> None:
        body = "line1\n%%VSLICE-ASSET%% a\n%%VSLICE-ASSET%% b\nline2\n"
        self.assertEqual(_strip_asset_markers(body), "line1\n\n\nline2\n")

    def test_does_not_touch_the_marker_sequence_when_not_at_line_start(self) -> None:
        body = "this line mentions %%VSLICE-ASSET%% mid-line, not at start\n"
        self.assertEqual(_strip_asset_markers(body), body)

    def test_leaves_a_body_without_markers_unchanged(self) -> None:
        body = "no markers here\njust text\n"
        self.assertEqual(_strip_asset_markers(body), body)


class AssetIdentityTest(unittest.TestCase):
    def test_uses_content_digest_when_present(self) -> None:
        primitive = _image("primitive:image:image:i0000", content_digest="md5:abc")
        identity, digest_missing = _asset_identity(primitive)
        self.assertEqual(identity, "md5:abc")
        self.assertFalse(digest_missing)

    def test_derives_identity_from_primitive_id_when_digest_is_none(self) -> None:
        primitive = _image("primitive:image:image:i0000", content_digest=None)
        identity, digest_missing = _asset_identity(primitive)
        self.assertEqual(identity, "missing:primitive:image:image:i0000")
        self.assertTrue(digest_missing)

    def test_two_digestless_occurrences_get_distinct_identities(self) -> None:
        first = _image("primitive:image:image:i0000", content_digest=None)
        second = _image("primitive:image:image:i0001", content_digest=None)

        first_identity, first_missing = _asset_identity(first)
        second_identity, second_missing = _asset_identity(second)

        self.assertNotEqual(first_identity, second_identity)
        self.assertTrue(first_missing)
        self.assertTrue(second_missing)


class ImageIndexFromObservationIdTest(unittest.TestCase):
    def test_parses_the_zero_padded_index(self) -> None:
        self.assertEqual(_image_index_from_observation_id("image:i0000"), 0)
        self.assertEqual(_image_index_from_observation_id("image:i0012"), 12)

    def test_rejects_an_unexpected_format(self) -> None:
        with self.assertRaises(ValueError):
            _image_index_from_observation_id("not-an-image-id")


if __name__ == "__main__":
    unittest.main()
