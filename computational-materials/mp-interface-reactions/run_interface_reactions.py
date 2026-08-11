"""
Interface Reaction Calculator using Materials Project API
=========================================================
Calculates Gibbs free energy of reaction for interface pairs using
pymatgen's InterfacialReactivity module and the Materials Project database.

Usage:
    python run_interface_reactions.py

    Prompts for:
      Material 1 (reference): e.g. Si
      Material 2 (targets):   e.g. Ta2O5, Si3N4, Cu

Outputs:
    - Markdown summary file with reaction table
    - Per-material markdown with convex hull and detailed reactions
    - Interface reaction energy plots (one per pair + combined)
    - Convex hull plots for each chemical system
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import warnings
import time
import traceback

from mp_api.client import MPRester
from pymatgen.analysis.interface_reactions import InterfacialReactivity
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.core import Composition, Element

warnings.filterwarnings('ignore', category=UserWarning)

# ── Configuration ──────────────────────────────────────────────────────
API_KEY = os.environ.get("MP_API_KEY")
if not API_KEY:
    raise SystemExit(
        "Set the MP_API_KEY environment variable to your Materials Project API key "
        "(free at https://next-gen.materialsproject.org/api)."
    )
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_chemsys_from_compositions(c1, c2):
    """Get the combined chemical system string for two compositions."""
    elements = set(c1.elements) | set(c2.elements)
    return "-".join(sorted(el.symbol for el in elements))


def analyze_interface(mpr, ref_formula, mat_formula, compat, temperature=None):
    """
    Analyze interface reactivity between two materials.

    Parameters:
        mpr: MPRester client
        ref_formula: Reference material formula (e.g., "Si")
        mat_formula: Target material formula (e.g., "HF")
        compat: MaterialsProject2020Compatibility instance
        temperature: If set (e.g., 300), use GibbsComputedStructureEntry via
                     use_gibbs parameter. If None or 0, use 0 K DFT energies.

    Returns dict with keys:
        ref, mat, chemsys, kinks_df, minimum_energy, minimum_rxn,
        all_reactions, pd_obj, analyzer, temperature, method, error
    """
    result = {
        "ref": ref_formula,
        "mat": mat_formula,
        "temperature": temperature if temperature else 0,
        "method": "SISSO Gibbs (Bartel 2018)" if temperature else "0 K DFT (MP2020)",
        "error": None,
    }

    try:
        c1 = Composition(ref_formula)
        c2 = Composition(mat_formula)
        chemsys = get_chemsys_from_compositions(c1, c2)
        result["chemsys"] = chemsys

        if temperature:
            # Finite-temperature: use GibbsComputedStructureEntry
            print(f"  Fetching Gibbs entries for system: {chemsys} (T={temperature} K)")
            try:
                all_entries = mpr.get_entries_in_chemsys(
                    chemsys, use_gibbs=int(temperature)
                )
                print(f"  Retrieved {len(all_entries)} Gibbs entries")
                # GibbsComputedStructureEntry already includes corrections —
                # do NOT run compat.process_entries() again
                processed = all_entries
            except Exception as gibbs_err:
                print(f"  WARNING: Gibbs conversion failed ({gibbs_err}), falling back to 0 K")
                result["temperature"] = 0
                result["method"] = "0 K DFT (MP2020) [Gibbs fallback]"
                all_entries = mpr.get_entries_in_chemsys(chemsys)
                processed = compat.process_entries(all_entries)
        else:
            # Standard 0 K workflow
            print(f"  Fetching entries for system: {chemsys}")
            # Pin to the GGA/GGA+U hull: the API default switched to a mixed
            # GGA/R2SCAN hull that MP2020Compatibility (GGA-only) cannot
            # process consistently (terminal entries can vanish, energies mix
            # functionals). See README "known quirk, resolved".
            all_entries = mpr.get_entries_in_chemsys(
                chemsys, additional_criteria={"thermo_types": ["GGA_GGA+U"]}
            )
            print(f"  Retrieved {len(all_entries)} entries")
            # Apply MP2020 compatibility corrections
            processed = compat.process_entries(all_entries)

        print(f"  After processing: {len(processed)} entries")

        if len(processed) < 2:
            result["error"] = f"Insufficient entries in {chemsys} system"
            return result

        # Build phase diagram
        pd_obj = PhaseDiagram(processed)
        result["pd_obj"] = pd_obj
        print(f"  Phase diagram: {len(pd_obj.stable_entries)} stable phases")

        # Run interfacial reactivity analysis
        analyzer = InterfacialReactivity(c1, c2, pd_obj, norm=True, use_hull_energy=False)
        result["analyzer"] = analyzer

        # Get kinks (critical compositions along the mixing line)
        kinks = analyzer.get_kinks()
        # kink tuple: (index, x_fraction, energy_eV_per_atom, Reaction, energy_kJ_per_mol)

        # Get dataframe for clean output
        df = analyzer.get_dataframe()
        result["kinks_df"] = df

        # Find minimum (most negative = most thermodynamically favorable)
        min_tuple = analyzer.minimum  # (x_fraction, min_energy_eV_per_atom)
        result["minimum_energy"] = float(min_tuple[1])

        # Find the reaction at the minimum
        all_reactions = []
        for kink in kinks:
            idx, x_frac, e_ev, rxn, e_kj = kink
            # normalized_repr gives integer stoichiometric coefficients (MP web style)
            try:
                likely_rxn = rxn.normalized_repr
            except Exception:
                likely_rxn = str(rxn)
            all_reactions.append({
                "x": float(x_frac),
                "energy_eV_per_atom": float(e_ev),
                "energy_kJ_per_mol": float(e_kj),
                "reaction": str(rxn),
                "likely_reaction": likely_rxn,
            })
        result["all_reactions"] = all_reactions

        # Find the most favorable reaction (most negative energy, excluding endpoints)
        interior = [r for r in all_reactions if 0 < r["x"] < 1]
        if interior:
            most_favorable = min(interior, key=lambda r: r["energy_eV_per_atom"])
            result["minimum_rxn"] = most_favorable
        else:
            result["minimum_rxn"] = None

        print(f"  Minimum energy: {result['minimum_energy']:.4f} eV/atom")
        if result["minimum_rxn"]:
            print(f"  Most favorable: {result['minimum_rxn']['reaction']}")

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        print(f"  ERROR: {result['error']}")
        traceback.print_exc()

    return result


def plot_interface_energy(result, save_path):
    """Plot reaction energy vs composition with data table below (matching MP web)."""
    if result.get("error") or not result.get("all_reactions"):
        return

    reactions = result["all_reactions"]
    min_rxn = result.get("minimum_rxn")
    min_e = min_rxn["energy_eV_per_atom"] if min_rxn else None

    x_vals = [r["x"] for r in reactions]
    e_vals = [r["energy_eV_per_atom"] for r in reactions]

    # Sort rows by energy (most negative first) for the table
    sorted_rxns = sorted(reactions, key=lambda r: r["energy_eV_per_atom"])

    # Build table data
    col_labels = ["Atomic\nfraction", "Reaction", "E_rxn\n(kJ/mol)", "E_rxn\n(eV/atom)", "Most likely\nreaction?"]
    cell_text = []
    cell_colors = []
    for rxn in sorted_rxns:
        is_ml = (min_e is not None
                 and abs(rxn["energy_eV_per_atom"] - min_e) < 1e-6
                 and 0 < rxn["x"] < 1)
        ml_str = "yes" if is_ml else "no"
        rxn_str = rxn["reaction"].replace("->", "→")
        cell_text.append([
            f'{rxn["x"]:.3f}',
            rxn_str,
            f'{rxn["energy_kJ_per_mol"]:.1f}',
            f'{rxn["energy_eV_per_atom"]:.3f}',
            ml_str,
        ])
        if is_ml:
            cell_colors.append(['#fef3c7'] * 5)
        else:
            cell_colors.append(['white'] * 5)

    n_rows = len(cell_text)
    # Dynamic figure height: plot gets ~5 inches, table gets space below
    row_h_inch = 0.35
    table_height_inch = 0.9 + n_rows * row_h_inch  # header (taller for 2-line labels) + rows + padding
    gap_inch = 1.0  # gap between plot bottom and table top (accounts for x-axis labels)
    plot_height_inch = 5.0
    top_margin = 0.5
    bot_margin = 0.3
    fig_height = top_margin + plot_height_inch + gap_inch + table_height_inch + bot_margin
    fig = plt.figure(figsize=(10, fig_height))

    # Plot axes (in figure fraction coordinates)
    plot_bottom_frac = (bot_margin + table_height_inch + gap_inch) / fig_height
    plot_height_frac = plot_height_inch / fig_height
    ax = fig.add_axes([0.10, plot_bottom_frac, 0.85, plot_height_frac])

    # ── Plot ───────────────────────────────────────────────────────────
    ax.plot(x_vals, e_vals, '-', color='#3b82f6', linewidth=1.5, zorder=2, label='Lines')
    ax.plot(x_vals, e_vals, 'o', color='black', markersize=7, zorder=3, label='Reactions')

    if min_rxn:
        rxn_label = min_rxn["reaction"].replace("->", "→")
        ax.plot(min_rxn["x"], min_rxn["energy_eV_per_atom"],
                '*', color='#8b1a1a', markersize=18, zorder=5, label='Suggested reaction')
        ax.text(0.5, 0.97, rxn_label, transform=ax.transAxes,
                fontsize=9, ha='center', va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#d1d5db', alpha=0.9))

    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.4)
    temp = result.get("temperature", 0)
    temp_label = f" ({temp} K)" if temp else " (0 K DFT)"
    ax.set_xlabel(f'x in x{result["ref"]} + (1-x){result["mat"]}', fontsize=12)
    ax.set_ylabel('Reaction energy (eV/atom)', fontsize=12)
    ax.set_title(f'Interface Reaction: {result["ref"]} | {result["mat"]}{temp_label}', fontsize=14, fontweight='bold')
    ax.set_xlim(-0.02, 1.02)
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.3)

    # ── Table below the plot ───────────────────────────────────────────
    tab_ax = fig.add_axes([0.05, bot_margin / fig_height, 0.90, table_height_inch / fig_height])
    tab_ax.axis('off')

    table = tab_ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellColours=cell_colors,
        colColours=['#e5e7eb'] * 5,
        cellLoc='center',
        loc='upper center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)

    # Column widths: wider for Reaction column
    col_widths = [0.08, 0.48, 0.12, 0.12, 0.12]
    for (row, col), cell in table.get_celld().items():
        cell.set_width(col_widths[col])
        cell.set_edgecolor('#d1d5db')
        if row == 0:  # Header (2-line labels need extra height)
            cell.set_text_props(fontweight='bold', fontsize=8)
            cell.set_height(0.14)
        else:
            cell.set_height(0.08)
        # Bold "yes" in Most likely column
        if col == 4 and row > 0 and cell_text[row - 1][4] == "yes":
            cell.set_text_props(fontweight='bold', color='#991b1b')

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved plot: {save_path}")


def plot_combined(results, save_path, ref_name):
    """Plot all interface reactions on a single combined figure with per-material tables."""
    valid = [r for r in results if not r.get("error") and r.get("all_reactions")]
    if not valid:
        return

    colors = ['#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c',
              '#0891b2', '#be185d', '#854d0e', '#4f46e5', '#15803d']

    # ── Build table data for each material ────────────────────────────
    table_blocks = []  # list of (title, col_labels, cell_text, cell_colors)
    col_labels = ["Atomic\nfraction", "Reaction", "E_rxn\n(kJ/mol)", "E_rxn\n(eV/atom)", "Most likely\nreaction?"]
    for result in valid:
        min_rxn = result.get("minimum_rxn")
        min_e = min_rxn["energy_eV_per_atom"] if min_rxn else None
        sorted_rxns = sorted(result["all_reactions"], key=lambda r: r["energy_eV_per_atom"])
        cell_text = []
        cell_colors = []
        for rxn in sorted_rxns:
            is_ml = (min_e is not None
                     and abs(rxn["energy_eV_per_atom"] - min_e) < 1e-6
                     and 0 < rxn["x"] < 1)
            rxn_str = rxn["reaction"].replace("->", "→")
            cell_text.append([
                f'{rxn["x"]:.3f}',
                rxn_str,
                f'{rxn["energy_kJ_per_mol"]:.1f}',
                f'{rxn["energy_eV_per_atom"]:.3f}',
                "yes" if is_ml else "no",
            ])
            cell_colors.append(['#fef3c7'] * 5 if is_ml else ['white'] * 5)
        title = f'{result["ref"]} | {result["mat"]}'
        table_blocks.append((title, col_labels, cell_text, cell_colors))

    # ── Compute figure layout ─────────────────────────────────────────
    row_h_inch = 0.35
    header_h_inch = 0.55  # header row (2-line labels)
    title_h_inch = 0.45   # section title above each table
    table_gap_inch = 0.3  # gap between consecutive tables

    total_tables_inch = 0.0
    for (title, _, ct, _) in table_blocks:
        total_tables_inch += title_h_inch + header_h_inch + len(ct) * row_h_inch + table_gap_inch

    plot_height_inch = 6.0
    gap_inch = 1.0        # gap between plot bottom and first table
    top_margin = 0.6
    bot_margin = 0.4
    fig_height = top_margin + plot_height_inch + gap_inch + total_tables_inch + bot_margin
    fig = plt.figure(figsize=(11, fig_height))

    # ── Plot axes ─────────────────────────────────────────────────────
    plot_bottom_frac = (bot_margin + total_tables_inch + gap_inch) / fig_height
    plot_height_frac = plot_height_inch / fig_height
    ax = fig.add_axes([0.10, plot_bottom_frac, 0.85, plot_height_frac])

    for i, result in enumerate(valid):
        reactions = result["all_reactions"]
        x_vals = [r["x"] for r in reactions]
        e_vals = [r["energy_eV_per_atom"] for r in reactions]
        color = colors[i % len(colors)]

        label = f'{result["ref"]} | {result["mat"]}'
        ax.plot(x_vals, e_vals, 'o-', color=color, linewidth=2, markersize=6,
                label=label, zorder=3)

        min_rxn = result.get("minimum_rxn")
        if min_rxn:
            ax.plot(min_rxn["x"], min_rxn["energy_eV_per_atom"],
                    'v', color=color, markersize=12, zorder=5)

    # Determine temperature from results (all should share the same temperature)
    temps = set(r.get("temperature", 0) for r in valid)
    temp = max(temps) if temps else 0
    temp_label = f" ({temp} K)" if temp else " (0 K DFT)"

    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
    ax.set_xlabel('Atomic Fraction x (of second material)', fontsize=12)
    ax.set_ylabel('Reaction energy (eV/atom)', fontsize=12)
    ax.set_title(f'Interface Reactions: {ref_name} vs Various Materials{temp_label}',
                 fontsize=14, fontweight='bold')
    ax.set_xlim(-0.02, 1.02)
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

    # ── Tables below the plot (one per material, stacked bottom-up) ──
    col_widths = [0.08, 0.48, 0.12, 0.12, 0.12]
    cursor_inch = bot_margin  # current y position in inches, starts at bottom

    for title, clabels, cell_text, cell_colors in reversed(table_blocks):
        n_rows = len(cell_text)
        block_h_inch = header_h_inch + n_rows * row_h_inch
        block_bottom_frac = cursor_inch / fig_height
        block_h_frac = block_h_inch / fig_height

        # Section title
        title_y_frac = (cursor_inch + block_h_inch + 0.05) / fig_height
        fig.text(0.05, title_y_frac, title, fontsize=10, fontweight='bold',
                 va='bottom', color='#1f2937')

        # Table axes
        tab_ax = fig.add_axes([0.05, block_bottom_frac, 0.90, block_h_frac])
        tab_ax.axis('off')

        table = tab_ax.table(
            cellText=cell_text,
            colLabels=clabels,
            cellColours=cell_colors,
            colColours=['#e5e7eb'] * 5,
            cellLoc='center',
            loc='upper center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)

        for (row, col), cell in table.get_celld().items():
            cell.set_width(col_widths[col])
            cell.set_edgecolor('#d1d5db')
            if row == 0:
                cell.set_text_props(fontweight='bold', fontsize=8)
                cell.set_height(0.14)
            else:
                cell.set_height(0.08)
            if col == 4 and row > 0 and cell_text[row - 1][4] == "yes":
                cell.set_text_props(fontweight='bold', color='#991b1b')

        cursor_inch += block_h_inch + title_h_inch + table_gap_inch

    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved combined plot: {save_path}")


def generate_markdown(results, ref_name, materials_list, temperature=None):
    """Generate markdown summary with tables and reaction details."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    temp = temperature if temperature else 0
    temp_str = f"{temp} K" if temp else "0 K (ground state)"
    method_str = "SISSO Gibbs (Bartel 2018)" if temp else "MP2020 compatibility corrections"

    md = []
    md.append(f"# Interface Reaction Analysis: {ref_name}")
    md.append(f"**Date**: {timestamp}")
    md.append(f"**Reference**: {ref_name}")
    md.append(f"**Materials**: {', '.join(materials_list)}")
    md.append(f"**Temperature**: {temp_str}")
    md.append(f"**Data Source**: Materials Project ({method_str})")
    md.append("")

    # ── Summary Table ──
    md.append("## Summary Table")
    md.append("")
    md.append("| Mat 1 | Mat 2 | Likely Reaction | E_rxn (eV/atom) | E_rxn (kJ/mol) | Stability |")
    md.append("|-------|-------|----------------|-----------------|----------------|-----------|")

    for r in results:
        mat = r["mat"]
        if r.get("error"):
            md.append(f"| {r['ref']} | {mat} | ERROR: {r['error']} | N/A | N/A | Unknown |")
            continue

        min_rxn = r.get("minimum_rxn")
        if min_rxn:
            e_ev = min_rxn["energy_eV_per_atom"]
            e_kj = min_rxn["energy_kJ_per_mol"]
            likely = min_rxn["likely_reaction"].replace("->", "→")

            if e_ev < -0.2:
                stability = "Highly Unstable"
            elif e_ev < -0.05:
                stability = "Unstable"
            elif e_ev < 0:
                stability = "Marginally Unstable"
            else:
                stability = "Stable"

            md.append(f"| {r['ref']} | {mat} | {likely} | {e_ev:.4f} | {e_kj:.1f} | {stability} |")
        else:
            md.append(f"| {r['ref']} | {mat} | No reaction | 0.0000 | 0.0 | Stable |")

    md.append("")

    # ── Detailed Results ──
    md.append("## Detailed Results")
    md.append("")

    for r in results:
        mat = r["mat"]
        md.append(f"### {r['ref']} | {mat}")
        md.append("")

        if r.get("error"):
            md.append(f"**Error**: {r['error']}")
            md.append("")
            continue

        chemsys = r.get("chemsys", "N/A")
        md.append(f"**Chemical System**: {chemsys}")
        md.append(f"**Minimum Reaction Energy**: {r.get('minimum_energy', 'N/A'):.4f} eV/atom")
        md.append("")

        # All kink reactions table (sorted by energy, most negative first — matching MP web)
        reactions = r.get("all_reactions", [])
        min_rxn = r.get("minimum_rxn")
        min_e = min_rxn["energy_eV_per_atom"] if min_rxn else None
        if reactions:
            sorted_rxns = sorted(reactions, key=lambda x: x["energy_eV_per_atom"])
            md.append("| Atomic fraction | Reaction | E_rxn (kJ/mol) | E_rxn (eV/atom) | Most likely reaction? |")
            md.append("|-----------------|----------|---------------:|----------------:|:---------------------:|")
            for rxn in sorted_rxns:
                rxn_str = rxn['reaction'].replace("->", "→")
                is_most_likely = (min_e is not None
                                  and abs(rxn["energy_eV_per_atom"] - min_e) < 1e-6
                                  and 0 < rxn["x"] < 1)
                ml = "**yes**" if is_most_likely else "no"
                md.append(f"| {rxn['x']:.3f} | {rxn_str} | {rxn['energy_kJ_per_mol']:.1f} | {rxn['energy_eV_per_atom']:.3f} | {ml} |")
            md.append("")

        md.append(f"![[{ref_name}_{mat}_interface_rxn.png]]")
        md.append("")

    # Combined plot
    md.append("## Combined Reaction Energy Plot")
    md.append("")
    md.append(f"![[{ref_name}_combined_interface_rxn.png]]")
    md.append("")

    return "\n".join(md)


def plot_convex_hull(pd_obj, chemsys, save_path):
    """Plot the convex hull for a chemical system."""
    try:
        from pymatgen.analysis.phase_diagram import PDPlotter
        plotter = PDPlotter(pd_obj, show_unstable=0.1, backend='matplotlib')
        ax = plotter.get_plot(label_stable=True, label_unstable=False)
        fig = ax.figure
        fig.set_size_inches(8, 6)
        ax.set_title(f"Convex Hull: {chemsys} System", fontsize=14, fontweight='bold')
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved convex hull: {save_path}")
    except Exception as e:
        print(f"  Warning: Could not plot convex hull for {chemsys}: {e}")


def generate_per_material_markdown(result, ref_name, pd_obj, temperature=None):
    """Generate a detailed markdown file for a single material interface."""
    mat = result["mat"]
    chemsys = result.get("chemsys", "N/A")
    temp = temperature if temperature else result.get("temperature", 0)
    temp_str = f"{temp} K" if temp else "0 K (ground state)"
    method_str = "SISSO Gibbs (Bartel 2018)" if temp else "MP2020 compatibility"

    md = []
    md.append(f"# Interface Reaction: {ref_name} | {mat}")
    md.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Chemical System**: {chemsys}")
    md.append(f"**Temperature**: {temp_str}")
    md.append(f"**Data Source**: Materials Project ({method_str})")
    md.append("")

    if result.get("error"):
        md.append(f"**Error**: {result['error']}")
        return "\n".join(md)

    # Stable phases
    if pd_obj:
        md.append(f"**Number of Entries**: {len(pd_obj.all_entries)}")
        md.append(f"**Stable Phases**: {len(pd_obj.stable_entries)}")
        md.append("")
        md.append("## Stable Phases in System")
        md.append("")
        md.append("| Phase | Energy (eV/atom) | Formation Energy (eV/atom) |")
        md.append("|-------|-----------------|---------------------------|")
        for entry in sorted(pd_obj.stable_entries, key=lambda e: e.energy_per_atom):
            form_e = pd_obj.get_form_energy_per_atom(entry)
            md.append(f"| {entry.composition.reduced_formula} | {entry.energy_per_atom:.4f} | {form_e:.4f} |")
        md.append("")

    md.append("## Convex Hull")
    md.append("")
    md.append(f"![[{ref_name}_{mat}_convex_hull.png]]")
    md.append("")

    # Reaction summary
    md.append("## Interface Reaction Analysis")
    md.append("")

    min_rxn = result.get("minimum_rxn")
    if min_rxn:
        e = min_rxn["energy_eV_per_atom"]
        if e < -0.2:
            stab = "Highly Unstable"
        elif e < -0.05:
            stab = "Unstable"
        elif e < 0:
            stab = "Marginally Unstable"
        else:
            stab = "Stable"

        likely = min_rxn.get('likely_reaction', min_rxn['reaction']).replace('->', '→')
        md.append(f"**Likely Reaction**: {likely}")
        md.append(f"**Reaction Energy**: {min_rxn['energy_eV_per_atom']:.4f} eV/atom ({min_rxn['energy_kJ_per_mol']:.1f} kJ/mol)")
        md.append(f"**Stability Assessment**: {stab}")
    else:
        md.append("**No reaction predicted** (interface is stable)")
    md.append("")

    # All kink reactions (sorted by energy, matching MP web format)
    reactions = result.get("all_reactions", [])
    min_rxn = result.get("minimum_rxn")
    min_e = min_rxn["energy_eV_per_atom"] if min_rxn else None
    if reactions:
        sorted_rxns = sorted(reactions, key=lambda x: x["energy_eV_per_atom"])
        md.append("### All Critical Compositions")
        md.append("")
        md.append("| Atomic fraction | Reaction | E_rxn (kJ/mol) | E_rxn (eV/atom) | Most likely reaction? |")
        md.append("|-----------------|----------|---------------:|----------------:|:---------------------:|")
        for r in sorted_rxns:
            rxn_str = r['reaction'].replace("->", "→")
            is_most_likely = (min_e is not None
                              and abs(r["energy_eV_per_atom"] - min_e) < 1e-6
                              and 0 < r["x"] < 1)
            ml = "**yes**" if is_most_likely else "no"
            md.append(f"| {r['x']:.3f} | {rxn_str} | {r['energy_kJ_per_mol']:.1f} | {r['energy_eV_per_atom']:.3f} | {ml} |")
        md.append("")

    md.append("### Reaction Energy Plot")
    md.append("")
    md.append(f"![[{ref_name}_{mat}_interface_rxn.png]]")
    md.append("")

    # Interpretation
    md.append("## Interpretation")
    md.append("")
    if min_rxn and min_rxn["energy_eV_per_atom"] < -0.2:
        products = min_rxn["reaction"].split("->")[-1].strip() if "->" in min_rxn["reaction"] else "decomposition products"
        md.append(
            f"{ref_name} is thermodynamically **highly reactive** with {mat}. "
            f"The predicted decomposition products are **{products}**, "
            f"with a driving force of {abs(min_rxn['energy_eV_per_atom']):.3f} eV/atom "
            f"({abs(min_rxn['energy_kJ_per_mol']):.1f} kJ/mol). "
            f"This reaction is expected to proceed spontaneously at room temperature."
        )
    elif min_rxn and min_rxn["energy_eV_per_atom"] < 0:
        md.append(f"{ref_name} shows moderate reactivity with {mat}. A passivation layer may form.")
    else:
        md.append(f"The {ref_name} | {mat} interface appears thermodynamically stable.")
    md.append("")

    return "\n".join(md)


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  Interface Reaction Calculator (Materials Project API)")
    print("=" * 70)

    # ── User Input ─────────────────────────────────────────────────────
    ref_input = input("\nMaterial 1 (reference) [default: Si]: ").strip()
    REFERENCE_MATERIAL = ref_input if ref_input else "Si"

    mat_input = input(
        f"Material 2 (comma-separated) [default: Ta2O5, Si3N4]: "
    ).strip()
    if mat_input:
        MATERIALS_LIST = [m.strip() for m in mat_input.split(",") if m.strip()]
    else:
        MATERIALS_LIST = ["Ta2O5", "Si3N4"]

    temp_input = input(
        f"Temperature [default: 0 K, enter 300 for Gibbs correction]: "
    ).strip()
    TEMPERATURE = int(temp_input) if temp_input else None

    print(f"\nReference    : {REFERENCE_MATERIAL}")
    print(f"Targets      : {', '.join(MATERIALS_LIST)}")
    temp_display = f"{TEMPERATURE} K (Gibbs)" if TEMPERATURE else "0 K (DFT ground state)"
    print(f"Temperature  : {temp_display}")
    print("=" * 70)

    compat = MaterialsProject2020Compatibility()
    results = []

    with MPRester(API_KEY) as mpr:
        for mat in MATERIALS_LIST:
            print(f"\n{'─' * 50}")
            print(f"Analyzing: {REFERENCE_MATERIAL} | {mat}")
            print(f"{'─' * 50}")

            result = analyze_interface(mpr, REFERENCE_MATERIAL, mat, compat, temperature=TEMPERATURE)
            results.append(result)

            # Plot individual interface reaction energy
            if not result.get("error"):
                plot_path = f"{OUTPUT_DIR}/{REFERENCE_MATERIAL}_{mat}_interface_rxn.png"
                plot_interface_energy(result, plot_path)

                # Plot convex hull
                pd_obj = result.get("pd_obj")
                chemsys = result.get("chemsys", "")
                if pd_obj:
                    hull_path = f"{OUTPUT_DIR}/{REFERENCE_MATERIAL}_{mat}_convex_hull.png"
                    plot_convex_hull(pd_obj, chemsys, hull_path)

                # Per-material markdown
                per_md = generate_per_material_markdown(result, REFERENCE_MATERIAL, pd_obj, temperature=TEMPERATURE)
                per_md_path = f"{OUTPUT_DIR}/{REFERENCE_MATERIAL}_{mat}_interface_analysis.md"
                with open(per_md_path, 'w') as f:
                    f.write(per_md)
                print(f"  Saved per-material markdown: {per_md_path}")

            time.sleep(0.5)  # Rate limit courtesy

    # Combined plot
    print(f"\n{'─' * 50}")
    print("Generating combined plot...")
    plot_combined(results, f"{OUTPUT_DIR}/{REFERENCE_MATERIAL}_combined_interface_rxn.png", REFERENCE_MATERIAL)

    # Generate summary markdown
    print("\nGenerating markdown summary...")
    md_content = generate_markdown(results, REFERENCE_MATERIAL, MATERIALS_LIST, temperature=TEMPERATURE)

    temp_suffix = f"_{TEMPERATURE}K" if TEMPERATURE else "_0K"
    md_path = f"{OUTPUT_DIR}/{REFERENCE_MATERIAL}_interface_reactions{temp_suffix}_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(md_path, 'w') as f:
        f.write(md_content)
    print(f"Saved summary markdown: {md_path}")

    # Print summary to console
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    for r in results:
        mat = r["mat"]
        if r.get("error"):
            print(f"  {r['ref']} | {mat}: ERROR - {r['error']}")
        elif r.get("minimum_rxn"):
            mr = r["minimum_rxn"]
            print(f"  {r['ref']} | {mat}: {mr['energy_eV_per_atom']:.4f} eV/atom | {mr['reaction']}")
        else:
            print(f"  {r['ref']} | {mat}: No reaction (stable)")
    print("=" * 70)
