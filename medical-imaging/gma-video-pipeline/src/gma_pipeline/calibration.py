"""Segmental asymmetry - the pipeline's OWN independent, relative assessment.

INDEPENDENT. This assessment is derived purely from the infant's own pose
kinematics by comparing each limb to (a) its contralateral pair and (b) the
distribution across all 12 paired keypoints. It is NOT calibrated to, and does
not depend on, any external reading. An optional transcribed clinician reading
(PT_ASSESSMENT in mos_r.py, empty by default) is carried ONLY as a separate,
clearly-labeled side comparison - it is NOT a ground truth and NOT a
calibration target.

RELATIVE. This is a single infant with no normative database, so every signal is
within-subject and relative - there is no absolute "normal" here. The HEADLINE is
a RANKING of how much each keypoint stands out as BOTH (i) consistently slower than
its contralateral pair AND (ii) lower in movement variety than the infant's own
other limbs, with effect sizes and cross-video consistency. A conservative,
heavily-caveated BINARY FLAG additionally marks the keypoints that stand out most.

Two relative signals per keypoint
---------------------------------
1. Contralateral speed deficit: the speed Symmetry Index (SI = left_speed /
   right_speed) per video gives, for each keypoint, how much SLOWER it is than its
   own left/right partner (contralateral_deficit_pct; positive = this side slower).
   "Consistent" = slower in EVERY video.
2. Movement variety: mean velocity entropy, expressed as a PERCENTILE among the 12
   paired keypoints (low percentile = this limb moves less variably than its peers).

standout_score in [0,1] = mean of (a) the keypoint's rank by contralateral speed
deficit and (b) its rank by LOW variety. Keypoints are ranked by standout_score;
the binary flag fires only on the conjunction (consistent contralateral deficit AND
bottom-tertile variety). A benign asymmetry is slow WITHOUT a variety loss; a
reduced-repertoire limb is slow AND impoverished.

LIMITATIONS (read before trusting anything here):
- n=3 videos, single subject; EXPLORATORY, not a validated detector.
- No normative database: the "bottom tertile" variety cutoff and the ranking are
  WITHIN-SUBJECT relative, not absolute/normal - they describe how this infant's
  limbs compare to EACH OTHER, nothing more.
- 2D pixel-speed CAMERA-OBLIQUITY confound: SI is a ratio of projected pixel speeds;
  a fixed oblique camera can manufacture a left/right speed difference from geometry
  alone, and cross-video consistency does not exclude a habitual filming orientation.
  A foreshortening indicator (bi-acromial/bi-iliac width L/R balance) would help.
- The two signals partly CO-VARY (velocity entropy uses self-scaled speed bins, so a
  slower limb tends toward lower entropy) - treat "both fired" as weaker than two
  fully-independent signals would be.
- NOT a GMA (a whole-body Gestalt method); this is a derived kinematic SIGN.
Final interpretation rests with the care team.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from gma_pipeline.features import PAIRED_KEYPOINTS, VideoFeatures
from gma_pipeline.mos_r import PT_ASSESSMENT


SEGMENTAL_VERSION = "v0.3-independent-relative"

# Bottom-tertile percentile for the low-variety (reduced-repertoire) condition.
ENTROPY_TERTILE_PCT = 33.333


@dataclass
class SegmentalFinding:
    keypoint: str
    side: str  # "left" | "right"
    joint: str  # shoulder | elbow | wrist | hip | knee | ankle
    # Contralateral speed asymmetry (relative to this keypoint's own pair).
    si_by_video: dict[str, float]
    si_median: float
    contralateral_deficit_pct: float  # median % slower than pair (positive = this side slower)
    deficit_consistent_videos: int  # how many videos show this side slower
    n_videos_with_si: int
    consistent_speed_deficit: bool  # slower in EVERY video
    # Movement variety (relative to the infant's other limbs).
    mean_velocity_entropy: float
    entropy_percentile: float  # 0..1 among the 12 keypoints (low = low variety)
    low_variety: bool  # bottom-tertile of this infant's limbs
    # Independent standout ranking (the headline).
    standout_score: float  # 0..1 composite (slow-vs-pair AND low-variety-vs-peers)
    standout_rank: int  # 1 = stands out most
    pipeline_flag: bool  # caveated binary flag: consistent deficit AND low variety
    # PROVISIONAL PT comparison (side-note only; NOT ground truth, NOT calibration).
    pt_assessment_provisional: str | None
    pt_agreement_provisional: bool | None


@dataclass
class SegmentalAnalysis:
    version: str
    videos: list[str]
    entropy_threshold: float
    findings: list[SegmentalFinding]  # ranked by standout_score, descending
    pipeline_flagged: list[str]  # keypoints the pipeline's own binary flag fires on
    ranking_summary: str  # the RELATIVE headline (independent)
    flag_summary: str  # the caveated binary-flag summary (independent)
    independence_note: str
    # Provisional PT side-note (clearly NOT ground truth).
    pt_provisional_flagged: list[str]
    pt_provisional_agreement: dict[str, int]  # both_flag, both_clear, pipeline_only, pt_only
    pt_provisional_summary: str
    notes: str


def _joint_of(keypoint: str) -> str:
    return keypoint.split("_", 1)[1]


def _rank01(values: dict[str, float], key: str, higher_is_more: bool = True) -> float:
    """Fraction of finite values that `values[key]` is >= (or <=) - a 0..1 rank."""
    v = values.get(key)
    finite = [x for x in values.values() if np.isfinite(x)]
    if not np.isfinite(v) or not finite:
        return float("nan")
    if higher_is_more:
        return float(sum(1 for x in finite if x <= v) / len(finite))
    return float(sum(1 for x in finite if x >= v) / len(finite))


def analyze_segmental_asymmetry(features_by_video: dict[str, VideoFeatures]) -> SegmentalAnalysis:
    """Run the independent, relative per-limb assessment across all videos."""
    videos = list(features_by_video.keys())
    paired = list(PAIRED_KEYPOINTS)
    keypoints = [kp for pair in paired for kp in pair]

    # Mean velocity entropy per keypoint across videos.
    mean_entropy: dict[str, float] = {}
    for kp in keypoints:
        vals = [
            features_by_video[v].keypoints[kp].velocity_entropy
            for v in videos
            if kp in features_by_video[v].keypoints and np.isfinite(features_by_video[v].keypoints[kp].velocity_entropy)
        ]
        mean_entropy[kp] = float(np.mean(vals)) if vals else float("nan")

    finite_ent = [e for e in mean_entropy.values() if np.isfinite(e)]
    threshold = float(np.percentile(finite_ent, ENTROPY_TERTILE_PCT)) if finite_ent else float("nan")

    def si_for(kp: str) -> dict[str, float]:
        for left, right in paired:
            if kp in (left, right):
                pair_key = f"{left}__vs__{right}"
                out = {}
                for v in videos:
                    s = features_by_video[v].symmetry.get(pair_key)
                    out[v] = float(s.speed_symmetry_index) if s and np.isfinite(s.speed_symmetry_index) else float("nan")
                return out
        return {}

    # First pass: per-keypoint relative signals.
    deficit_pct: dict[str, float] = {}
    tmp: dict[str, dict] = {}
    for kp in keypoints:
        side = "right" if kp.startswith("right") else "left"
        si_by_video = si_for(kp)
        si_vals = [v for v in si_by_video.values() if np.isfinite(v)]
        si_median = float(np.median(si_vals)) if si_vals else float("nan")

        # Per-video "this side slower than its pair?" and the median deficit magnitude.
        def _deficit(si: float) -> float:
            # positive = THIS keypoint is slower than its contralateral pair.
            if not np.isfinite(si) or si <= 0:
                return float("nan")
            return (1.0 - 1.0 / si) if side == "right" else (1.0 - si)

        per_video_deficit = [_deficit(v) for v in si_vals]
        consistent_videos = sum(1 for d in per_video_deficit if np.isfinite(d) and d > 0)
        consistent = bool(si_vals) and all((d if np.isfinite(d) else -1) > 0 for d in per_video_deficit)
        median_deficit = float(np.median([d for d in per_video_deficit if np.isfinite(d)])) if per_video_deficit else float("nan")
        deficit_pct[kp] = median_deficit * 100.0 if np.isfinite(median_deficit) else float("nan")

        tmp[kp] = dict(
            side=side, si_by_video=si_by_video, si_median=si_median,
            consistent=consistent, consistent_videos=consistent_videos, n_videos=len(si_vals),
        )

    # Relative ranks across the 12 keypoints.
    findings: list[SegmentalFinding] = []
    pt_labels = PT_ASSESSMENT["labels"]
    pipeline_flagged: list[str] = []
    pt_flagged: list[str] = []
    both_flag = both_clear = pipeline_only = pt_only = 0

    prelim: list[dict] = []
    for kp in keypoints:
        ent = mean_entropy[kp]
        ent_pct = _rank01(mean_entropy, kp, higher_is_more=True)  # low = low variety
        speed_rank = _rank01(deficit_pct, kp, higher_is_more=True)  # high deficit => near 1
        variety_rank = (1.0 - ent_pct) if np.isfinite(ent_pct) else float("nan")  # low variety => near 1
        if np.isfinite(speed_rank) and np.isfinite(variety_rank):
            standout = float((speed_rank + variety_rank) / 2.0)
        else:
            standout = float("nan")
        low_variety = bool(np.isfinite(ent) and np.isfinite(threshold) and ent <= threshold)
        flag = bool(tmp[kp]["consistent"] and low_variety)
        prelim.append(dict(kp=kp, ent=ent, ent_pct=ent_pct, variety_rank=variety_rank,
                           speed_rank=speed_rank, standout=standout, low_variety=low_variety, flag=flag))

    order = sorted(range(len(prelim)), key=lambda i: (prelim[i]["standout"] if np.isfinite(prelim[i]["standout"]) else -1.0), reverse=True)
    rank_of = {prelim[i]["kp"]: r + 1 for r, i in enumerate(order)}

    for p in prelim:
        kp = p["kp"]
        t = tmp[kp]
        pt = pt_labels.get(kp)
        pt_prov = "abnormal" if pt == "abnormal" else ("normal" if pt == "normal" else None)
        flag_label = "abnormal" if p["flag"] else "normal"
        agree = (flag_label == pt_prov) if pt_prov is not None else None
        if p["flag"]:
            pipeline_flagged.append(kp)
        if pt_prov == "abnormal":
            pt_flagged.append(kp)
        if pt_prov is not None:
            if p["flag"] and pt_prov == "abnormal":
                both_flag += 1
            elif p["flag"] and pt_prov == "normal":
                pipeline_only += 1
            elif (not p["flag"]) and pt_prov == "abnormal":
                pt_only += 1
            else:
                both_clear += 1
        findings.append(SegmentalFinding(
            keypoint=kp, side=t["side"], joint=_joint_of(kp),
            si_by_video=t["si_by_video"], si_median=t["si_median"],
            contralateral_deficit_pct=deficit_pct[kp],
            deficit_consistent_videos=t["consistent_videos"], n_videos_with_si=t["n_videos"],
            consistent_speed_deficit=t["consistent"],
            mean_velocity_entropy=p["ent"], entropy_percentile=p["ent_pct"], low_variety=p["low_variety"],
            standout_score=p["standout"], standout_rank=rank_of[kp], pipeline_flag=p["flag"],
            pt_assessment_provisional=pt_prov, pt_agreement_provisional=agree,
        ))

    findings.sort(key=lambda f: f.standout_rank)

    # Headline: relative ranking (top standouts).
    top = [f for f in findings if np.isfinite(f.standout_score)][:3]
    top_str = "; ".join(
        f"{f.keypoint.replace('_', ' ')} (rank {f.standout_rank}: {f.contralateral_deficit_pct:+.0f}% vs pair in "
        f"{f.deficit_consistent_videos}/{f.n_videos_with_si} videos, variety {f.entropy_percentile*100:.0f}th pct)"
        for f in top
    )
    ranking_summary = (
        "INDEPENDENT relative ranking (this infant's limbs vs each other, no external reference). "
        f"Standing out most as slow-vs-pair AND low-variety-vs-peers: {top_str}."
    )
    flag_summary = (
        f"Conservative binary flag (consistent contralateral speed deficit AND bottom-tertile variety, "
        f"threshold {threshold:.3f} nats): {', '.join(k.replace('_', ' ') for k in pipeline_flagged) or 'no limb flagged'}. "
        "Heavily caveated: within-subject relative cutoff, n=3, 2D pixel-speed (camera-obliquity confound), signals partly co-vary."
    )
    independence_note = (
        "This assessment is INDEPENDENT: its rule and thresholds are within-subject relative comparisons derived from "
        "the infant's own kinematics, NOT fitted to or graded against any external reading. Any transcribed clinician "
        "reading below is a separate side-note only."
    )

    # PROVISIONAL clinician side-note (NOT ground truth, NOT used to calibrate anything).
    n_pt = both_flag + both_clear + pipeline_only + pt_only
    if n_pt == 0:
        pt_provisional_summary = (
            "No external clinician reading has been transcribed (PT_ASSESSMENT in mos_r.py is an empty placeholder). "
            "Fill it in to see a side-by-side coincidence count; the pipeline's own assessment above is independent "
            "of it either way."
        )
    else:
        pt_provisional_summary = (
            f"PROVISIONAL clinician reading ({PT_ASSESSMENT['scorer']}, {PT_ASSESSMENT['date']}) - NOT a confirmed "
            f"reference standard. It is shown only as an external side-note, NOT as ground truth. "
            f"Reading: {PT_ASSESSMENT['categorical']} "
            f"For interest only, the pipeline's own flag and this provisional reading happen to coincide on {both_flag + both_clear}"
            f"/{n_pt} keypoints (both-flagged={both_flag}, both-clear={both_clear}, pipeline-only={pipeline_only}, "
            f"PT-only={pt_only}) - this is NOT a validation (the reading is provisional and the pipeline is not calibrated to it)."
        )

    notes = (
        f"Independent relative assessment over {len(videos)} video(s). "
        + ("WARNING: fewer than 3 videos weakens the 'consistent in every video' condition. " if len(videos) < 3 else "")
        + "EXPLORATORY (few videos, single subject, no normative database; within-subject relative thresholds; 2D pixel-speed "
        "camera-obliquity confound; the speed-deficit and low-variety signals partly co-vary). NOT a GMA. Final clinical "
        "interpretation rests with the clinical care team; any transcribed clinician reading is a side-note, not a reference standard."
    )

    return SegmentalAnalysis(
        version=SEGMENTAL_VERSION,
        videos=videos,
        entropy_threshold=threshold,
        findings=findings,
        pipeline_flagged=pipeline_flagged,
        ranking_summary=ranking_summary,
        flag_summary=flag_summary,
        independence_note=independence_note,
        pt_provisional_flagged=pt_flagged,
        pt_provisional_agreement={"both_flag": both_flag, "both_clear": both_clear,
                                  "pipeline_only": pipeline_only, "pt_only": pt_only},
        pt_provisional_summary=pt_provisional_summary,
        notes=notes,
    )


def segmental_analysis_to_dict(analysis: SegmentalAnalysis) -> dict:
    return asdict(analysis)
