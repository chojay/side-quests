"""MOS-R (Motor Optimality Score - Revised) PROXY + clinical calibration.

EVERY NUMBER HERE IS A PROXY. This module does NOT produce a clinical MOS-R.
It produces an explicitly-labeled, honest proxy of the subset of the MOS-R that
single-camera 2D pose kinematics can even partially address. The companion
calibration.py produces a 2D-pose-derived per-limb SEGMENTAL-ASYMMETRY signal
and can compare it with an external clinician reading, if one is transcribed
into the PT_ASSESSMENT placeholder below.

Not a GMA. Prechtl's General Movements Assessment is by definition a whole-body
visual-Gestalt method: a trained observer judges the OVERALL quality (complexity,
variation, fluency, and global fidgety presence "in all parts of the body") - it
is NOT the status of individual joints/keypoints, and no validated per-keypoint
GMA instrument exists (Einspieler & Prechtl 2005, PMID 15856440). The per-limb
segmental-asymmetry map here is a legitimate DERIVED kinematic sign that can
INFORM, but is not itself, a GMA.

Why a proxy and not a score
---------------------------
The real MOS-R (Einspieler et al. 2019, J Clin Med 8(10):1616) sums five
subscales to a total of 5..28:

  F  - Fidgety movements                12 / 4 / 1   (most heavily weighted)
  P  - Observed movement patterns        4 / 2 / 1
  R  - Age-adequate movement repertoire  4 / 2 / 1
  Po - Observed postural patterns        4 / 2 / 1
  C  - Movement character                4 / 2 / 1

Of these, only F and C are even *partially* derivable from a 13-keypoint 2D
skeleton; P, R and Po require human Gestalt perception, an age-keyed normative
reference, and finger-level posture detail that a 13-keypoint skeleton does not
capture. So the maximum points this pipeline can address is F(12) + C(4) = 16
of 28. The other 12 points are clinician-only.

Design (per the MOS-R research synthesis)
-----------------------------------------
1. Compute proxies ONLY for F and C; mark P, R, Po NOT_COMPUTABLE.
2. Report two totals:
     - computable proxy out of 16 (F + C only),
     - an explicit UPPER BOUND out of 28 where P, R, Po are imputed at their
       CEILING (4/4/4). The true MOS-R is <= this number by an unknown margin;
       only a certified assessor can fill the missing 12 points. We never impute
       the middle/low values (that would fabricate pathology).
3. A focal one-limb deficit must NOT crush the whole-body F subscale. Keeping F
   (a whole-body Gestalt subscale) high when fidgety is globally present (e.g.
   3/4 limbs normal) is faithful to how F is scored. A focal single-limb finding
   is carried instead by the segmental-asymmetry channel: segmental movement
   asymmetry was PRESENT in 91.7% (22/24) of perinatal-stroke infants
   (Bertoncelli 2024) - a prevalence among affected infants, NOT a CP-detection
   sensitivity.

   BUT this must not read as reassuring. A genuinely CP-heralding unilateral
   deficit normally DRAGS the true MOS-R total DOWN (character, posture and
   repertoire all degrade): perinatal-stroke infants who developed unilateral CP
   had a median MOS-R of 6, vs 26 in controls (Bertoncelli 2024). So a
   near-normal 2D-proxy total more likely reflects the proxy's BLINDNESS to
   those channels than reassurance, and a focal fidgety-age asymmetry is itself
   an established early marker of a unilateral brain lesion / congenital
   hemiplegic CP (Guzzetta 2003, PMID 12776225). The segmental-asymmetry channel,
   not the F/upper-bound total, is the headline.

Final scoring rests with a certified GMA assessor.

Key references: Einspieler et al. 2019, J Clin Med 8(10):1616 (MOS-R instrument);
Bertoncelli et al. 2024, Children 11(8):940 (perinatal-stroke MOS-R cutoffs).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from gma_pipeline.features import VideoFeatures


MOSR_PROXY_VERSION = "v0.2"


# ---------------------------------------------------------------------------
# External clinician assessment - USER-FILLABLE PLACEHOLDER (empty by default).
#
# If a trained GMA assessor has read your recordings, transcribe the reading
# here: scorer, date, the verbatim categorical reading, and per-keypoint
# "normal"/"abnormal" labels for the 12 paired keypoints. calibration.py then
# shows a side-by-side coincidence count. The pipeline's own assessment
# (calibration.py) is INDEPENDENT and is NEVER calibrated to or graded against
# this dict; it is carried only as a clearly-labeled side-note.
#
# TERMINOLOGY NOTE for transcription: "poor repertoire" is formally one of the
# four WRITHING-period whole-body GM categories (normal / poor-repertoire /
# cramped-synchronized / chaotic), assessed term to ~6-9 weeks, and is never a
# per-limb label. In the fidgety period the standard nomenclature is normal /
# absent / abnormal(exaggerated) fidgety plus MOS-R subscale descriptors. Keep
# any clinician quote verbatim, but do NOT treat writhing-period category names
# as fidgety-stage or per-limb GMA categories in scoring logic (Einspieler &
# Prechtl 2005, PMID 15856440).
#
# TIMING NOTE: the fidgety window opens ~6-9 wk, is OPTIMAL 12-16 wk, remains
# valid to ~20 wk, and FMs normally fade/disappear 18-20 wk as antigravity
# movements emerge (Ferrari et al. 2016, Early Hum Dev 103:219-224, PMID 27825041).
# Window validity is keyed to corrected age AT RECORDING, not the scoring date.
# ---------------------------------------------------------------------------
PT_ASSESSMENT = {
    "scorer": None,  # e.g. "<clinician name>, PT"
    "date": None,  # ISO date of the clinical scoring, if any
    "corrected_age_weeks": None,  # corrected age at recording, if known
    "provisional": True,  # any transcribed reading is a side-note, not a reference standard
    "provisional_note": (
        "Placeholder: no external clinician reading has been transcribed. Fill this dict in to see a "
        "side-by-side comparison; the pipeline's own assessment is independent of it either way."
    ),
    "categorical": None,  # verbatim clinical reading goes here, if available
    "labels": {
        "right_shoulder": None,
        "right_elbow": None,
        "right_wrist": None,
        "left_shoulder": None,
        "left_elbow": None,
        "left_wrist": None,
        "left_hip": None,
        "right_hip": None,
        "left_knee": None,
        "right_knee": None,
        "left_ankle": None,
        "right_ankle": None,
    },
}


# Population-specific MOS-R cutoffs (for context only; this proxy is not a MOS-R).
POPULATION_CUTOFFS = [
    {
        "population": "General optimality bands (MOS-R)",
        "threshold": "25-28 optimal; 20-24 mildly reduced; 9-19 moderately reduced; 5-8 severely reduced",
        "note": "Descriptive bands over the full 5-28 range; common binary collapse 20-28 lower-risk vs 5-19 higher-risk.",
        "source": "Einspieler et al. 2019, J Clin Med 8(10):1616",
    },
    {
        "population": "Perinatal arterial stroke / unilateral injury",
        "threshold": "MOS-R <= 13",
        "note": (
            "100% sens & spec for unilateral CP (GMFCS>=2); segmental asymmetry present in 91.7% (22/24). "
            "Wide CI: 24 stroke cases of 48 enrolled; specificity CI floor ~30.5%, so 100% spec is NOT robust. "
            "DIRECTION OF BIAS: this cutoff is from a near-obligate-CP cohort (~87.5% developed unilateral CP), so "
            "applied outside that etiology it is at best a conservative upper-bound context number, not a "
            "calibrated risk estimate."
        ),
        "source": "Bertoncelli et al. 2024, Children 11(8):940 (PMC11352565)",
    },
    {
        "population": "Very preterm (2-year outcome)",
        "threshold": "MOS-R <= 23 general impairment; <= 15 definite CP",
        "note": "<=15: 100% sens / 95% spec for definite CP; median 24 (IQR 21-26) in very preterm (n=169).",
        "source": "Kwong AK-L, et al. 2022, J Clin Med 11(7):1833 (PMC9000187)",
    },
    {
        "population": "Malformation of cortical development (NO validated cutoff)",
        "threshold": "no MOS-R cutoff exists",
        "note": "Descriptive only (n=9): abnormal GMs in all, poor repertoire universal. Literature context, not thresholding.",
        "source": "Ferrari F, Prechtl HFR, Cioni G, et al. 1997, Early Hum Dev 50(1):87-113 (PMID 9467696)",
    },
]


# Distal markers per limb (most reliable fidgety-frequency carriers in 2D pose).
_LIMB_DISTAL = {
    "left_arm": "left_wrist",
    "right_arm": "right_wrist",
    "left_leg": "left_ankle",
    "right_leg": "right_ankle",
}
_LIMB_PROXIMAL = {
    "left_arm": "left_elbow",
    "right_arm": "right_elbow",
    "left_leg": "left_knee",
    "right_leg": "right_knee",
}

# Fidgety-ish dominant-frequency band (Hz) for the distal marker. UNVALIDATED
# HEURISTIC, not a literature value: no primary GMA source (Prechtl, Einspieler,
# Hadders-Algra) assigns any Hz to fidgety movements - they are defined
# qualitatively as "small movements of moderate speed with VARIABLE acceleration
# ... in all directions" (Einspieler & Prechtl 2005, PMID 15856440). Because true
# FMs are aperiodic/broadband, a SHARP spectral peak is if anything a sign of
# abnormal (tremulous/monotonous) movement; this band is only a coarse
# low-frequency-energy gate, and 2D pose cannot certify true fidgety. This
# constant is the single shared band both this module and scoring.py use.
_FIDGETY_BAND = (1.0, 4.0)
# Non-trivial motion floor for the distal marker, in frame-diagonals/second.
_MOTION_FLOOR_NORM = 0.02
# Minimum detection fraction for a limb to count as "continuously present".
_MIN_DETECTION = 0.5


@dataclass
class MOSRSubscale:
    code: str  # "F" | "P" | "R" | "Po" | "C"
    name: str
    max_points: int
    points: float | None  # None => NOT_COMPUTABLE (clinician-only)
    computable: str  # "partial" | "no"
    confidence: str  # "LOW" | "MODERATE" | "NOT_COMPUTABLE"
    rationale: str
    detail: dict = field(default_factory=dict)


@dataclass
class MOSRProxy:
    video_id: str
    version: str
    subscales: dict[str, MOSRSubscale]
    computable_total: float  # F + C
    computable_max: int  # 16
    upper_bound_28: float  # F + C + ceiling(P,R,Po)=4+4+4
    repertoire_richness_descriptor: float  # mean velocity entropy, NOT a P/R score
    interpretation: str


def _limb_fidgety_state(features: VideoFeatures, limb: str) -> dict:
    """Per-limb fidgety presence/quality from the distal marker kinematics."""
    distal = _LIMB_DISTAL[limb]
    kk = features.keypoints.get(distal)
    diag = features.frame_diagonal_pixels or 1.0
    out = {
        "limb": limb,
        "distal": distal,
        "present": False,
        "quality": "absent",
        "speed_norm": float("nan"),
        "dom_freq_hz": float("nan"),
        "detection": float("nan"),
    }
    if kk is None or not np.isfinite(kk.speed_mean):
        return out
    speed_norm = kk.speed_mean / diag
    out["speed_norm"] = float(speed_norm)
    out["dom_freq_hz"] = float(kk.dominant_freq_hz)
    out["detection"] = float(kk.fraction_valid)
    present = (kk.fraction_valid >= _MIN_DETECTION) and (speed_norm >= _MOTION_FLOOR_NORM)
    out["present"] = bool(present)
    if not present:
        out["quality"] = "absent"
        return out
    in_band = np.isfinite(kk.dominant_freq_hz) and (_FIDGETY_BAND[0] <= kk.dominant_freq_hz <= _FIDGETY_BAND[1])
    out["quality"] = "present_normal" if in_band else "present_reduced"
    return out


def _score_fidgety(features: VideoFeatures) -> MOSRSubscale:
    """F proxy (12/4/1). Whole-body: not crushed by a single focal limb deficit."""
    limbs = {limb: _limb_fidgety_state(features, limb) for limb in _LIMB_DISTAL}
    n_present_normal = sum(1 for s in limbs.values() if s["quality"] == "present_normal")
    n_present = sum(1 for s in limbs.values() if s["present"])

    if n_present_normal >= 3:
        points = 12.0
        verdict = "fidgety present and continuous in 3+ of 4 limbs with in-band oscillation"
    elif n_present >= 2:
        points = 4.0
        verdict = "fidgety present but reduced/exaggerated or out-of-band in most limbs"
    else:
        points = 1.0
        verdict = "fidgety effectively absent in most limbs"

    reduced = [s["limb"] for s in limbs.values() if s["quality"] == "present_reduced"]
    rationale = (
        f"Per-limb distal-marker fidgety proxy: {n_present_normal}/4 limbs present+in-band -> F~{points:g}. "
        f"{verdict}. PROXY only - 2D pose cannot certify that detected oscillation IS true fidgety; "
        "the global total is deliberately NOT reduced for a focal single-limb deficit (that is carried "
        "by the segmental asymmetry channel)."
    )
    if reduced:
        rationale += f" Limbs with out-of-band/reduced distal signal: {', '.join(reduced)}."
    return MOSRSubscale(
        code="F",
        name="Fidgety movements",
        max_points=12,
        points=points,
        computable="partial",
        confidence="LOW",
        rationale=rationale,
        detail={k: v for k, v in limbs.items()},
    )


def _score_character(features: VideoFeatures) -> MOSRSubscale:
    """C proxy (4/2/1). Cramped-synchronized = high SIGNED, ZERO-LAG whole-body
    speed-envelope synchrony (limbs co-activate simultaneously, in phase)."""
    sync = features.cramped_sync_index
    if not np.isfinite(sync):
        return MOSRSubscale("C", "Movement character", 4, None, "partial", "NOT_COMPUTABLE",
                            "No whole-body synchrony available.", {})
    # Official MOS-R Movement Character tiers: smooth/fluent (4); "abnormal, but not
    # cramped-synchronised" (2); abnormal AND cramped-synchronised (1). Thresholds
    # on the signed synchrony index are UNCALIBRATED heuristics. Cramped-synchronized
    # is NEAR-simultaneous whole-body co-contraction, so it requires synchrony near
    # UNITY; a moderate positive baseline (~0.3-0.5, from shared overall activity
    # level - limbs quiet together then active together) is EXPECTED and is not CS.
    if sync >= 0.75:
        points, verdict = 1.0, "near-simultaneous whole-body co-activation (cramped-synchronized signature)"
    elif sync >= 0.55:
        points, verdict = 2.0, "abnormal, but not cramped-synchronised (elevated in-phase synchrony)"
    else:
        points, verdict = 4.0, "smooth/fluent - low/moderate (shared-activity baseline) or reciprocal synchrony, no CS pattern"
    return MOSRSubscale(
        code="C",
        name="Movement character",
        max_points=4,
        points=points,
        computable="partial",
        confidence="LOW",
        rationale=(
            f"Whole-body cramped-sync index (mean SIGNED zero-lag speed-envelope correlation across all limb pairs, "
            f"homologous + cross-limb) = {sync:+.2f} -> C~{points:g}: {verdict}. FIXED metric: signed + zero-lag + "
            f"cross-limb distinguishes in-phase cramped-synchronized (positive) from normal ANTI-phase reciprocal "
            f"movement (<=0), which the old |xcorr|-at-any-lag conflated. Still a PROXY: it captures co-TIMING (the "
            f"'synchronized' half) but not rigidity/loss-of-fluency (the 'cramped' half). Character remains a Gestalt."
        ),
        detail={"cramped_sync_index": sync},
    )


def _not_computable(code: str, name: str, max_points: int, why: str) -> MOSRSubscale:
    return MOSRSubscale(code, name, max_points, None, "no", "NOT_COMPUTABLE", why, {})


def compute_mosr_proxy(features: VideoFeatures) -> MOSRProxy:
    """Compute the honest MOS-R PROXY for one video."""
    f = _score_fidgety(features)
    c = _score_character(features)
    p = _not_computable(
        "P", "Observed movement patterns", 4,
        "Requires recognizing/counting a named catalogue of typical vs atypical age-specific patterns "
        "(hand-to-mouth, midline hand-to-hand, antigravity leg lift, etc.) - a Gestalt task a 13-keypoint 2D skeleton cannot do.",
    )
    r = _not_computable(
        "R", "Age-adequate movement repertoire", 4,
        "Requires an age-keyed normative database of expected patterns. Clinician-only.",
    )
    po = _not_computable(
        "Po", "Observed postural patterns", 4,
        "Requires finger posture (absent in a 13-keypoint skeleton) and depth/Gestalt judgement of neck/trunk posture typicality.",
    )

    subscales = {"F": f, "P": p, "R": r, "Po": po, "C": c}
    computable_total = (f.points or 0.0) + (c.points or 0.0)
    computable_max = f.max_points + c.max_points  # 16
    # Upper bound: impute the 3 non-computable subscales at CEILING (4 each).
    upper_bound_28 = computable_total + p.max_points + r.max_points + po.max_points

    entropies = [kk.velocity_entropy for kk in features.keypoints.values() if np.isfinite(kk.velocity_entropy)]
    repertoire = float(np.mean(entropies)) if entropies else float("nan")

    interpretation = (
        f"MOS-R PROXY (exploratory, non-clinical). Computable proxy F+C = {computable_total:g} of {computable_max} "
        f"(F={f.points:g}/12, C={c.points:g}/4). Observed-patterns (P), age-adequate-repertoire (R) and postural (Po) "
        f"are NOT computable from 2D pose and are clinician-only. UPPER BOUND on the full MOS-R = {upper_bound_28:g}/28 "
        f"(P/R/Po imputed at ceiling 4/4/4); the true MOS-R is <= this by an unknown margin and only a certified "
        f"assessor can fill the missing 12 points. The upper bound's nominal '{_band(upper_bound_28)}' band is NOT "
        f"reassurance: a near-normal proxy total more likely reflects this proxy's BLINDNESS to the P/R/Po/character "
        f"channels than a normal infant - a genuinely CP-heralding unilateral deficit normally DRAGS the true MOS-R "
        f"down (perinatal-stroke->unilateral-CP median MOS-R was 6, not near-normal; Bertoncelli 2024). GUARDRAIL: do "
        f"not read a high F or a high upper bound as 'normal/reassuring' while a limb is flagged abnormal in the "
        f"SEGMENTAL ASYMMETRY analysis - that per-limb map, not this total, is the headline."
    )

    return MOSRProxy(
        video_id=features.video_id,
        version=MOSR_PROXY_VERSION,
        subscales=subscales,
        computable_total=computable_total,
        computable_max=computable_max,
        upper_bound_28=upper_bound_28,
        repertoire_richness_descriptor=repertoire,
        interpretation=interpretation,
    )


def _band(total: float) -> str:
    if total >= 25:
        return "optimal (25-28)"
    if total >= 20:
        return "mildly reduced (20-24)"
    if total >= 9:
        return "moderately reduced (9-19)"
    return "severely reduced (5-8)"


def mosr_proxy_to_dict(proxy: MOSRProxy) -> dict:
    return {
        "video_id": proxy.video_id,
        "version": proxy.version,
        "computable_total": proxy.computable_total,
        "computable_max": proxy.computable_max,
        "upper_bound_28": proxy.upper_bound_28,
        "repertoire_richness_descriptor": proxy.repertoire_richness_descriptor,
        "interpretation": proxy.interpretation,
        "subscales": {k: asdict(v) for k, v in proxy.subscales.items()},
    }
