"""Self-contained HTML assessment reports.

Produces shareable single-file HTML (plots embedded as base64 data URIs, so each
file is fully portable - no external assets):
  - one per-video report (kinematics, MOS-R proxy, validity timeline, plots),
  - one cross-video dashboard `gma-assessment.html` (segmental concordance table
    + scatter, MOS-R summary, links to per-video pages, population cutoffs).

EVERY NUMBER IS A PROXY. Not a medical device. Final interpretation rests with
the infant's clinical care team.
"""

from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path

import numpy as np

from gma_pipeline.features import VideoFeatures
from gma_pipeline.mos_r import PT_ASSESSMENT, POPULATION_CUTOFFS, MOSRProxy
from gma_pipeline.scoring import ScoringResult


_CSS = """
:root { --abn:#dc2626; --norm:#2563eb; --ok:#16a34a; --ink:#1f2937; --mut:#6b7280; --line:#e5e7eb; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: var(--ink);
       max-width: 1000px; margin: 0 auto; padding: 24px; line-height: 1.5; background:#fff; }
h1 { font-size: 1.7rem; margin-bottom: 4px; } h2 { font-size: 1.25rem; margin-top: 32px; border-bottom: 2px solid var(--line); padding-bottom: 6px; }
h3 { font-size: 1.05rem; color: var(--mut); margin-top: 22px; }
.disclaimer { background:#fef2f2; border:1px solid #fecaca; border-left:5px solid var(--abn); padding:12px 16px; border-radius:8px; margin:16px 0; font-size:0.9rem; }
.meta { color: var(--mut); font-size: 0.85rem; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.9rem; }
th, td { border: 1px solid var(--line); padding: 7px 10px; text-align: left; }
th { background:#f9fafb; }
tr.abn td { background:#fef2f2; } tr.miss td { background:#fffbeb; }
.tag { display:inline-block; padding:1px 8px; border-radius:999px; font-size:0.78rem; font-weight:600; }
.tag.abn { background:#fee2e2; color:var(--abn); } .tag.norm { background:#dbeafe; color:var(--norm); }
.tag.ok { background:#dcfce7; color:var(--ok); } .tag.na { background:#f3f4f6; color:var(--mut); }
.card { border:1px solid var(--line); border-radius:10px; padding:16px 18px; margin:14px 0; background:#fcfcfd; }
.big { font-size:1.5rem; font-weight:700; } .kpi { display:inline-block; margin-right:28px; }
img.plot { max-width:100%; border:1px solid var(--line); border-radius:8px; margin:8px 0; }
a { color: var(--norm); } .footer { margin-top:40px; color:var(--mut); font-size:0.82rem; border-top:1px solid var(--line); padding-top:12px; }
code { background:#f3f4f6; padding:1px 5px; border-radius:4px; font-size:0.85em; }
"""

_DISCLAIMER = (
    "<strong>NOT A MEDICAL DEVICE.</strong> This is a parent's exploratory, non-clinical pose-analysis of "
    "home videos. Every number is a PROXY, not a GMA score or diagnosis. It has not been validated against "
    "any clinical reference standard. Final interpretation rests entirely with the infant's clinical care team."
)


def _img(path: Path, alt: str) -> str:
    if not path.exists():
        return f"<p class='meta'>[{html.escape(alt)} not available]</p>"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f'<img class="plot" alt="{html.escape(alt)}" src="data:image/png;base64,{b64}">'


def _page(title: str, body: str) -> str:
    stamp = datetime.now().isoformat(timespec="seconds")
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head><body>"
        f"{body}"
        f"<div class='footer'>Generated {stamp} - gma-pipeline v0.2 - "
        "personal-reference, non-clinical.</div></body></html>"
    )


def build_video_html(features: VideoFeatures, scoring: ScoringResult, mosr: MOSRProxy,
                     plots_dir: Path, out_dir: Path) -> Path:
    fps = features.fps or 30.0
    seg_str = ", ".join(f"{a / fps:.1f}-{b / fps:.1f}s" for a, b in features.valid_segments)
    b: list[str] = []
    b.append(f"<h1>GMA Assessment - {html.escape(features.video_id)}</h1>")
    b.append(f"<p class='meta'>Scoring version <code>{html.escape(scoring.scoring_version)}</code> - "
             "<a href='gma-assessment.html'>&larr; back to dashboard</a></p>")
    b.append(f"<div class='disclaimer'>{_DISCLAIMER}</div>")

    b.append("<h2>Supine-validity</h2>")
    b.append(
        "<div class='card'><span class='kpi'><span class='big'>"
        f"{features.valid_supine_fraction * 100:.0f}%</span> valid supine</span>"
        f"<span class='kpi'><span class='big'>{features.n_invalid_segments}</span> excluded roll/prone segment(s)</span>"
        f"<br><span class='meta'>Valid segment(s): {seg_str}. Every rolling/side-lying/prone frame is excluded "
        "by a per-frame mask, not just a trailing truncation.</span></div>"
    )
    b.append(_img(plots_dir / f"{features.video_id}-validity-timeline.png", "validity timeline"))

    b.append("<h2>MOS-R PROXY</h2>")
    b.append("<table><tr><th>Subscale</th><th>Max</th><th>Proxy</th><th>Computable</th></tr>")
    for code in ("F", "P", "R", "Po", "C"):
        s = mosr.subscales[code]
        pts = "<span class='tag na'>clinician-only</span>" if s.points is None else f"<b>{s.points:g}</b>"
        b.append(f"<tr><td>{s.code} - {html.escape(s.name)}</td><td>{s.max_points}</td>"
                 f"<td>{pts}</td><td>{s.computable}</td></tr>")
    b.append("</table>")
    b.append(
        f"<div class='card'><span class='kpi'>Computable F+C: <b>{mosr.computable_total:g}/{mosr.computable_max}"
        f"</b></span><span class='kpi'>Upper bound: <b>&le; {mosr.upper_bound_28:g}/28</b></span>"
        f"<span class='kpi'>Repertoire-richness descriptor: {mosr.repertoire_richness_descriptor:.2f} nats</span></div>"
    )

    b.append("<h2>Per-keypoint kinematics</h2>")
    b.append("<table><tr><th>Keypoint</th><th>valid %</th><th>mean speed (px/s)</th>"
             "<th>dom freq (Hz)</th><th>vel entropy</th></tr>")
    for kp_name, kk in features.keypoints.items():
        b.append(f"<tr><td>{kp_name}</td><td>{kk.fraction_valid * 100:.0f}%</td>"
                 f"<td>{kk.speed_mean:.1f}</td><td>{kk.dominant_freq_hz:.2f}</td>"
                 f"<td>{kk.velocity_entropy:.2f}</td></tr>")
    b.append("</table>")

    b.append("<h2>Plots</h2>")
    b.append(_img(plots_dir / "symmetry.png", "symmetry per keypoint pair"))
    b.append(_img(plots_dir / "velocity_time_series.png", "velocity time series"))
    b.append(_img(plots_dir / "wrist_fft.png", "wrist FFT"))

    b.append("<h2>Interpretation</h2>")
    b.append(f"<p>{html.escape(scoring.interpretation)}</p>")

    out = out_dir / f"{features.video_id}-gma-report.html"
    out.write_text(_page(f"GMA - {features.video_id}", "".join(b)))
    return out


def build_dashboard_html(features_by_video: dict, mosr_by_video: dict, analysis,
                         plots_dir: Path, out_dir: Path) -> Path:
    b: list[str] = []
    b.append("<h1>Independent GMA-informed Pose Assessment (v0.3)</h1>")
    b.append("<p class='meta'>Fidgety-stage home recordings. This is the pose pipeline's OWN independent, "
             "relative assessment - each limb compared to its contralateral pair and to the infant's other limbs. It "
             "is NOT calibrated to any external reading. Any transcribed clinician reading appears further down as a "
             "side-note only.</p>")
    b.append(f"<div class='disclaimer'>{_DISCLAIMER}</div>")

    # 1. Independent relative ranking (headline)
    b.append("<h2>1. Independent relative ranking (headline)</h2>")
    b.append(f"<div class='card'>{html.escape(analysis.ranking_summary)}<br>"
             f"<span class='meta'>{html.escape(analysis.independence_note)}</span></div>")
    b.append(_img(plots_dir / "segmental-concordance.png", "independent per-keypoint scatter"))
    b.append("<table><tr><th>Rank</th><th>Keypoint</th><th>% vs pair</th><th>slower in</th><th>variety pct</th>"
             "<th>low-variety</th><th>standout</th><th>flag</th></tr>")
    for f in analysis.findings:  # sorted by standout_rank
        dpct = "nan" if not np.isfinite(f.contralateral_deficit_pct) else f"{f.contralateral_deficit_pct:+.0f}%"
        vpct = "nan" if not np.isfinite(f.entropy_percentile) else f"{f.entropy_percentile * 100:.0f}th"
        so = "nan" if not np.isfinite(f.standout_score) else f"{f.standout_score:.2f}"
        row_cls = " class='abn'" if f.pipeline_flag else ""
        flag = "<span class='tag abn'>flag</span>" if f.pipeline_flag else "-"
        b.append(f"<tr{row_cls}><td>{f.standout_rank}</td><td>{f.keypoint}</td><td>{dpct}</td>"
                 f"<td>{f.deficit_consistent_videos}/{f.n_videos_with_si}</td><td>{vpct}</td>"
                 f"<td>{'yes' if f.low_variety else 'no'}</td><td>{so}</td><td>{flag}</td></tr>")
    b.append("</table>")

    # 2. Conservative binary flag (caveated)
    b.append("<h2>2. Conservative binary flag (caveated)</h2>")
    b.append(f"<div class='card'>{html.escape(analysis.flag_summary)}</div>")

    # 3. External clinician reading (side-note only - NOT ground truth)
    b.append("<h2>3. External clinician reading (side-note only - NOT ground truth)</h2>")
    if PT_ASSESSMENT.get("scorer"):
        b.append(f"<div class='card'><b>{html.escape(str(PT_ASSESSMENT['scorer']))}</b>, "
                 f"{html.escape(str(PT_ASSESSMENT['date'] or 'undated'))} "
                 f"<span class='tag na'>PROVISIONAL</span><br>"
                 f"<span class='meta'>{html.escape(str(PT_ASSESSMENT['categorical'] or ''))}</span><br>"
                 f"<span class='meta'>{html.escape(analysis.pt_provisional_summary)}</span></div>")
    else:
        b.append(f"<div class='card'><span class='meta'>{html.escape(analysis.pt_provisional_summary)}</span></div>")
    b.append(f"<p class='meta'>{html.escape(analysis.notes)}</p>")

    # MOS-R summary
    b.append("<h2>MOS-R PROXY summary</h2>")
    b.append("<p class='meta'>Only Fidgety (F) and Movement Character (C) are computable from 2D pose (max 16 of 28); "
             "Observed Patterns, Age-adequate Repertoire and Postural require a clinician. A focal one-limb deficit "
             "does not crush the whole-body total - read the segmental table above as the headline.</p>")
    b.append(_img(plots_dir / "mosr-summary.png", "MOS-R proxy summary"))
    b.append("<table><tr><th>Video</th><th>F (/12)</th><th>C (/4)</th><th>Computable F+C</th>"
             "<th>Upper bound</th><th>Detail</th></tr>")
    for v, mosr in mosr_by_video.items():
        fp = mosr.subscales["F"].points or 0.0
        cp = mosr.subscales["C"].points or 0.0
        b.append(f"<tr><td>{v}</td><td>{fp:g}</td><td>{cp:g}</td>"
                 f"<td><b>{mosr.computable_total:g}/{mosr.computable_max}</b></td>"
                 f"<td>&le; {mosr.upper_bound_28:g}/28</td>"
                 f"<td><a href='{v}-gma-report.html'>{v} report &rarr;</a></td></tr>")
    b.append("</table>")

    # Per-video supine-validity
    b.append("<h2>Per-video supine-validity</h2>")
    b.append("<table><tr><th>Video</th><th>frames</th><th>valid supine</th><th>segments</th><th>excluded</th></tr>")
    for v, feats in features_by_video.items():
        fps = feats.fps or 30.0
        seg_str = ", ".join(f"{a / fps:.1f}-{b2 / fps:.1f}s" for a, b2 in feats.valid_segments)
        b.append(f"<tr><td>{v}</td><td>{feats.n_frames}</td>"
                 f"<td>{feats.valid_supine_fraction * 100:.0f}%</td><td>{seg_str}</td>"
                 f"<td>{feats.n_invalid_segments}</td></tr>")
    b.append("</table>")

    # Population cutoffs
    b.append("<h2>Population MOS-R cutoffs (context only)</h2>")
    b.append("<table><tr><th>Population</th><th>Threshold</th><th>Note</th><th>Source</th></tr>")
    for co in POPULATION_CUTOFFS:
        b.append(f"<tr><td>{html.escape(co['population'])}</td><td>{html.escape(co['threshold'])}</td>"
                 f"<td>{html.escape(co['note'])}</td><td>{html.escape(co['source'])}</td></tr>")
    b.append("</table>")

    out = out_dir / "gma-assessment.html"
    out.write_text(_page("GMA Assessment Dashboard", "".join(b)))
    return out
