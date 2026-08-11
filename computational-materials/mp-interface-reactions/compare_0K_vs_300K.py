"""
Compare 0 K vs 300 K interface reaction results.

Parses both summary markdown files and generates:
1. Side-by-side comparison table (markdown)
2. Scatter plot: E_0K vs E_300K with y=x reference
3. Bar chart: ΔE (E_300K - E_0K) per material
4. Highlights materials with significant rank changes

Usage:
    python compare_0K_vs_300K.py
    python compare_0K_vs_300K.py --file-0k custom_0K.md --file-300k custom_300K.md
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import argparse

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_summary_table(path, reference="Si"):
    """Parse materials and energies from a summary markdown file.

    Returns dict: {material_name: {"e_ev": float, "e_kj": float, "reaction": str}}
    """
    with open(path) as f:
        text = f.read()

    data = {}
    for line in text.split("\n"):
        if line.startswith(f"| {reference} |"):
            parts = [c.strip() for c in line.split("|")]
            mat = parts[2]
            rxn = parts[3]
            try:
                e_ev = float(parts[4])
            except ValueError:
                continue
            try:
                e_kj = float(parts[5])
            except ValueError:
                e_kj = 0.0
            data[mat] = {"e_ev": e_ev, "e_kj": e_kj, "reaction": rxn}
    return data


def get_halogen_color(mat):
    """Color-code by primary halogen."""
    mat_upper = mat.upper()
    has_F = 'F' in mat_upper and mat_upper not in ['ALCL3']
    has_Cl = 'CL' in mat_upper
    has_Br = 'BR' in mat_upper
    has_I = mat in ['HI', 'IF7', 'TiI4']

    if has_F and (has_Cl or has_I):
        return '#8b5cf6'
    elif has_F:
        return '#2563eb'
    elif has_Cl:
        return '#059669'
    elif has_Br:
        return '#ea580c'
    elif has_I:
        return '#dc2626'
    return '#6b7280'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare 0 K vs 300 K interface reaction results.")
    parser.add_argument("--reference", default="Si", help="Reference material symbol used in the summary tables.")
    parser.add_argument("--file-0k", default=None, help="Path to 0 K summary markdown.")
    parser.add_argument("--file-300k", default=None, help="Path to 300 K summary markdown.")
    args = parser.parse_args()

    # Locate summary files
    file_0k = args.file_0k
    file_300k = args.file_300k

    if file_0k is None:
        # Try temperature-suffixed name first, then legacy
        candidate = os.path.join(OUTPUT_DIR, "Si_interface_reactions_0K.md")
        if os.path.exists(candidate):
            file_0k = candidate
        else:
            file_0k = os.path.join(OUTPUT_DIR, "Si_interface_reactions_0K.md")

    if file_300k is None:
        file_300k = os.path.join(OUTPUT_DIR, "Si_interface_reactions_300K.md")

    if not os.path.exists(file_0k):
        print(f"ERROR: 0 K summary not found: {file_0k}")
        print("Run: python run_interface_reactions.py (once per temperature)  (or --temperature 0)")
        exit(1)
    if not os.path.exists(file_300k):
        print(f"ERROR: 300 K summary not found: {file_300k}")
        print("Run: python run_interface_reactions.py (once per temperature) --temperature 300")
        exit(1)

    data_0k = parse_summary_table(file_0k, reference=args.reference)
    data_300k = parse_summary_table(file_300k, reference=args.reference)

    # Find common materials
    common = sorted(set(data_0k.keys()) & set(data_300k.keys()),
                    key=lambda m: data_0k[m]["e_ev"])

    print(f"0 K file:   {os.path.basename(file_0k)} ({len(data_0k)} materials)")
    print(f"300 K file: {os.path.basename(file_300k)} ({len(data_300k)} materials)")
    print(f"Common materials: {len(common)}")

    if not common:
        print("ERROR: No common materials found between the two files.")
        exit(1)

    # ── Build comparison data ─────────────────────────────────────────
    # Rank at 0 K (1 = most negative)
    ranked_0k = sorted(common, key=lambda m: data_0k[m]["e_ev"])
    rank_0k = {m: i + 1 for i, m in enumerate(ranked_0k)}

    # Rank at 300 K
    ranked_300k = sorted(common, key=lambda m: data_300k[m]["e_ev"])
    rank_300k = {m: i + 1 for i, m in enumerate(ranked_300k)}

    rows = []
    for mat in ranked_0k:
        e0 = data_0k[mat]["e_ev"]
        e3 = data_300k[mat]["e_ev"]
        delta = e3 - e0
        r0 = rank_0k[mat]
        r3 = rank_300k[mat]
        rank_change = r0 - r3  # positive = moved up at 300 K
        rows.append({
            "mat": mat,
            "e_0k": e0,
            "e_300k": e3,
            "delta": delta,
            "rank_0k": r0,
            "rank_300k": r3,
            "rank_change": rank_change,
        })

    # ── 1. Markdown comparison table ──────────────────────────────────
    md = []
    md.append("# Comparison: 0 K vs 300 K Interface Reaction Energies")
    md.append("")
    md.append(f"**0 K source**: `{os.path.basename(file_0k)}`")
    md.append(f"**300 K source**: `{os.path.basename(file_300k)}`")
    md.append(f"**Materials compared**: {len(common)}")
    md.append("")
    md.append("## Key Observations")
    md.append("")

    avg_delta = np.mean([r["delta"] for r in rows])
    max_delta_row = max(rows, key=lambda r: r["delta"])
    min_delta_row = min(rows, key=lambda r: r["delta"])
    big_rank_changes = [r for r in rows if abs(r["rank_change"]) >= 3]

    md.append(f"- **Average shift**: {avg_delta:+.4f} eV/atom (300 K vs 0 K)")
    md.append(f"- **Largest positive shift** (least affected): {max_delta_row['mat']} ({max_delta_row['delta']:+.4f} eV/atom)")
    md.append(f"- **Smallest shift** (most affected): {min_delta_row['mat']} ({min_delta_row['delta']:+.4f} eV/atom)")
    md.append(f"- **Materials with rank change >= 3**: {len(big_rank_changes)}")
    md.append("")

    md.append("## Comparison Table")
    md.append("")
    md.append("| Rank (0K) | Material | E_0K (eV/atom) | E_300K (eV/atom) | \u0394E (eV/atom) | Rank (300K) | Rank \u0394 |")
    md.append("|-----------|----------|---------------:|------------------:|---------------:|------------:|-------:|")
    for r in rows:
        rc_str = f"+{r['rank_change']}" if r['rank_change'] > 0 else str(r['rank_change'])
        highlight = " **" if abs(r['rank_change']) >= 3 else ""
        md.append(
            f"| {r['rank_0k']} | {r['mat']}{highlight} | {r['e_0k']:.4f} | {r['e_300k']:.4f} "
            f"| {r['delta']:+.4f} | {r['rank_300k']} | {rc_str} |"
        )
    md.append("")

    # Limitations section
    md.append("## Methodology Notes")
    md.append("")
    md.append("- **0 K**: Ground-state DFT formation enthalpies with MP2020 compatibility corrections")
    md.append("- **300 K**: SISSO-based Gibbs free energy (Bartel et al. 2018) via `GibbsComputedStructureEntry`")
    md.append("- For 11/41 gases (BCl3, BF3, CCl4, HBr, HCl, HF, NF3, SF6, SiCl4, SiF4, WF6), NIST-JANAF experimental data is used")
    md.append("- SISSO was trained on crystalline solids \u2014 approximate for gas-phase molecules")
    md.append("- Elemental diatomics (F\u2082, Cl\u2082, Br\u2082) get 0 Gibbs correction by convention; gas-phase entropy NOT captured")
    md.append("- Minimum Gibbs temperature is 300 K (pymatgen constraint), not 298.15 K")
    md.append("")

    md_path = os.path.join(OUTPUT_DIR, "Comparison_0K_vs_300K.md")
    with open(md_path, 'w') as f:
        f.write("\n".join(md))
    print(f"Saved: {md_path}")

    # ── 2. Scatter plot: E_0K vs E_300K ───────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 9))

    e0_vals = [r["e_0k"] for r in rows]
    e3_vals = [r["e_300k"] for r in rows]
    colors = [get_halogen_color(r["mat"]) for r in rows]

    ax.scatter(e0_vals, e3_vals, c=colors, s=60, edgecolors='white', linewidths=0.5, zorder=3)

    # Label points
    for r in rows:
        offset_x = 0.02
        offset_y = 0.02
        ax.annotate(r["mat"], (r["e_0k"], r["e_300k"]),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=6, alpha=0.8)

    # y=x reference line
    lim_min = min(min(e0_vals), min(e3_vals)) - 0.2
    lim_max = max(max(e0_vals), max(e3_vals)) + 0.2
    ax.plot([lim_min, lim_max], [lim_min, lim_max], '--', color='gray', linewidth=1, alpha=0.6, label='y = x (no change)')

    ax.set_xlabel('Reaction energy at 0 K (eV/atom)', fontsize=12)
    ax.set_ylabel('Reaction energy at 300 K (eV/atom)', fontsize=12)
    ax.set_title('0 K vs 300 K Interface Reaction Energy\n(points above y=x line = less negative at 300 K)', fontsize=13, fontweight='bold')
    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)
    ax.set_aspect('equal')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Halogen family legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2563eb', label='Fluorine'),
        Patch(facecolor='#059669', label='Chlorine'),
        Patch(facecolor='#ea580c', label='Bromine'),
        Patch(facecolor='#dc2626', label='Iodine'),
        Patch(facecolor='#8b5cf6', label='Mixed halogen'),
    ]
    ax.legend(handles=legend_elements + [plt.Line2D([0], [0], linestyle='--', color='gray', label='y = x')],
              loc='upper left', fontsize=8, framealpha=0.9)

    scatter_path = os.path.join(OUTPUT_DIR, "Comparison_scatter_0K_vs_300K.png")
    plt.savefig(scatter_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {scatter_path}")

    # ── 3. Bar chart: ΔE per material ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, max(8, len(rows) * 0.35 + 1)))

    # Sort by delta (largest shift first)
    rows_sorted = sorted(rows, key=lambda r: r["delta"], reverse=True)
    y_pos = np.arange(len(rows_sorted))
    deltas = [r["delta"] for r in rows_sorted]
    labels = [r["mat"] for r in rows_sorted]
    bar_colors = [get_halogen_color(r["mat"]) for r in rows_sorted]

    bars = ax.barh(y_pos, deltas, height=0.7, color=bar_colors, edgecolor='white', linewidth=0.5)

    for i, (d, bar) in enumerate(zip(deltas, bars)):
        x_pos = d + 0.005 if d >= 0 else d - 0.005
        ha = 'left' if d >= 0 else 'right'
        ax.text(x_pos, i, f'{d:+.4f}', va='center', ha=ha, fontsize=7, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('\u0394E = E(300K) - E(0K) (eV/atom)', fontsize=12)
    ax.set_title('Energy Shift: 300 K Gibbs vs 0 K DFT\n(positive = less reactive at 300 K)', fontsize=13, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    bar_path = os.path.join(OUTPUT_DIR, "Comparison_delta_bar_0K_vs_300K.png")
    plt.savefig(bar_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {bar_path}")

    # ── Console summary ───────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"COMPARISON SUMMARY: 0 K vs 300 K")
    print(f"{'='*60}")
    print(f"Average \u0394E:         {avg_delta:+.4f} eV/atom")
    print(f"Largest shift:       {max_delta_row['mat']} ({max_delta_row['delta']:+.4f})")
    print(f"Smallest shift:      {min_delta_row['mat']} ({min_delta_row['delta']:+.4f})")
    print(f"Rank changes >= 3:   {len(big_rank_changes)}")
    if big_rank_changes:
        for r in big_rank_changes:
            direction = "up" if r["rank_change"] > 0 else "down"
            print(f"  {r['mat']}: {r['rank_0k']} -> {r['rank_300k']} ({direction} {abs(r['rank_change'])} places)")
    print(f"{'='*60}")
