# EXAMPLE MOS-R Proxy Evaluation (synthetic run)

> **EXAMPLE REPORT from a fully synthetic recording.** A 90-second seeded
> pose sequence (13 keypoints, fidgety-band oscillations, plus a scripted
> roll at 38-47 s) was written to parquet and pushed through the real
> evaluation path: `extract_features_from_parquet` -> validity mask ->
> kinematics -> `compute_mosr_proxy`. No real recording, infant, or
> clinical content exists anywhere in this example.

**Supine-validity:** 91% of frames valid across 2 segments (0.0-38.4s, 46.6-90.0s); the scripted roll was excluded, not truncated.

**Computable proxy total: 16 / 16** (full clinical MOS-R is 28)

| Subscale | Points | Max | Status | Note (first line) |
|---|---:|---:|---|---|
| F (Fidgety movements) | 12 | 12 | computed (partial) | Per-limb distal-marker fidgety proxy: 4/4 limbs present+in-band -> F~12. fidgety present and co |
| P (Observed movement patterns) | - | 4 | NOT_COMPUTABLE | Requires recognizing/counting a named catalogue of typical vs atypical age-specific patterns (h |
| R (Age-adequate movement repertoire) | - | 4 | NOT_COMPUTABLE | Requires an age-keyed normative database of expected patterns. Clinician-only. |
| Po (Observed postural patterns) | - | 4 | NOT_COMPUTABLE | Requires finger posture (absent in a 13-keypoint skeleton) and depth/Gestalt judgement of neck/ |
| C (Movement character) | 4 | 4 | computed (partial) | Whole-body cramped-sync index (mean SIGNED zero-lag speed-envelope correlation across all limb  |

**Ceiling-imputed upper bound: 28 / 28.** Clinician-only
subscales are imputed at maximum, never at middle values, because middle
values would fabricate pathology.

## Interpretation discipline (verbatim pipeline output)

MOS-R PROXY (exploratory, non-clinical). Computable proxy F+C = 16 of 16 (F=12/12, C=4/4). Observed-patterns (P), age-adequate-repertoire (R) and postural (Po) are NOT computable from 2D pose and are clinician-only. UPPER BOUND on the full MOS-R = 28/28 (P/R/Po imputed at ceiling 4/4/4); the true MOS-R is <= this by an unknown margin and only a certified assessor can fill the missing 12 points. The upper bound's nominal 'optimal (25-28)' band is NOT reassurance: a near-normal proxy total more likely reflects this proxy's BLINDNESS to the P/R/Po/character channels than a normal infant - a genuinely CP-heralding unilateral deficit normally DRAGS the true MOS-R down (perinatal-stroke->unilateral-CP median MOS-R was 6, not near-normal; Bertoncelli 2024). GUARDRAIL: do not read a high F or a high upper bound as 'normal/reassuring' while a limb is flagged abnormal in the SEGMENTAL ASYMMETRY analysis - that per-limb map, not this total, is the headline.

## Per-limb monitoring (synthetic run)

Each limb is tracked through its distal marker; the calibration module
independently ranks limbs by contralateral speed deficit plus movement
variety (figure: `example-run-limbs.png`).

| Limb | Distal marker | Fidgety quality | Speed (diag/s) | Dominant freq |
|---|---|---|---:|---:|
| left arm | left_wrist | present_normal | 0.099 | 2.3 Hz |
| right arm | right_wrist | present_normal | 0.110 | 2.6 Hz |
| left leg | left_ankle | present_normal | 0.104 | 2.1 Hz |
| right leg | right_ankle | present_normal | 0.135 | 2.8 Hz |
