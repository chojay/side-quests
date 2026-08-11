# Architecture

System design of the GMA video pipeline: how a phone video becomes kinematic features and an honest proxy score. See [README.md](README.md) for motivation, science, and limitations; this document is the structural map.

## Dataflow

```mermaid
flowchart TD
    V[/"home video (.mov)"/] --> PRE[preprocess.py <br/>frame extraction 30 fps, rotation metadata, <br/>ffprobe QuickTime timestamps]
    PRE --> SEG[segment.py <br/>3-tier segmentation with fallback]
    SEG --> POSE[pose.py <br/>BlazePose 33 to 13 keypoints, <br/>mask-guided background darkening, <br/>principal-axis rotation normalization]
    POSE --> FEAT[features.py <br/>velocity, jerk, entropy, PSD, curvature, <br/>supine-validity mask, rolling detectors, <br/>whole-body synchrony]

    FEAT --> MOS[mos_r.py <br/>honest MOS-R proxy: <br/>F + C subscales only, <br/>rest NOT_COMPUTABLE]
    FEAT --> SCORE[scoring.py <br/>heuristic subscale proxies, <br/>symmetry-index bands]
    FEAT --> CAL[calibration.py <br/>per-limb segmental-asymmetry <br/>ranking]

    MOS --> REP[report.py <br/>markdown reports]
    SCORE --> REP
    CAL --> REP
    REP --> HTML[html_report.py <br/>self-contained HTML dashboard, <br/>plots embedded as base64]
    FEAT --> VIZ[viz.py <br/>matplotlib time series, FFT, <br/>symmetry plots]
    VIZ --> HTML

    subgraph SUPPORT["Support modules"]
        CLI[cli.py <br/>10-subcommand Typer CLI]
        CFG[config.py <br/>run config + SHA-256 hash]
        BP[body_parts.py <br/>SAM 3 per-limb labeling, <br/>anatomical left/right resolution]
        SC[spot_check.py <br/>segmentation QA panels]
        COMPAT[sam3_compat.py <br/>CUDA-to-MPS patches]
    end

    CLI -.orchestrates.-> PRE
    CFG -.stamps every run.-> REP
    COMPAT -.enables.-> SEG
    BP -.labels limbs for.-> CAL
```

## The segmentation fallback chain

Segmentation is the most environment-sensitive stage, so it degrades gracefully:

```mermaid
flowchart LR
    A{SAM 3 imports <br/>and runs on MPS?} -->|yes| S3[SAM 3 <br/>text-prompted segmentation]
    A -->|no| B{SAM 2.1 <br/>available?}
    B -->|yes| S2[SAM 2.1 tiny <br/>box prompt bootstrapped <br/>from MediaPipe]
    B -->|no| MP[MediaPipe <br/>Selfie Segmenter alone]
```

Two deliberate decisions live here:

- **Crop-first inference.** SAM internally resizes to 1024x1024, so the frame is cropped to the subject bounding box (plus 20 percent) before inference and the mask is pasted back afterward. The model spends its resolution on the subject instead of the floor.
- **SAM 2.1 tiny over base_plus.** The larger model "correctly" separates the diaper from skin, which punches a hole in the body mask and breaks pose estimation downstream. The smaller model produces the coherent whole-body mask the pipeline actually needs.

## Why the scoring path is split across three modules

The separation is intentional, not incidental:

- `mos_r.py` owns the claim discipline: which MOS-R subscales a 13-keypoint 2D skeleton can partially address (Fidgety and Movement Character, 16 of 28 points) and which it must report as NOT_COMPUTABLE. Its upper bound imputes missing subscales at ceiling, never at middle values, because middle values would fabricate pathology.
- `scoring.py` holds the heuristic feature-to-band mappings, kept apart so heuristics can be tuned without touching the claim discipline.
- `calibration.py` is an independent within-subject check that ranks paired keypoints by contralateral speed deficit plus low movement variety. It shares no thresholds with the other two, so its output can corroborate or contradict them.

## Validity before kinematics

GMA is only defined for a supine infant, so validity is computed before any feature is trusted. The per-frame supine-validity mask votes on trunk geometry (bi-acromial width collapse, signed shoulder-offset sign flips, trunk tilt), is debounced by a centered majority window, and supports multiple disjoint valid segments. Kinematics are computed over the full series with invalid frames as NaN, so no derivative ever bridges an excluded rolling event. Two independent rolling detectors (velocity-spike and gradual-angle) mark the events themselves.

## Reproducibility spine

Every run writes a `config.yaml` containing the exact configuration and a SHA-256 hash of it; reports embed the hash. The CLI is idempotent per stage (skip-existing), so a crashed run resumes rather than recomputes. Tests are fully synthetic (seeded RNG trajectories, rectangle masks, handcrafted feature objects); no real data exists anywhere in the repo.
