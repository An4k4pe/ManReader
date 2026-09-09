"""I corridoi che l'ammissione di `layout.column_band` ha respinto.

Milestone 44, Fase 1. Osserva, non decide: qui non si dice che un corridoio
respinto avrebbe dovuto essere una banda, si dice soltanto che **c'era** e
perche' e' stato respinto.

**Il buco che chiude.** Il producer incatena i corridoi verticali di una pagina,
li giudica e tiene gli ammessi. Il verdetto sugli altri viveva dentro una
variabile locale e spariva: quando il producer aveva finito, un corridoio
respinto non esisteva piu' in nessun artefatto. La docstring di `_reject_reason`
dichiara da sempre il contrario -- «uno scarto etichettato e' materiale per i
producer successivi. Un gutter con un solo carattere numerico per lato e' un
forte indizio di TABELLA -- e' proprio la colonna dei numeri di riga -- e va
passato a chi rileva tabelle, non perso» -- ma non lo passava a nessuno.

**Perche' una misura e non un candidato.** Un `RegionCandidate` in piu' cambia
cio' che **ogni** consumer si trova davanti e obbliga a battezzare subito una
categoria che nessun consumer ha ancora chiesto. Una misura non cambia il
comportamento di nessuno: chi legge le bande vede esattamente le bande di prima.
Stesso precedente di Milestone 33, dove cio' che un candidato minimale non puo'
portare e' finito in una misura satellite.

**Cosa NON fa.** Non classifica, non ordina, non mette in relazione il corridoio
con nessun altro candidato. Che un corridoio dentro una tabella vada trattato
diversamente da uno dentro un rientro sospeso e' una decisione, e le decisioni
stanno in Resolution o nel consumer -- `AGENTS.MD` §Layout e candidati.
"""

from __future__ import annotations

from dataclasses import dataclass

from geometry_model import _validate_finite_number, _validate_non_empty_string


@dataclass(frozen=True, slots=True)
class RejectedGutter:
    """Un corridoio verticale che l'ammissione ha respinto, con il suo profilo.

    `left_chars_total` e `right_chars_total` sono i caratteri **sommati** sulle
    righe di fianco, non la loro mediana: e' la grandezza che distingue un lato
    vuoto (zero) da un lato che porta pochi caratteri veri, e nessuna delle due
    e' ricavabile dai campi che il candidato porta.

    `height_in_page_lines` e' l'altezza nell'unita' che usa il criterio
    `too_short`, cioe' l'interlinea mediana **della pagina**.

    `rejected_only_by_wordiness` dice se la mancanza di parole ai fianchi e'
    l'**unica** cosa fra questo corridoio e l'ammissione. Serve perche' il motivo
    di scarto e' il primo che scatta, non l'elenco di tutti quelli che
    scatterebbero: un corridoio senza parole puo' essere anche troppo basso, e
    chi legge solo l'etichetta non lo distinguerebbe.
    """

    page_id: str
    x0: float
    x1: float
    y0: float
    y1: float
    height_in_page_lines: float
    left_lines: int
    right_lines: int
    left_chars_total: int
    right_chars_total: int
    reject_reason: str
    rejected_only_by_wordiness: bool

    def __post_init__(self) -> None:
        _validate_non_empty_string(self.page_id, "page_id")
        for name in ("x0", "x1", "y0", "y1", "height_in_page_lines"):
            _validate_finite_number(getattr(self, name), name)
        if self.x1 <= self.x0:
            raise ValueError("x1 must be greater than x0")
        if self.y1 <= self.y0:
            raise ValueError("y1 must be greater than y0")
        if self.height_in_page_lines < 0.0:
            raise ValueError("height_in_page_lines must not be negative")
        for name in ("left_lines", "right_lines", "left_chars_total", "right_chars_total"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        # Un respinto senza motivo sarebbe uno scarto silenzioso registrato come
        # tale: e' esattamente cio' che questo modulo esiste per impedire.
        _validate_non_empty_string(self.reject_reason, "reject_reason")
        if not isinstance(self.rejected_only_by_wordiness, bool):
            raise ValueError("rejected_only_by_wordiness must be a boolean")
        if self.rejected_only_by_wordiness and self.reject_reason != "too_few_wordy_lines":
            raise ValueError(
                "rejected_only_by_wordiness requires reject_reason == 'too_few_wordy_lines'"
            )


def measure_rejected_gutters(
    page_id: str, rows: list[dict[str, object]]
) -> tuple[RejectedGutter, ...]:
    """I soli corridoi respinti fra quelli che il producer ha giudicato.

    Prende le righe di `column_band_gutter_rows` perche' e' li' che il verdetto
    vive: la misura non rigiudica niente e non torna sulle primitive. Un
    corridoio ammesso (`reject_reason` a `None`) e' gia' descritto dalla banda
    che ne nasce e non viene ripetuto qui.
    """

    _validate_non_empty_string(page_id, "page_id")
    misure: list[RejectedGutter] = []
    for row in rows:
        reason = row.get("reject_reason")
        if reason is None:
            continue
        if not isinstance(reason, str):
            raise ValueError("reject_reason must be a string or None")
        misure.append(
            RejectedGutter(
                page_id=page_id,
                x0=float(row["x0"]),  # type: ignore[arg-type]
                x1=float(row["x1"]),  # type: ignore[arg-type]
                y0=float(row["y0"]),  # type: ignore[arg-type]
                y1=float(row["y1"]),  # type: ignore[arg-type]
                height_in_page_lines=float(row["height_in_page_lines"]),  # type: ignore[arg-type]
                left_lines=int(row["left_lines"]),  # type: ignore[arg-type]
                right_lines=int(row["right_lines"]),  # type: ignore[arg-type]
                left_chars_total=int(row["left_chars_total"]),  # type: ignore[arg-type]
                right_chars_total=int(row["right_chars_total"]),  # type: ignore[arg-type]
                reject_reason=reason,
                rejected_only_by_wordiness=bool(row.get("rejected_only_by_wordiness", False)),
            )
        )
    return tuple(misure)
