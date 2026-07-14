"""Shared helpers for fold structure scanners (PYPOST-732)."""

from pypost.ui.widgets.fold.fold_region import FoldRegion


def line_at_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n")


def path_id(segments: list[str | int]) -> str:
    if not segments:
        return "/"
    return "/" + "/".join(str(segment) for segment in segments)


def append_region_if_multiline(
    regions: list[FoldRegion],
    *,
    region_id: str,
    start_line: int,
    end_line: int,
    kind: str,
) -> None:
    if end_line > start_line:
        regions.append(
            FoldRegion(
                region_id=region_id,
                header_block=start_line,
                start_block=start_line,
                end_block=end_line,
                kind=kind,
            )
        )
