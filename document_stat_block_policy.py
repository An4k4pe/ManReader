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

import re
from collections.abc import Mapping
from dataclasses import dataclass

from document_stat_block_measurements import FieldCombinationMeasurements
from stat_block_field_lines import MINIMO_RIPETIZIONI, stays_in_place
from stat_block_regions import bound_label_groups_from_counts


@dataclass(frozen=True, slots=True)
class StatBlockFields:
    """Cio' che, in questo documento, dichiara una scheda.

    ``combinations`` sono le combinazioni su una riga della prima policy;
    ``nuclei`` sono i gruppi di etichette che il documento conta insieme
    (`Criterio_NucleoCheSiContaInsieme_v1.md`). Un blocco porta una scheda se
    contiene una combinazione, oppure due etichette dello stesso nucleo."""

    combinations: frozenset[frozenset[str]]
    nuclei: tuple[frozenset[str], ...] = ()

    @property
    def speaks(self) -> bool:
        """La policy ha qualcosa da dire su questo documento."""

        return bool(self.combinations or self.nuclei)

    def carried_by(self, labels: frozenset[str]) -> bool:
        """La riga porta una combinazione ammessa.

        Contenimento e non uguaglianza: una riga che porta la combinazione
        **piu'** un'altra etichetta resta una riga di campi. Il contrario —
        accettare un pezzo della combinazione — e' cio' che fa entrare
        `movimento` da solo, che su Dragonbane e' anche una colonna di
        `ANIMALI COMUNI`."""

        return any(c <= labels for c in self.combinations) or any(
            len(nucleo & labels) >= 2 for nucleo in self.nuclei
        )


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


def stat_block_nuclei(counts: Mapping[str, Mapping[int, int]]) -> StatBlockFields:
    """I nuclei di etichette dichiarate che il documento conta insieme.

    La regola non si riscrive: e' `bound_label_groups_from_counts`, la stessa di
    `_bound_label_groups` misurata il 14 settembre. Qui cambia solo che cosa si
    conta — le etichette **dichiarate** con i due punti — e che un nucleo deve
    avere almeno due etichette, perche' un'etichetta sola non e' una struttura:
    e' la cella `Versatile:` della tabella delle armi."""

    return StatBlockFields(
        combinations=frozenset(),
        nuclei=tuple(
            nucleo
            for nucleo in bound_label_groups_from_counts(counts)
            if len(nucleo) >= 2 and not is_a_scale(nucleo)
        ),
    )


_NUMERO_E_SEGNI = re.compile(r"[\d+\-/()#]")


def is_a_scale(nucleo: frozenset[str]) -> bool:
    """Il nucleo e' una **scala**: la stessa parola con un numero che cambia.

    `Criterio_NucleoCheSiContaInsieme_v2.md`. I campi di una scheda sono nomi
    diversi — `Ferocia`, `Taglia`, `Movimento`. `Rango 1:` … `Rango 4:` sono un
    campo solo, ripetuto con un grado che sale: su Dag idx 324 stanno impilati in
    una cella della colonna DANNO di una tabella di armi, e la v1 li prendeva per
    scheda. Lo stesso per i marcatori numerati `#1:` `#2:` `#3:` di Wilder.

    Tolti cifre e segni, le etichette di una scala si riducono a una sola radice."""

    return len({_NUMERO_E_SEGNI.sub("", etichetta) for etichetta in nucleo}) <= 1
