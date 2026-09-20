"""Quali combinazioni di campi contano come scheda, per questo documento.

Policy di documento, nella forma di `heading_bands`: prende la misura e decide,
una volta per documento, e il risultato scende nelle pagine. Le due condizioni
sono quelle gia' misurate e non sono nuove:

**Ripetizione.** La combinazione deve comparire almeno tre volte. Non e' una
soglia nuova: e' quella che `repeated_structures` chiede gia' a una struttura
per esistere, applicata alla combinazione invece che all'insieme.

**Posizione.** Un solo profilo deve coprire la **maggioranza** delle occorrenze:
`Criterio_PosizioneRelativaDeiCampi_v1.md`, «non basta che ci siano, devono
essere nella stessa posizione relativa». Misurato su DB: i tre insiemi veri
hanno un profilo dominante su 16, 13 e 12 occorrenze; i numeri delle opzioni di
un D6 dentro le celle della tabella dei tesori hanno cinque profili distinti su
cinque occorrenze.

La regola vive in `stat_block_field_lines.stays_in_place`, e qui non si
riscrive: la strada vecchia e questa devono decidere allo stesso modo, altrimenti
confrontarle non dice niente.
"""

from __future__ import annotations

from dataclasses import dataclass

from document_stat_block_measurements import FieldCombinationMeasurements
from stat_block_field_lines import MINIMO_RIPETIZIONI, stays_in_place


@dataclass(frozen=True, slots=True)
class StatBlockFields:
    """Le combinazioni che, in questo documento, dichiarano una scheda."""

    combinations: frozenset[frozenset[str]]

    def carried_by(self, labels: frozenset[str]) -> bool:
        """La riga porta una combinazione ammessa.

        Contenimento e non uguaglianza: una riga che porta la combinazione
        **piu'** un'altra etichetta resta una riga di campi. Il contrario —
        accettare un pezzo della combinazione — e' cio' che fa entrare
        `movimento` da solo, che su Dragonbane e' anche una colonna di
        `ANIMALI COMUNI`."""

        return any(c <= labels for c in self.combinations)


def stat_block_fields(
    measurements: FieldCombinationMeasurements, *, minimo: int = MINIMO_RIPETIZIONI
) -> StatBlockFields:
    """Le combinazioni ripetute che stanno sempre nello stesso posto."""

    return StatBlockFields(
        combinations=frozenset(
            combinazione
            for combinazione, n in measurements.occurrences.items()
            if n >= minimo and stays_in_place(measurements.profiles[combinazione], n)
        )
    )
