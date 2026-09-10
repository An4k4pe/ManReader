"""Resolution: quali corridoi respinti valgono comunque come confine di colonna.

Milestone 44, Fase 2. La regola e' V4, misurata nella Milestone 43: **dentro un
`table_candidate`, un corridoio respinto solo per mancanza di parole ai fianchi
vale come confine di colonna, a meno che un lato sia del tutto vuoto.** Fuori
dalle tabelle non cambia niente.

**Perche' sta in Resolution e non nel producer.** La regola guarda l'uscita di
due producer diversi -- i corridoi respinti di `column_band` e i candidati di
`table_candidate` -- e `AGENTS.MD` §Layout e candidati dice che la relazione fra
candidati di producer diversi si decide qui, mai dentro un producer.

**Perche' non e' un `ResolvedCandidateOutcome`.** Quel contratto assegna un esito
a un **candidato**, e un corridoio respinto candidato non e': `column_band` non
lo ha mai proposto. Forzarcelo dentro avrebbe voluto dire promuoverlo prima a
candidato, cioe' cambiare cio' che ogni consumer si trova davanti -- la strada
scartata alla Fase 1. Questo modulo emette quindi un artefatto **parallelo**, e
non tocca ne' `resolution_model.py` ne' `resolution_page_candidates.py`.

**Cosa NON fa, ed e' importante.** Non crea bande e non riordina niente. Dice
soltanto quali confini di colonna Resolution considera validi su quella pagina.
In particolare **non decide come si legge una tabella**: una regione a due
colonne letta per colonne da' «tutti i numeri, poi tutte le descrizioni», che su
una tabella e' l'ordine sbagliato. La lettura per righe e' la fase successiva, e
senza di essa consumare questi confini peggiora le tabelle invece di
migliorarle.

Nessuna soglia nuova: «un lato del tutto vuoto» e' la distinzione fra c'e' testo
e non ce n'e', non una grandezza da tarare. I criteri di ammissione del producer
restano suoi e non vengono riscritti qui -- il campo `rejected_only_by_wordiness`
li ha gia' applicati.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from geometry_model import _validate_finite_number, _validate_non_empty_string
from page_analysis_column_band_rejected_gutters import RejectedGutter
from page_analysis_model import RegionCandidate

_ADMITTED = "admitted_by_table_context"
_VALID_REASON_TOKENS = frozenset(
    {
        _ADMITTED,
        "outside_table_candidate",
        "empty_flank",
        "other_reject_reason",
    }
)


@dataclass(frozen=True, slots=True)
class ResolvedColumnBoundary:
    """L'esito che Resolution assegna a un corridoio respinto.

    Ogni corridoio respinto riceve un esito: quelli non ammessi portano il
    motivo per cui non lo sono. Nessuno sparisce in silenzio."""

    page_id: str
    x0: float
    x1: float
    y0: float
    y1: float
    outcome: Literal["admitted", "not_admitted"]
    reason_token: str

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
        for name in ("x0", "x1", "y0", "y1"):
            _validate_finite_number(getattr(self, name), name)
        if self.x1 <= self.x0:
            raise ValueError("x1 must be greater than x0")
        if self.y1 <= self.y0:
            raise ValueError("y1 must be greater than y0")
        if self.outcome not in ("admitted", "not_admitted"):
            raise ValueError('outcome must be "admitted" or "not_admitted"')
        if self.reason_token not in _VALID_REASON_TOKENS:
            raise ValueError(f"unknown reason_token: {self.reason_token!r}")
        if self.outcome == "admitted" and self.reason_token != _ADMITTED:
            raise ValueError(f'an admitted boundary must carry "{_ADMITTED}"')
        if self.outcome == "not_admitted" and self.reason_token == _ADMITTED:
            raise ValueError(f'a boundary that is not admitted must not carry "{_ADMITTED}"')


@dataclass(frozen=True, slots=True)
class ResolvedPageColumnBoundaries:
    """Gli esiti di tutti i corridoi respinti di una pagina."""

    page_id: str
    boundaries: tuple[ResolvedColumnBoundary, ...]

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
        if not isinstance(self.boundaries, tuple):
            raise ValueError("boundaries must be a tuple")
        for index, boundary in enumerate(self.boundaries):
            if not isinstance(boundary, ResolvedColumnBoundary):
                raise ValueError(f"boundaries[{index}] must be a ResolvedColumnBoundary")
            if boundary.page_id != self.page_id:
                raise ValueError(f"boundaries[{index}] belongs to another page")

    @property
    def admitted(self) -> tuple[ResolvedColumnBoundary, ...]:
        return tuple(b for b in self.boundaries if b.outcome == "admitted")


def _covered_by_a_table(
    gutter: RejectedGutter, table_candidates: tuple[RegionCandidate, ...]
) -> bool:
    """La tabella copre il corridoio: lo contiene in x e lo incrocia in y.

    E' la stessa relazione con cui i numeri della Milestone 43 sono stati
    misurati, scritta qui perche' l'oracolo di quella milestone resti
    confrontabile. Contenimento in x e sovrapposizione in y, non contenimento
    pieno: una tabella puo' cominciare sotto l'inizio del corridoio."""

    for candidate in table_candidates:
        x0, y0, x1, y1 = candidate.bbox
        if x0 <= gutter.x0 and x1 >= gutter.x1 and y0 <= gutter.y1 and y1 >= gutter.y0:
            return True
    return False


def resolve_column_boundaries(
    *,
    page_id: str,
    rejected_gutters: tuple[RejectedGutter, ...],
    table_candidates: tuple[RegionCandidate, ...],
) -> ResolvedPageColumnBoundaries:
    """Applica V4 ai corridoi respinti di una pagina."""

    _validate_non_empty_string(page_id, "page_id")
    if not isinstance(rejected_gutters, tuple):
        raise ValueError("rejected_gutters must be a tuple")
    if not isinstance(table_candidates, tuple):
        raise ValueError("table_candidates must be a tuple")

    boundaries: list[ResolvedColumnBoundary] = []
    for gutter in rejected_gutters:
        if not isinstance(gutter, RejectedGutter):
            raise ValueError("rejected_gutters items must be RejectedGutter")
        if gutter.page_id != page_id:
            raise ValueError("a rejected gutter belongs to another page")

        if not gutter.rejected_only_by_wordiness:
            outcome, reason = "not_admitted", "other_reject_reason"
        elif not _covered_by_a_table(gutter, table_candidates):
            outcome, reason = "not_admitted", "outside_table_candidate"
        elif min(gutter.left_chars_total, gutter.right_chars_total) == 0:
            outcome, reason = "not_admitted", "empty_flank"
        else:
            outcome, reason = "admitted", _ADMITTED

        boundaries.append(
            ResolvedColumnBoundary(
                page_id=page_id,
                x0=gutter.x0,
                x1=gutter.x1,
                y0=gutter.y0,
                y1=gutter.y1,
                outcome=outcome,  # type: ignore[arg-type]
                reason_token=reason,
            )
        )
    return ResolvedPageColumnBoundaries(page_id=page_id, boundaries=tuple(boundaries))
