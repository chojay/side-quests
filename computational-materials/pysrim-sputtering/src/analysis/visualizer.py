"""
Publication-quality matplotlib figures for SRIM simulation results.

Style presets:
  - 'publication': serif fonts, 300 DPI, suitable for journal figures
  - 'presentation': larger fonts, clean look for slides
"""
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from .metrics import RangeMetrics, DamageMetrics, EnergyPartitioning


# Color palette for ion species
ION_COLORS = {
    'N': '#2176AE',    # Blue
    'Ar': '#D7263D',   # Red
    'O': '#2E8B57',    # Green
    'B': '#F4A261',   # Orange
}

ION_LABELS = {
    'N': 'N⁺',
    'Ar': 'Ar⁺',
    'O': 'O⁺',
    'B': 'B⁺',
}


class SRIMVisualizer:
    """
    Publication-quality figures for SRIM results.

    Parameters
    ----------
    style : str
        'publication' or 'presentation'.
    output_dir : str
        Directory to save figures.
    """

    def __init__(self, style: str = 'publication',
                 output_dir: str = 'output/figures'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._apply_style(style)

    def _apply_style(self, style: str):
        if style == 'publication':
            plt.rcParams.update({
                'font.family': 'serif',
                'font.size': 11,
                'axes.labelsize': 12,
                'axes.titlesize': 13,
                'legend.fontsize': 9,
                'xtick.labelsize': 10,
                'ytick.labelsize': 10,
                'figure.dpi': 300,
                'savefig.dpi': 300,
                'savefig.bbox': 'tight',
                'axes.linewidth': 1.0,
                'lines.linewidth': 1.5,
                'lines.markersize': 5,
            })
        elif style == 'presentation':
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.size': 14,
                'axes.labelsize': 16,
                'axes.titlesize': 18,
                'legend.fontsize': 12,
                'xtick.labelsize': 13,
                'ytick.labelsize': 13,
                'figure.dpi': 150,
                'savefig.dpi': 150,
                'savefig.bbox': 'tight',
                'axes.linewidth': 1.5,
                'lines.linewidth': 2.5,
                'lines.markersize': 8,
            })

    # ── Single simulation plots ─────────────────────────────────

    def plot_range_distribution(
        self, range_df: pd.DataFrame,
        metrics: Optional[RangeMetrics] = None,
        title: str = "", ax=None, save_path: Optional[str] = None,
    ):
        """Plot ion range distribution with Rp annotation."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            fig = ax.figure

        ax.plot(range_df['depth_nm'], range_df['ions_per_A_per_ion'],
                color=ION_COLORS['N'], linewidth=1.5)
        ax.fill_between(range_df['depth_nm'], range_df['ions_per_A_per_ion'],
                        alpha=0.2, color=ION_COLORS['N'])

        if metrics:
            ax.axvline(metrics.Rp_nm, color='red', linestyle='--',
                       linewidth=1, label=f'Rp = {metrics.Rp_nm:.2f} nm')
            ax.axvspan(metrics.Rp_nm - metrics.delta_Rp_nm,
                       metrics.Rp_nm + metrics.delta_Rp_nm,
                       alpha=0.1, color='red',
                       label=f'ΔRp = {metrics.delta_Rp_nm:.2f} nm')
            ax.legend(loc='upper right')

        ax.set_xlabel('Depth [nm]')
        ax.set_ylabel('Ion Distribution [ions/Å/ion]')
        ax.set_title(title or 'Ion Range Distribution')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    def plot_damage_profile(
        self, vacancy_df: pd.DataFrame,
        title: str = "", ax=None, save_path: Optional[str] = None,
    ):
        """Plot vacancy depth profile."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            fig = ax.figure

        depth = vacancy_df['depth_nm'] if 'depth_nm' in vacancy_df else vacancy_df['depth_A'] / 10
        vac_cols = [c for c in vacancy_df.columns
                    if c not in ('depth_A', 'depth_nm')]

        for col in vac_cols[:3]:  # Plot first 3 columns
            ax.plot(depth, vacancy_df[col], label=col, linewidth=1.5)

        ax.set_xlabel('Depth [nm]')
        ax.set_ylabel('Vacancies [vac/Å/ion]')
        ax.set_title(title or 'Damage Depth Profile')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        if len(vac_cols) > 1:
            ax.legend(loc='upper right', fontsize=8)

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    def plot_energy_loss(
        self, ionization_df: pd.DataFrame,
        title: str = "", ax=None, save_path: Optional[str] = None,
    ):
        """Plot electronic vs nuclear stopping vs depth."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            fig = ax.figure

        depth = ionization_df['depth_nm'] if 'depth_nm' in ionization_df else ionization_df['depth_A'] / 10

        if 'ions_ionization' in ionization_df:
            ax.plot(depth, ionization_df['ions_ionization'],
                    label='Electronic (ions)', color=ION_COLORS['N'])
        if 'recoils_ionization' in ionization_df:
            ax.plot(depth, ionization_df['recoils_ionization'],
                    label='Nuclear (recoils)', color=ION_COLORS['Ar'])

        ax.set_xlabel('Depth [nm]')
        ax.set_ylabel('Energy Loss [eV/Å/ion]')
        ax.set_title(title or 'Energy Loss Profile')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend()

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    # ── Parameter sweep plots ───────────────────────────────────

    def plot_rp_vs_energy(
        self, energies_eV: List[float],
        rp_values_nm: List[float],
        straggling_nm: Optional[List[float]] = None,
        ion_symbol: str = "N", target_name: str = "",
        ax=None, save_path: Optional[str] = None,
    ):
        """
        Plot projected range vs ion energy (log-log).

        This is the key deliverable figure.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(7, 5))
        else:
            fig = ax.figure

        color = ION_COLORS.get(ion_symbol, '#333')
        label = ION_LABELS.get(ion_symbol, ion_symbol)

        ax.loglog(energies_eV, rp_values_nm, 'o-',
                  color=color, label=f'{label} → {target_name}',
                  markersize=5, linewidth=1.5)

        if straggling_nm:
            rp = np.array(rp_values_nm)
            strag = np.array(straggling_nm)
            ax.fill_between(energies_eV, rp - strag, rp + strag,
                            alpha=0.15, color=color)

        ax.set_xlabel('Ion Energy [eV]')
        ax.set_ylabel('Projected Range Rp [nm]')
        ax.set_title(f'Projected Range vs Energy  -  {label} → {target_name}')
        ax.legend()
        ax.grid(True, which='both', alpha=0.3)

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    def plot_species_comparison(
        self, species_data: Dict[str, pd.DataFrame],
        energy_eV: float,
        ax=None, save_path: Optional[str] = None,
    ):
        """Overlaid range distributions for multiple ion species."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(7, 5))
        else:
            fig = ax.figure

        for ion_sym, df in species_data.items():
            color = ION_COLORS.get(ion_sym, '#333')
            label = ION_LABELS.get(ion_sym, ion_sym)
            depth = df['depth_nm'] if 'depth_nm' in df else df['depth_A'] / 10
            ax.plot(depth, df['ions_per_A_per_ion'],
                    color=color, label=label, linewidth=1.5)

        ax.set_xlabel('Depth [nm]')
        ax.set_ylabel('Ion Distribution [ions/Å/ion]')
        ax.set_title(f'Ion Species Comparison at {energy_eV:.0f} eV')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend()

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    def plot_sputter_yield_vs_energy(
        self, energies_eV: List[float],
        yields: List[float],
        ion_symbol: str = "N", target_name: str = "SiO2",
        ax=None, save_path: Optional[str] = None,
    ):
        """Plot sputtering yield vs energy."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            fig = ax.figure

        color = ION_COLORS.get(ion_symbol, '#333')
        label = ION_LABELS.get(ion_symbol, ion_symbol)

        ax.plot(energies_eV, yields, 'o-', color=color,
                label=f'{label} → {target_name}', markersize=5)

        ax.set_xlabel('Ion Energy [eV]')
        ax.set_ylabel('Sputtering Yield [atoms/ion]')
        ax.set_title(f'Sputtering Yield  -  {label} → {target_name}')
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    def plot_energy_partitioning_vs_energy(
        self, energies_eV: List[float],
        partitions: List[EnergyPartitioning],
        ax=None, save_path: Optional[str] = None,
    ):
        """Plot electronic/nuclear/phonon fractions vs energy."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            fig = ax.figure

        e_frac = [p.electronic_fraction for p in partitions]
        n_frac = [p.nuclear_fraction for p in partitions]
        p_frac = [p.phonon_fraction for p in partitions]

        ax.semilogx(energies_eV, e_frac, 'o-', color=ION_COLORS['N'],
                     label='Electronic', markersize=4)
        ax.semilogx(energies_eV, n_frac, 's-', color=ION_COLORS['Ar'],
                     label='Nuclear', markersize=4)
        ax.semilogx(energies_eV, p_frac, '^-', color=ION_COLORS['O'],
                     label='Phonon', markersize=4)

        ax.set_xlabel('Ion Energy [eV]')
        ax.set_ylabel('Energy Fraction')
        ax.set_title('Energy Partitioning vs Ion Energy')
        ax.set_ylim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            fig.savefig(os.path.join(self.output_dir, save_path))
            plt.close(fig)
        return ax

    # ── Multi-panel composite figures ───────────────────────────

    def plot_scenario_a_summary(
        self,
        energies_eV: List[float],
        rp_nm: List[float],
        straggling_nm: List[float],
        yields: Optional[List[float]] = None,
        damage_dfs: Optional[Dict[float, pd.DataFrame]] = None,
        partitions: Optional[List[EnergyPartitioning]] = None,
        ion_symbol: str = "N",
        save_path: str = "scenario_a_summary.png",
    ):
        """4-panel summary for target bombardment study."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Panel 1: Rp vs energy
        self.plot_rp_vs_energy(
            energies_eV, rp_nm, straggling_nm,
            ion_symbol=ion_symbol, target_name="SiO₂",
            ax=axes[0, 0]
        )

        # Panel 2: Sputter yield vs energy
        if yields:
            self.plot_sputter_yield_vs_energy(
                energies_eV, yields,
                ion_symbol=ion_symbol, ax=axes[0, 1]
            )
        else:
            axes[0, 1].text(0.5, 0.5, 'No sputtering data',
                            transform=axes[0, 1].transAxes, ha='center')
            axes[0, 1].set_title('Sputtering Yield')

        # Panel 3: Damage profiles at key energies
        if damage_dfs:
            for energy, df in sorted(damage_dfs.items()):
                depth = df['depth_nm'] if 'depth_nm' in df else df['depth_A'] / 10
                vac_cols = [c for c in df.columns
                            if c not in ('depth_A', 'depth_nm')]
                if vac_cols:
                    axes[1, 0].plot(depth, df[vac_cols[0]],
                                    label=f'{energy:.0f} eV')
            axes[1, 0].set_xlabel('Depth [nm]')
            axes[1, 0].set_ylabel('Vacancies [vac/Å/ion]')
            axes[1, 0].set_title('Damage Profiles')
            axes[1, 0].legend(fontsize=8)
            axes[1, 0].set_xlim(left=0)
        else:
            axes[1, 0].text(0.5, 0.5, 'No damage data',
                            transform=axes[1, 0].transAxes, ha='center')

        # Panel 4: Energy partitioning
        if partitions:
            self.plot_energy_partitioning_vs_energy(
                energies_eV, partitions, ax=axes[1, 1]
            )
        else:
            axes[1, 1].text(0.5, 0.5, 'No partitioning data',
                            transform=axes[1, 1].transAxes, ha='center')

        fig.suptitle(
            f'Scenario A: {ION_LABELS.get(ion_symbol, ion_symbol)} → SiO₂ Target',
            fontsize=14, fontweight='bold'
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])

        fig.savefig(os.path.join(self.output_dir, save_path))
        plt.close(fig)
        return fig

    def plot_scenario_b_summary(
        self,
        energies_eV: List[float],
        rp_nm: List[float],
        straggling_nm: List[float],
        species_data: Optional[Dict[str, pd.DataFrame]] = None,
        species_energy_eV: float = 100,
        bias_energies: Optional[List[float]] = None,
        bias_rp_nm: Optional[List[float]] = None,
        bias_labels: Optional[List[str]] = None,
        multilayer_dfs: Optional[Dict[float, pd.DataFrame]] = None,
        ion_symbol: str = "N",
        save_path: str = "scenario_b_summary.png",
    ):
        """4-panel summary for film bombardment study."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Panel 1: Rp vs energy with film thickness reference
        self.plot_rp_vs_energy(
            energies_eV, rp_nm, straggling_nm,
            ion_symbol=ion_symbol, target_name="ITO",
            ax=axes[0, 0]
        )
        axes[0, 0].axhline(1200, color='gray', linestyle=':', alpha=0.5,
                            label='Film thickness (1.2 μm)')

        # Panel 2: Species comparison
        if species_data:
            self.plot_species_comparison(
                species_data, species_energy_eV, ax=axes[0, 1]
            )
        else:
            axes[0, 1].text(0.5, 0.5, 'No species data',
                            transform=axes[0, 1].transAxes, ha='center')

        # Panel 3: Bias voltage effect
        if bias_rp_nm and bias_labels:
            axes[1, 0].bar(range(len(bias_labels)), bias_rp_nm,
                           color=ION_COLORS['N'], alpha=0.8)
            axes[1, 0].set_xticks(range(len(bias_labels)))
            axes[1, 0].set_xticklabels(bias_labels)
            axes[1, 0].set_xlabel('Substrate Bias')
            axes[1, 0].set_ylabel('Projected Range [nm]')
            axes[1, 0].set_title('Bias Voltage Effect on Rp')
        else:
            axes[1, 0].text(0.5, 0.5, 'No bias data',
                            transform=axes[1, 0].transAxes, ha='center')

        # Panel 4: Multilayer penetration
        if multilayer_dfs:
            for thickness, df in sorted(multilayer_dfs.items()):
                depth = df['depth_nm'] if 'depth_nm' in df else df['depth_A'] / 10
                axes[1, 1].plot(depth, df['ions_per_A_per_ion'],
                                label=f'Al₂O₃ = {thickness:.0f} nm')
            axes[1, 1].set_xlabel('Depth [nm]')
            axes[1, 1].set_ylabel('Ion Distribution')
            axes[1, 1].set_title('Al₂O₃ Interlayer Shielding')
            axes[1, 1].legend(fontsize=8)
            axes[1, 1].set_xlim(left=0)
        else:
            axes[1, 1].text(0.5, 0.5, 'No multilayer data',
                            transform=axes[1, 1].transAxes, ha='center')

        fig.suptitle(
            f'Scenario B: {ION_LABELS.get(ion_symbol, ion_symbol)} → ITO Film',
            fontsize=14, fontweight='bold'
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])

        fig.savefig(os.path.join(self.output_dir, save_path))
        plt.close(fig)
        return fig
