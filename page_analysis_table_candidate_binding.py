"""Pure binding between one normalized page and its opened pdfplumber page."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pdfplumber.page import Page as PdfPlumberPage

from primitive_model import NormalizedPrimitivePage

_PAGE_ID_PATTERN = re.compile(r"^page:(\d+)$")


@dataclass(frozen=True, slots=True)
class BoundTableCandidatePage:
    """One normalized page explicitly paired with the matching pdfplumber page."""

    primitive_page: NormalizedPrimitivePage
    plumber_page: PdfPlumberPage

    def __post_init__(self) -> None:
        if not isinstance(self.primitive_page, NormalizedPrimitivePage):
            raise ValueError("primitive_page must be a NormalizedPrimitivePage")

        match = _PAGE_ID_PATTERN.fullmatch(self.primitive_page.page_id)
        plumber_page_number = self.plumber_page.page_number
        if match is None:
            raise ValueError(
                "page_id format mismatch: "
                f"primitive_page.page_id={self.primitive_page.page_id!r}, "
                f"plumber_page.page_number={plumber_page_number!r}"
            )

        primitive_page_number = int(match.group(1))
        if primitive_page_number != plumber_page_number:
            raise ValueError(
                "page number mismatch: "
                f"primitive_page.page_id={self.primitive_page.page_id!r} "
                f"({primitive_page_number}), plumber_page.page_number={plumber_page_number!r}"
            )
