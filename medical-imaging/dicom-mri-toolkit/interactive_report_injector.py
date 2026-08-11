#!/usr/bin/env python3
"""
Interactive Report Injector
===========================
Post-processes the Plotly 3D HTML from ventricle_3d_analysis.py into a
fully self-contained review tool:

- Base64-embeds each candidate's validation PNG directly into the HTML
- Clicking a candidate marker in the 3D scene opens a modal with the
  matching validation panel
- Keyboard shortcuts: 1-9 and 0 jump to candidates, Escape closes
- Verdict-color-coded quick-nav buttons (green/amber/red)
- A hint toast that fades out after a few seconds

Candidate metadata is loaded from a JSON file (not hardcoded), e.g.:

    [
      {"index": 1, "image": "validation_candidate_01.png",
       "verdict": "LIKELY", "note": "free-text reviewer note"},
      {"index": 2, "image": "validation_candidate_02.png",
       "verdict": "UNCERTAIN", "note": ""}
    ]

Verdict strings control color coding: verdicts containing CONFIRMED or
LIKELY render green, UNCERTAIN amber, REJECTED red.

The injector refuses to run twice on the same file (it checks for an
injection marker) - regenerate the HTML first if you need to re-inject.

Usage:
    python interactive_report_injector.py \
        --html PATH/TO/ventricles_3d.html \
        --candidates PATH/TO/candidate_verdicts.json \
        --images-dir PATH/TO/validation_pngs \
        [--summary PATH/TO/validation_summary.png]
"""

import argparse
import base64
import json
import os
import sys

INJECTION_MARKER = "<!-- candidate-modal-injected -->"


def encode_image_base64(path):
    with open(path, 'rb') as f:
        data = f.read()
    return f"data:image/png;base64,{base64.b64encode(data).decode()}"


def verdict_class(verdict):
    """Map a verdict string to a CSS class for button coloring."""
    v = (verdict or '').upper()
    if 'REJECT' in v:
        return 'rejected'
    if 'UNCERTAIN' in v:
        return 'uncertain'
    return 'confirmed'


def verdict_symbol(verdict):
    v = (verdict or '').upper()
    if 'REJECT' in v:
        return 'x'
    if 'UNCERTAIN' in v:
        return '?'
    return 'ok'


STYLE_AND_MARKUP = """
<!-- candidate-modal-injected -->
<style>
#cand-modal-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.88);
    z-index: 10000;
    justify-content: center;
    align-items: center;
    cursor: pointer;
}
#cand-modal-overlay.active { display: flex; }
#cand-modal-content {
    max-width: 92vw;
    max-height: 90vh;
    position: relative;
}
#cand-modal-img {
    max-width: 92vw;
    max-height: 82vh;
    border: 2px solid #555;
    border-radius: 8px;
}
#cand-modal-caption {
    color: #ccc;
    text-align: center;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    margin-top: 8px;
}
#cand-modal-verdict {
    font-size: 16px;
    font-weight: bold;
    margin-top: 4px;
    text-align: center;
    font-family: 'Helvetica Neue', Arial, sans-serif;
}
#cand-modal-note {
    color: #999;
    font-size: 13px;
    text-align: center;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    margin-top: 2px;
}
#cand-modal-close {
    position: absolute;
    top: -15px;
    right: -15px;
    width: 32px; height: 32px;
    background: #444; color: white;
    border: 2px solid #888; border-radius: 50%;
    font-size: 18px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    z-index: 10001;
}
#cand-modal-close:hover { background: #666; }
#cand-hint {
    position: fixed;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(40,40,60,0.9);
    color: #aab;
    padding: 8px 18px;
    border-radius: 20px;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    z-index: 9999;
    pointer-events: none;
    transition: opacity 0.5s;
}
#cand-summary-btn {
    position: fixed;
    top: 12px; right: 12px;
    background: rgba(60,60,80,0.9);
    color: #dde; border: 1px solid #667;
    padding: 8px 16px; border-radius: 6px;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px; cursor: pointer; z-index: 9999;
}
#cand-summary-btn:hover { background: rgba(80,80,110,0.95); }
#cand-nav {
    position: fixed;
    bottom: 12px; right: 12px;
    display: flex; gap: 6px;
    z-index: 9999;
}
.cand-nav-btn {
    background: rgba(60,60,80,0.9);
    color: #dde; border: 1px solid #556;
    padding: 6px 12px; border-radius: 4px;
    font-family: monospace; font-size: 13px;
    cursor: pointer;
}
.cand-nav-btn:hover { background: rgba(80,80,110,0.95); }
.cand-nav-btn.confirmed { border-color: #6a6; color: #8c8; }
.cand-nav-btn.uncertain { border-color: #a86; color: #da8; }
.cand-nav-btn.rejected { border-color: #a44; color: #c88; opacity: 0.7; }
</style>

<div id="cand-modal-overlay" onclick="closeModal()">
    <div id="cand-modal-content" onclick="event.stopPropagation()">
        <button id="cand-modal-close" onclick="closeModal()">&times;</button>
        <img id="cand-modal-img" src="" alt="Candidate Validation">
        <div id="cand-modal-caption"></div>
        <div id="cand-modal-verdict"></div>
        <div id="cand-modal-note"></div>
    </div>
</div>

<div id="cand-hint">Click any candidate marker to view its validation panel</div>
<button id="cand-summary-btn" onclick="showSummary()">View All Candidates</button>

<div id="cand-nav">
    <span style="color:#888;font-size:12px;align-self:center;margin-right:4px;">Quick:</span>
    __NAV_BUTTONS__
</div>

<script>
__CANDIDATE_DATA__

function showCandidate(num) {
    const data = candidateImages[num];
    if (!data) return;
    document.getElementById('cand-modal-img').src = data.src;
    document.getElementById('cand-modal-caption').textContent =
        'Candidate #' + num + ' - Click outside or the X to close';
    const verdictEl = document.getElementById('cand-modal-verdict');
    verdictEl.textContent = data.verdict;
    const v = (data.verdict || '').toUpperCase();
    verdictEl.style.color = v.includes('REJECT') ? '#f66'
        : (v.includes('UNCERTAIN') ? '#fa6' : '#6f6');
    document.getElementById('cand-modal-note').textContent = data.note || '';
    document.getElementById('cand-modal-overlay').classList.add('active');
}

function showSummary() {
    if (!summaryImage) return;
    document.getElementById('cand-modal-img').src = summaryImage;
    document.getElementById('cand-modal-caption').textContent =
        'All candidates (summary panel)';
    document.getElementById('cand-modal-verdict').textContent = '';
    document.getElementById('cand-modal-note').textContent = '';
    document.getElementById('cand-modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('cand-modal-overlay').classList.remove('active');
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
    if (e.key >= '1' && e.key <= '9') showCandidate(parseInt(e.key));
    if (e.key === '0') showCandidate(10);
});

setTimeout(function() {
    var hint = document.getElementById('cand-hint');
    if (hint) { hint.style.opacity = '0'; setTimeout(function() { hint.remove(); }, 600); }
}, 5000);

setTimeout(function() {
    var plotDiv = document.querySelector('.plotly-graph-div') ||
                  document.querySelector('[class*="plotly"]') ||
                  document.querySelector('.js-plotly-plot');
    if (!plotDiv) return;
    plotDiv.on('plotly_click', function(eventData) {
        if (!eventData || !eventData.points || !eventData.points.length) return;
        var traceName = eventData.points[0].data.name || '';
        var match = traceName.match(/^Candidate #(\\d+)/);
        if (match) showCandidate(parseInt(match[1]));
    });
}, 1000);
</script>
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inject clickable candidate validation images into a Plotly 3D HTML report.")
    parser.add_argument('--html', required=True,
                        help="Plotly HTML file to modify in place")
    parser.add_argument('--candidates', required=True,
                        help="JSON file listing candidates: [{index, image, verdict, note}, ...]")
    parser.add_argument('--images-dir', default=None,
                        help="Directory containing the validation PNGs "
                             "(default: directory of the candidates JSON)")
    parser.add_argument('--summary', default=None,
                        help="Optional summary PNG shown by the 'View All Candidates' button")
    return parser.parse_args()


def main():
    args = parse_args()
    images_dir = args.images_dir or os.path.dirname(os.path.abspath(args.candidates))

    with open(args.html, 'r') as f:
        html = f.read()

    if INJECTION_MARKER in html:
        print("ERROR: This HTML already contains the injected modal.")
        print("Re-running would duplicate the UI. Regenerate the HTML "
              "(ventricle_3d_analysis.py) and inject again.")
        sys.exit(1)

    with open(args.candidates) as f:
        entries = json.load(f)

    print(f"Injecting {len(entries)} candidate images into {os.path.basename(args.html)}...")

    images_b64 = {}
    for entry in entries:
        idx = int(entry['index'])
        img_path = os.path.join(images_dir, entry['image'])
        if not os.path.exists(img_path):
            print(f"  WARNING: image not found, skipping #{idx}: {img_path}")
            continue
        images_b64[idx] = {
            'src': encode_image_base64(img_path),
            'verdict': entry.get('verdict', ''),
            'note': entry.get('note', ''),
        }
        print(f"  #{idx}: {os.path.getsize(img_path) / 1024:.0f} KB - {entry.get('verdict', '(no verdict)')}")

    if not images_b64:
        print("ERROR: no candidate images found; nothing to inject.")
        sys.exit(1)

    # Optional summary image
    summary_b64 = None
    if args.summary and os.path.exists(args.summary):
        summary_b64 = encode_image_base64(args.summary)

    # Build JS data block (json.dumps handles all escaping)
    js_images = "const candidateImages = {\n"
    for idx, data in sorted(images_b64.items()):
        js_images += (f"  {idx}: {{src: {json.dumps(data['src'])}, "
                      f"verdict: {json.dumps(data['verdict'])}, "
                      f"note: {json.dumps(data['note'])}}},\n")
    js_images += "};\n"
    js_images += f"const summaryImage = {json.dumps(summary_b64)};\n"

    # Build verdict-coded nav buttons
    nav_buttons = ""
    for idx, data in sorted(images_b64.items()):
        cls = verdict_class(data['verdict'])
        sym = verdict_symbol(data['verdict'])
        nav_buttons += (f'<button class="cand-nav-btn {cls}" '
                        f'onclick="showCandidate({idx})">#{idx} {sym}</button>\n    ')

    inject_html = (STYLE_AND_MARKUP
                   .replace('__CANDIDATE_DATA__', js_images)
                   .replace('__NAV_BUTTONS__', nav_buttons))

    if '</body>' in html:
        html = html.replace('</body>', inject_html + '\n</body>')
    else:
        html += inject_html

    with open(args.html, 'w') as f:
        f.write(html)

    size_mb = os.path.getsize(args.html) / (1024 * 1024)
    print(f"\n  Updated HTML: {size_mb:.1f} MB")
    print("  Done.")


if __name__ == '__main__':
    main()
