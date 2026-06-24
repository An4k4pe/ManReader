"""Lightweight validation for ManReader's loaded document IR.

The validator reports issues without mutating the IR so review, enrichment, and
human override steps can decide how to handle invalid or incomplete data.
"""

from __future__ import annotations

from ir_model import DocumentIR, Issue


def validate_document_ir(document: DocumentIR) -> list[Issue]:
    """Return validation issues found in a loaded DocumentIR."""
    issues: list[Issue] = []
    seen_ids: dict[str, str] = {}

    if not document.schema_version:
        issues.append(
            _issue(
                kind="missing_schema_version",
                target_id=None,
                message="schema_version is empty.",
            )
        )

    if not document.source_path:
        issues.append(
            _issue(
                kind="missing_source_path",
                target_id=None,
                message="source_path is empty.",
            )
        )

    if document.page_count != len(document.pages):
        issues.append(
            _issue(
                kind="page_count_mismatch",
                target_id=None,
                message=f"page_count is {document.page_count}, but pages contains {len(document.pages)} items.",
            )
        )

    for page in document.pages:
        if page.id:
            _register_id(issues, seen_ids, page.id, "page", page.page_num)
        else:
            issues.append(
                _issue(
                    kind="missing_page_id",
                    target_id=None,
                    page_num=page.page_num,
                    message="Page id is empty.",
                )
            )

        for block in page.blocks:
            if block.id:
                _register_id(issues, seen_ids, block.id, "block", block.page_num)
            else:
                issues.append(
                    _issue(
                        kind="missing_block_id",
                        target_id=None,
                        page_num=block.page_num,
                        message="Block id is empty.",
                    )
                )

            if block.bbox is not None and not _is_valid_bbox(block.bbox):
                issues.append(
                    _issue(
                        kind="invalid_bbox",
                        target_id=block.id or None,
                        page_num=block.page_num,
                        message="Block bbox must contain exactly four numeric values.",
                    )
                )

            if block.asset is None:
                continue

            if block.asset.id:
                _register_id(issues, seen_ids, block.asset.id, "asset", block.page_num)
            else:
                issues.append(
                    _issue(
                        kind="missing_asset_id",
                        target_id=block.id or None,
                        page_num=block.page_num,
                        path=block.asset.path,
                        message="Asset id is empty.",
                    )
                )

    for entity in document.entities:
        if entity.id:
            _register_id(issues, seen_ids, entity.id, "entity", entity.page_num)
        else:
            issues.append(
                _issue(
                    kind="missing_entity_id",
                    target_id=None,
                    page_num=entity.page_num,
                    message="Entity id is empty.",
                )
            )

    return issues


def _register_id(
    issues: list[Issue],
    seen_ids: dict[str, str],
    item_id: str,
    kind: str,
    page_num: int | None,
) -> None:
    previous_kind = seen_ids.get(item_id)
    if previous_kind is not None:
        issues.append(
            _issue(
                kind="duplicate_id",
                target_id=item_id,
                page_num=page_num,
                message=f"ID {item_id!r} is used by both {previous_kind} and {kind}.",
            )
        )
        return

    seen_ids[item_id] = kind


def _is_valid_bbox(value: object) -> bool:
    if not isinstance(value, (tuple, list)):
        return False

    if len(value) != 4:
        return False

    # bool is an int subclass, but coordinates should be real numeric geometry.
    return all(isinstance(coord, (int, float)) and not isinstance(coord, bool) for coord in value)


def _issue(
    kind: str,
    target_id: str | None,
    message: str,
    page_num: int | None = None,
    path: str | None = None,
) -> Issue:
    return Issue(
        id=f"validation:{kind}:{target_id or 'document'}:{page_num or 0}",
        target_id=target_id,
        page_num=page_num,
        kind="validation",
        path=path,
        reason=kind,
        message=message,
    )
