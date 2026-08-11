# Medical Imaging Side Quests

Two code-only projects built to understand clinical imaging from first principles instead of passively receiving it. No patient imaging, videos, DICOM files, or real reports ship with either project; each carries one explicitly labeled example (a synthetic-fixture evaluation; a public-template annotation figure). Both expect you to supply your own data and both defer, explicitly and by design, to clinicians.

| Project | What it does | Docs |
|---|---|---|
| [gma-video-pipeline/](gma-video-pipeline/) | Infant general-movements video to segmentation, pose, kinematic features, and an honest MOS-R proxy score. SAM 3 / SAM 2.1 on Apple Silicon. | [README](gma-video-pipeline/README.md) - [ARCHITECTURE](gma-video-pipeline/ARCHITECTURE.md) - [DISCLAIMER](gma-video-pipeline/DISCLAIMER.md) |
| [dicom-mri-toolkit/](dicom-mri-toolkit/) | Hospital DICOM CD to matched series, longitudinal difference maps, 3D ventricle reconstruction, curvature-based candidate detection, and a self-contained interactive HTML report. | [README](dicom-mri-toolkit/README.md) - [ARCHITECTURE](dicom-mri-toolkit/ARCHITECTURE.md) |

Shared principles:

- **Honesty about limits is a feature.** The GMA pipeline reports 3 of 5 subscales as NOT_COMPUTABLE instead of imputing them. The MRI toolkit caps candidates and routes every one through human visual review with veto power.
- **If tooling disagrees with a clinician, the clinician is right by definition.** Both projects state this rule in code and docs.
- **All data stays local, always.** These tools exist to help someone ask their care team better questions.
