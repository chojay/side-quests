"""MOS-R proxy scoring from kinematic features.

The Motor Optimality Score - Revised (MOS-R) has five subscales:
  1. Fidgety quality
  2. Movement repertoire
  3. Movement character
  4. Postural patterns
  5. Age-adequate motor patterns

This module computes proxy scores for the first four from 2D pose kinematics.
The fifth (age-adequate) is not implemented because it requires a reference
database of typical age-matched movement patterns.

EVERY SCORE HERE IS A PROXY. Thresholds are initial heuristics based on
published GMA computer-vision literature (GigaScience 2024 UPenn/CHOP and
related). They would need recalibration against a professional GMA scoring
before being trusted for anything.

Output convention: each subscale has a score in 0..5 (higher = more optimal),
plus a confidence label HIGH/MODERATE/LOW for how reliable the proxy is.
A "global proxy" sums the available subscales for an at-a-glance number.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from gma_pipeline.features import VideoFeatures


SCORING_VERSION = "v0.2"


@dataclass
class SubscaleScore:
    """One MOS-R subscale proxy result."""

    subscale: str
    score_0_to_5: float
    confidence: str  # "HIGH" | "MODERATE" | "LOW" | "NOT_IMPLEMENTED"
    rationale: str
    inputs_used: dict[str, float] = field(default_factory=dict)


@dataclass
class AsymmetryFinding:
    """Asymmetry signal flagged per keypoint pair."""

    pair: str  # e.g. "left_wrist__vs__right_wrist"
    symmetry_index: float  # ratio left/right; 1.0 = symmetric
    flagged: bool  # True if outside normal range
    direction: str  # "left_dominant" | "right_dominant" | "symmetric"
    severity: str  # "mild" | "moderate" | "marked" | "none"


@dataclass
class ScoringResult:
    video_id: str
    scoring_version: str
    subscales: dict[str, SubscaleScore] = field(default_factory=dict)
    asymmetry_findings: list[AsymmetryFinding] = field(default_factory=list)
    global_proxy_score: float = 0.0
    interpretation: str = ""


def _clip(x: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, x)))


def _score_fidgety_quality(features: VideoFeatures) -> SubscaleScore:
    """Fidgety quality proxy. LOW confidence - see the caveats on each component.

    Canonical definition (Einspieler & Prechtl 2005, PMID 15856440): fidgety
    movements are "small movements of moderate speed with VARIABLE acceleration
    of neck, trunk, and limbs in all directions", continuous in the awake infant.
    Note they involve neck and trunk too, not only the four distal limbs, and are
    aperiodic/multidirectional (variable acceleration) - NOT smooth-and-periodic.

    This proxy combines four inputs, each with a known limitation:
    - detection rate: a WEAK continuity proxy - it measures whether the pose model
      found a body, not whether it moved; a still baby (the pathology this should
      catch) scores ~1.0. (Better: a limb-speed motion floor, as mos_r.py does.)
    - distal dominant frequency in the shared _FIDGETY_BAND: an UNVALIDATED
      low-frequency gate (no literature Hz exists for FMs); rewarding proximity to
      a sharp 2 Hz peak is conceptually backwards because a sharp peak signals
      abnormal (tremulous/monotonous) periodicity, not true aperiodic fidgety.
    - normalized jerk index: a MOVEMENT-CHARACTER (fluency) property, not part of
      the fidgety-presence definition; low jerk is not "more fidgety" (it can favour
      monotonous/poor-repertoire movement). NJI itself is noise- and
      normalization-sensitive (see features._normalized_jerk_index).
    - four-limb balance: normal FMs need NOT be symmetric across limbs; route
      focal asymmetry through the SEGMENTAL channel, not here.
    """
    inputs: dict[str, float] = {}
    score_components: list[float] = []

    diag = features.frame_diagonal_pixels or 1.0
    distal = ("left_wrist", "right_wrist", "left_ankle", "right_ankle")

    # Component 1: MOTION PRESENCE - do the distal limbs actually MOVE? (Replaces
    # detection-rate, which only measured whether a body was found, not whether it
    # moved - a perfectly still baby, the exact pathology, scored ~1.0 there.)
    present: list[float] = []
    for kp_name in distal:
        kk = features.keypoints.get(kp_name)
        if kk is None or not np.isfinite(kk.speed_mean):
            continue
        speed_norm = kk.speed_mean / diag
        inputs[f"{kp_name}_speed_norm"] = float(speed_norm)
        present.append(1.0 if speed_norm >= 0.02 else 0.0)  # 0.02 diag/s motion floor
    if present:
        score_components.append(float(np.mean(present)))

    # Component 2: in-band ENERGY FRACTION (robust; NOT a sharp-peak reward). How
    # much of the distal-limb movement energy sits in the low fidgety band, across
    # both axes - replaces the conceptually-backwards "proximity to a sharp 2 Hz
    # peak" reward (a sharp peak signals abnormal periodicity, not aperiodic fidgety).
    energy: list[float] = []
    for kp_name in distal:
        kk = features.keypoints.get(kp_name)
        if kk is None or not np.isfinite(kk.inband_energy_fraction):
            continue
        inputs[f"{kp_name}_inband_energy"] = float(kk.inband_energy_fraction)
        energy.append(kk.inband_energy_fraction)
    if energy:
        score_components.append(_clip(float(np.mean(energy)), 0.0, 1.0))

    # Component 3: trajectory CURVATURE (multidirectionality) - the literature's best
    # single fidgety discriminator (Kanemaru 2019, Phys Ther); true fidgety is curved/
    # multidirectional. Replaces the low-jerk reward (jerk is a movement-CHARACTER
    # property and low jerk can favour monotonous, poor-repertoire movement).
    # Scale-free = curvature (1/px) * frame diagonal; squash is an uncalibrated heuristic.
    curvs: list[float] = []
    for kp_name in distal:
        kk = features.keypoints.get(kp_name)
        if kk is None or not np.isfinite(kk.mean_curvature):
            continue
        inputs[f"{kp_name}_curvature"] = float(kk.mean_curvature)
        curvs.append(kk.mean_curvature)
    if curvs:
        med_curv_norm = float(np.median(curvs)) * diag
        score_components.append(_clip(med_curv_norm / 10.0, 0.0, 1.0))

    # Component 4: all four limbs have non-trivial movement
    speeds: list[float] = []
    for kp_name in ("left_wrist", "right_wrist", "left_ankle", "right_ankle"):
        if kp_name in features.keypoints:
            s = features.keypoints[kp_name].speed_mean
            if np.isfinite(s):
                speeds.append(s)
    if speeds:
        # Penalize if any limb is much quieter than the others
        min_speed = min(speeds)
        max_speed = max(speeds)
        balance = (min_speed / max_speed) if max_speed > 0 else 0.0
        inputs["limb_balance"] = float(balance)
        score_components.append(_clip(balance, 0.0, 1.0))

    if not score_components:
        return SubscaleScore("fidgety_quality", float("nan"), "LOW", "no inputs", inputs)
    raw = float(np.mean(score_components))
    return SubscaleScore(
        subscale="fidgety_quality",
        score_0_to_5=raw * 5.0,
        confidence="LOW",
        rationale=(
            "Heuristic blend of detection-continuity + distal dominant-frequency in an unvalidated low-frequency band "
            "+ jerk-smoothness + four-limb balance. LOW confidence: detection-rate does not measure movement, the "
            "frequency band has no literature Hz value (and a sharp peak is if anything abnormal), low jerk is a "
            "movement-character not a fidgety-presence property, and normal FMs need not be limb-symmetric. "
            "Reconciled with mos_r.py's LOW rating for the same construct (was mislabeled HIGH)."
        ),
        inputs_used=inputs,
    )


def _score_movement_repertoire(features: VideoFeatures) -> SubscaleScore:
    """Variety of movements across the recording.

    Higher entropy of velocity distributions per limb means more varied motion.
    """
    inputs: dict[str, float] = {}
    entropies: list[float] = []
    for kp_name, kk in features.keypoints.items():
        if np.isfinite(kk.velocity_entropy):
            entropies.append(kk.velocity_entropy)
            inputs[f"{kp_name}_velocity_entropy"] = float(kk.velocity_entropy)
    if not entropies:
        return SubscaleScore("movement_repertoire", float("nan"), "LOW", "no inputs", inputs)
    mean_entropy = float(np.mean(entropies))
    # Heuristic: entropy below 1.5 is monotone, above 3.0 is rich
    raw = _clip((mean_entropy - 1.5) / 1.5, 0.0, 1.0)
    return SubscaleScore(
        subscale="movement_repertoire",
        score_0_to_5=raw * 5.0,
        confidence="LOW",
        rationale=(
            "Mean Shannon entropy of per-keypoint SPEED-magnitude histograms - a descriptor of speed-distribution "
            "spread, NOT the clinical 'age-adequate movement repertoire' (variety of movement PATTERNS/postures/"
            "directions), which mos_r.py correctly marks NOT_COMPUTABLE from 2D pose. Direction is discarded and the "
            "bins are self-scaled. Treat as an exploratory descriptor only, not a repertoire score."
        ),
        inputs_used=inputs,
    )


def _score_movement_character(features: VideoFeatures) -> SubscaleScore:
    """Fluency and inter-limb coordination.

    Normal: independent or reciprocal limb movement (low / negative whole-body
    synchrony). Cramped-synchronized: limbs co-activate near-simultaneously
    in-phase (high positive synchrony) - the bad sign per Prechtl criteria.
    """
    sync = features.cramped_sync_index
    inputs = {"cramped_sync_index": float(sync)} if np.isfinite(sync) else {}
    if not np.isfinite(sync):
        return SubscaleScore("movement_character", float("nan"), "LOW", "no whole-body synchrony available", inputs)
    # Higher (positive) synchrony = more cramped-synchronized = lower score. A
    # moderate positive baseline (~0.3-0.5, shared activity level) is normal; only
    # near-unity synchrony is the CS signature, so the penalty starts at 0.55.
    raw = _clip(1.0 - max(0.0, sync - 0.55) / 0.35, 0.0, 1.0)
    return SubscaleScore(
        subscale="movement_character",
        score_0_to_5=raw * 5.0,
        confidence="LOW",
        rationale=(
            f"Whole-body cramped-sync index (SIGNED, zero-lag speed-envelope correlation across all limb pairs) "
            f"= {sync:+.2f}; positive = in-phase co-activation (cramped-synchronized direction). Fixed metric (signed, "
            "zero-lag, cross-limb) separates in-phase CS from normal anti-phase reciprocal movement. LOW confidence: "
            "captures co-timing (the 'synchronized' half), not rigidity/loss-of-fluency (the 'cramped' half); "
            "uncalibrated thresholds. Cross-check against clinical scoring."
        ),
        inputs_used=inputs,
    )


def _score_postural_patterns(features: VideoFeatures) -> SubscaleScore:
    """Trunk midline stability (very limited from 2D pose).

    Proxy: combined position spread of shoulders and hips (relative to frame
    diagonal). Lower = more stable trunk. We explicitly flag this as LOW
    confidence because true postural assessment needs 3D.
    """
    inputs: dict[str, float] = {}
    spreads: list[float] = []
    for kp_name in ("left_shoulder", "right_shoulder", "left_hip", "right_hip"):
        if kp_name in features.keypoints:
            s = features.keypoints[kp_name].position_std_norm
            if np.isfinite(s):
                spreads.append(s)
                inputs[f"{kp_name}_position_std_norm"] = float(s)
    if not spreads:
        return SubscaleScore("postural_patterns", float("nan"), "LOW", "no inputs", inputs)
    mean_spread = float(np.mean(spreads))
    # Heuristic: spread below 0.03 (3 percent of frame diagonal) = stable
    raw = _clip(1.0 - (mean_spread - 0.02) / 0.06, 0.0, 1.0)
    return SubscaleScore(
        subscale="postural_patterns",
        score_0_to_5=raw * 5.0,
        confidence="LOW",
        rationale="Shoulder + hip position spread as a 2D proxy for trunk stability",
        inputs_used=inputs,
    )


def _score_age_adequate() -> SubscaleScore:
    return SubscaleScore(
        subscale="age_adequate_motor_patterns",
        score_0_to_5=float("nan"),
        confidence="NOT_IMPLEMENTED",
        rationale="Requires reference database keyed to corrected age",
    )


def _classify_asymmetry(ss) -> AsymmetryFinding:
    """Translate a SymmetryStats to a flagged finding."""
    si = ss.speed_symmetry_index
    if not np.isfinite(si):
        return AsymmetryFinding(
            pair=f"{ss.pair_left}__vs__{ss.pair_right}",
            symmetry_index=float("nan"),
            flagged=False,
            direction="symmetric",
            severity="none",
        )
    # 1.0 = perfectly symmetric. Below 0.8 or above 1.25 = asymmetric.
    flagged = si < 0.8 or si > 1.25
    if 0.95 <= si <= 1.05:
        severity = "none"
        direction = "symmetric"
    elif 0.8 <= si < 0.95 or 1.05 < si <= 1.25:
        severity = "mild"
        direction = "left_dominant" if si > 1.0 else "right_dominant"
    elif 0.65 <= si < 0.8 or 1.25 < si <= 1.5:
        severity = "moderate"
        direction = "left_dominant" if si > 1.0 else "right_dominant"
    else:
        severity = "marked"
        direction = "left_dominant" if si > 1.0 else "right_dominant"
    return AsymmetryFinding(
        pair=f"{ss.pair_left}__vs__{ss.pair_right}",
        symmetry_index=float(si),
        flagged=flagged,
        direction=direction,
        severity=severity,
    )


def _interpret(result: ScoringResult, features: VideoFeatures) -> str:
    """Plain-language interpretation summary."""
    pieces: list[str] = []

    fq = result.subscales.get("fidgety_quality")
    if fq and np.isfinite(fq.score_0_to_5):
        if fq.score_0_to_5 >= 4.0:
            pieces.append(
                "Fidgety-quality proxy is in the upper-normal range. Continuous low-amplitude "
                "movement was detected across all four limbs with smoothness and a dominant "
                "frequency near the expected fidgety band."
            )
        elif fq.score_0_to_5 >= 2.5:
            pieces.append(
                "Fidgety-quality proxy is in a mid range. Some inputs (continuity, frequency, "
                "smoothness, limb balance) are below the upper-normal heuristic threshold."
            )
        else:
            pieces.append(
                "Fidgety-quality proxy is in the lower range. Multiple inputs are atypical "
                "relative to the heuristic upper-normal targets."
            )

    mc = result.subscales.get("movement_character")
    if mc and np.isfinite(mc.score_0_to_5):
        if mc.score_0_to_5 >= 4.0:
            pieces.append(
                "Inter-limb cross-correlation is in the typical range, no cramped-synchronized signal."
            )
        elif mc.score_0_to_5 < 2.0:
            pieces.append(
                "Inter-limb cross-correlation is elevated across pairs, which is the signal direction "
                "associated with cramped-synchronized patterns in the GMA literature. Cross-check "
                "against a professional clinical scoring before treating this as meaningful."
            )

    asym_flagged = [a for a in result.asymmetry_findings if a.flagged]
    if asym_flagged:
        pairs = ", ".join(f"{a.pair} (SI {a.symmetry_index:.2f})" for a in asym_flagged)
        pieces.append(
            f"Raw symmetry-index band flags: {pairs}. NOTE: raw |SI| magnitude is NOT diagnostic - "
            "benign asymmetry in a clinically normal limb can match the magnitude seen in a genuinely affected limb. "
            "See the segmental-asymmetry analysis for the pipeline's own per-keypoint assessment."
        )
    else:
        pieces.append("No paired-limb asymmetries crossed the raw-SI band (which is not diagnostic on its own).")

    pieces.append(
        "EVERY NUMBER IS A PROXY. This is exploratory pattern observation, not a clinical GMA score. The "
        "headline is the segmental-asymmetry analysis; "
        "final interpretation rests with the clinical care team."
    )
    return " ".join(pieces)


def score_video(features: VideoFeatures) -> ScoringResult:
    result = ScoringResult(video_id=features.video_id, scoring_version=SCORING_VERSION)
    result.subscales["fidgety_quality"] = _score_fidgety_quality(features)
    result.subscales["movement_repertoire"] = _score_movement_repertoire(features)
    result.subscales["movement_character"] = _score_movement_character(features)
    result.subscales["postural_patterns"] = _score_postural_patterns(features)
    result.subscales["age_adequate_motor_patterns"] = _score_age_adequate()

    operational = [s.score_0_to_5 for s in result.subscales.values() if np.isfinite(s.score_0_to_5)]
    result.global_proxy_score = float(np.sum(operational)) if operational else 0.0

    for ss in features.symmetry.values():
        result.asymmetry_findings.append(_classify_asymmetry(ss))
    result.interpretation = _interpret(result, features)
    return result


def write_scoring_json(result: ScoringResult, path: Path) -> None:
    payload = {
        "video_id": result.video_id,
        "scoring_version": result.scoring_version,
        "global_proxy_score": result.global_proxy_score,
        "subscales": {name: asdict(s) for name, s in result.subscales.items()},
        "asymmetry_findings": [asdict(a) for a in result.asymmetry_findings],
        "interpretation": result.interpretation,
    }
    path.write_text(json.dumps(payload, indent=2))
