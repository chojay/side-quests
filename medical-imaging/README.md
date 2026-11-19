# Medical Imaging Side Quests

Two code-only projects that work through medical imaging and movement analysis from first principles. No patient imaging, videos, DICOM files, or real reports ship with either project; each carries one explicitly labeled example (a synthetic-fixture evaluation; a public-template annotation figure). Both expect you to supply your own data and both defer, explicitly and by design, to clinicians.

| Project | What it does | Docs |
|---|---|---|
| [gma-video-pipeline/](gma-video-pipeline/) | A study of the published General Movements Assessment (GMA) method: a phone-camera clip to segmentation, pose, kinematic features, and an honest MOS-R proxy score. SAM 3 / SAM 2.1 on Apple Silicon. | [README](gma-video-pipeline/README.md) - [ARCHITECTURE](gma-video-pipeline/ARCHITECTURE.md) - [DISCLAIMER](gma-video-pipeline/DISCLAIMER.md) |
| [dicom-mri-toolkit/](dicom-mri-toolkit/) | Two DICOM MRI studies to matched series, normalized difference maps, 3D ventricle reconstruction, curvature-based shape analysis, and a self-contained interactive HTML report. | [README](dicom-mri-toolkit/README.md) - [ARCHITECTURE](dicom-mri-toolkit/ARCHITECTURE.md) |

Shared principles:

- **Honesty about limits is a feature.** The GMA pipeline reports 3 of 5 subscales as NOT_COMPUTABLE instead of imputing them. The MRI toolkit caps candidates and routes every one through human visual review with veto power.
- **If tooling disagrees with a clinician, the clinician is right by definition.** Both projects state this rule in their docs; the GMA pipeline also bakes it into every scoring string.
- **All data stays local, always.** These tools exist to learn the methods, never to answer a clinical question.
