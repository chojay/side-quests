# Disclaimer

**This pipeline is for personal reference only.**

It is not a medical device. It has not been validated for clinical use. It is not cleared by the FDA or any other regulatory body. Its outputs are not a diagnosis.

It is not a substitute for professional General Movements Assessment (GMA) scoring by a trained clinician. All clinical decisions about any infant must be made by that infant's clinicians.

Any results produced by this pipeline are best treated as exploratory pattern observations. This began as a personal project to better understand home recordings, to learn the relevant computer vision and signal processing techniques, and to track changes over time across recordings. It does not exist to compete with, replace, or second-guess a clinician's professional interpretation.

If pipeline output disagrees with a clinician's scoring, the clinical scoring is correct by definition. The pipeline is the thing being calibrated, not the clinician.

## Specific limitations

- **2D pose only**. Single-camera phone footage cannot capture true 3D motion. Postural assessment is approximate.
- **Infant pose models are imperfect**. Adult-trained pose estimators systematically misplace infant keypoints. Even infant-specialized models like Ostadabbas SyRIP have measurable error.
- **MOS-R subscales partial**. Only the Fidgety and Movement Character subscales are even partially derivable from 2D pose (max 16 of 28 points). Observed Patterns, Age-adequate Repertoire, and Postural Patterns are clinician-only and are reported as NOT_COMPUTABLE.
- **No reference comparison**. The pipeline uses heuristic thresholds derived from published feature distributions. Calibration against an actual clinical interpretation would be required for any confidence in the proxy scores.
- **Cramped-synchronized detection unvalidated**. The whole-body synchrony index can flag the pattern direction but has not been clinically validated in this pipeline.

## When in doubt, defer to the clinician.
