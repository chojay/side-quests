"""Core data model.

Everything here is frozen. A rule must never be able to mutate the fit it is auditing,
which is what makes rule evaluation order irrelevant and the whole engine testable.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, fields
from enum import IntEnum, StrEnum

# Material classes that possess no density of states at the Fermi level, and therefore
# cannot physically exhibit Doniach-Sunjic asymmetry. A conductive oxide (RuO2, ITO)
# must be declared explicitly as "conductive-oxide" rather than "oxide".
INSULATING = frozenset({"insulator", "oxide", "polymer", "ceramic", "glass"})
METALLIC = frozenset({"metal", "graphitic", "conductive-oxide", "doped-semiconductor"})

# Doublet area ratios follow from the (2j+1) degeneracy of the two spin-orbit states.
# p: 4/2, d: 6/4, f: 8/6. Expressed as area(higher j) / area(lower j).
DOUBLET_RATIOS: dict[str, float] = {"p": 2.0, "d": 1.5, "f": 4.0 / 3.0}


class Tier(IntEnum):
    """Epistemic status of a rule. See docs/why-tiers.md."""

    ONE = 1
    TWO = 2
    THREE = 3

    def __str__(self) -> str:
        return f"T{self.value}"


class Outcome(StrEnum):
    """Five outcomes, not two.

    ``NOT_APPLICABLE`` and ``CANNOT_CHECK`` look similar and mean opposite things:
    the first is a complete answer, the second is an absent one. Merging them would
    corrupt the coverage figure, which is the entire point of this design.
    """

    PASS = "pass"
    FAIL = "fail"
    CANNOT_CHECK = "cannot-check"
    NOT_APPLICABLE = "not-applicable"
    PROMPT = "prompt"

    @property
    def counts_as_checked(self) -> bool:
        return self in (Outcome.PASS, Outcome.FAIL)

    @property
    def counts_as_uncovered(self) -> bool:
        return self is Outcome.CANNOT_CHECK


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PROMPT = "prompt"


@dataclass(frozen=True)
class Instrument:
    """Instrument response. Every field is Tier 2: knowable, but only by measuring it."""

    gaussian_width: float | None = None
    """Instrumental Gaussian FWHM in eV, at the working pass energy.

    Measure on Ag 3d5/2 (clean silver) or the Fermi edge. This is not a constant and
    not a literature value; it belongs to your spectrometer at your settings.
    """
    pass_energy: float | None = None
    source_linewidth: float | None = None
    transmission_function: str | None = None
    work_function: float | None = None
    """Sample work function in eV, from UPS. Required to reference to adventitious carbon."""

    def declared(self) -> frozenset[str]:
        return frozenset(
            f"instrument.{f.name}" for f in fields(self) if getattr(self, f.name) is not None
        )


@dataclass(frozen=True)
class ChargeReference:
    method: str
    """One of: adventitious_carbon, internal, fermi_edge, noble_metal_decoration."""
    value: float | None = None
    basis: str | None = None
    """Free text stating the calibration chain, e.g. 'Cu 2p3/2 = 932.67 eV'."""


@dataclass(frozen=True)
class Component:
    """One synthetic peak."""

    id: str
    element: str
    orbital: str
    binding_energy: float
    fwhm: float
    area: float
    lineshape: str = "voigt"
    """voigt | pseudo-voigt | gaussian | lorentzian | doniach-sunjic | dss."""
    gl_mix: float | None = None
    """Lorentzian fraction, 0.0 to 1.0."""
    asymmetry: float | None = None
    """Doniach-Sunjic singularity index alpha."""
    j: str | None = None
    doublet_partner: str | None = None
    assignment: str | None = None
    material_class: str | None = None

    @property
    def subshell(self) -> str:
        return self.orbital[-1].lower()

    @property
    def j_value(self) -> float | None:
        if self.j is None:
            return None
        num, _, den = self.j.partition("/")
        try:
            return float(num) / float(den) if den else float(num)
        except ValueError:
            return None

    @property
    def is_insulating(self) -> bool | None:
        """True for a known insulating class, False for a known metallic class, else None.

        None covers both an undeclared class and one that is in neither set (a typo, or
        an undoped "semiconductor"): a Tier 1 rule must not pass on a class it does not
        recognise.
        """
        if self.material_class is None:
            return None
        cls = self.material_class.lower()
        if cls in INSULATING:
            return True
        if cls in METALLIC:
            return False
        return None

    @property
    def transition(self) -> str:
        return f"{self.element} {self.orbital}"


@dataclass(frozen=True)
class Spectrum:
    name: str
    components: tuple[Component, ...] = ()
    background: str | None = None
    background_mode: str | None = None
    """static | active."""
    step_size: float | None = None
    charge_reference: ChargeReference | None = None
    quantified: bool = True
    """Whether component areas are used to derive atomic concentrations."""

    def component(self, cid: str) -> Component | None:
        return next((c for c in self.components if c.id == cid), None)

    def doublet_pairs(self) -> list[tuple[Component, Component]]:
        """Return (lower-j, higher-j) pairs, each pair yielded exactly once.

        When either component omits ``j``, the pair is ordered by binding energy: the
        lower-j state of a spin-orbit doublet lies at the higher binding energy. File
        order is never used, so listing the 3/2 line first cannot flip the ratio.
        """
        seen: set[frozenset[str]] = set()
        pairs: list[tuple[Component, Component]] = []
        for comp in self.components:
            if comp.doublet_partner is None:
                continue
            partner = self.component(comp.doublet_partner)
            if partner is None:
                continue
            key = frozenset({comp.id, partner.id})
            if key in seen:
                continue
            seen.add(key)
            a, b = comp, partner
            ja, jb = a.j_value, b.j_value
            if ja is not None and jb is not None:
                if ja > jb:
                    a, b = b, a
            elif a.binding_energy < b.binding_energy:
                a, b = b, a
            pairs.append((a, b))
        return pairs


@dataclass(frozen=True)
class FitResult:
    source: str
    spectra: tuple[Spectrum, ...] = ()
    instrument: Instrument = field(default_factory=Instrument)
    survey_elements: frozenset[str] = frozenset()

    def declared(self) -> frozenset[str]:
        keys = set(self.instrument.declared())
        if self.survey_elements:
            keys.add("survey.elements")
        return frozenset(keys)

    def components(self) -> Iterator[tuple[Spectrum, Component]]:
        for spectrum in self.spectra:
            for comp in spectrum.components:
                yield spectrum, comp


@dataclass(frozen=True)
class Diagnostic:
    code: str
    tier: Tier
    outcome: Outcome
    severity: Severity
    target: str
    message: str
    observed: str | None = None
    expected: str | None = None
    hint: str | None = None
    citation: str | None = None
