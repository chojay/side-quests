#!/usr/bin/env python3
"""
drt_batch.py - headless Distribution of Relaxation Times (DRT) over EIS spectra.

Runs pyimpspec's TR-RBF DRT on a single Gamry .DTA file or a whole folder tree of
them, writing one gamma(tau) CSV per spectrum. Defaults to the bundled synthetic
spectrum so it runs with no real instrument data.

    python drt_batch.py                                  # runs on the bundled synthetic spectrum
    python drt_batch.py --input path/to/spectrum.DTA
    python drt_batch.py --data-dir path/to/folder --out drt_out
"""
import os
import time
import argparse
from tqdm import tqdm
from pyimpspec import parse_data, calculate_drt_tr_rbf


def analyze_drt_save(dta_file_path, out_dir=None):
    file_prefix = os.path.splitext(os.path.basename(dta_file_path))[0]

    datasets = parse_data(dta_file_path)
    if not datasets:
        print(f"No data found in {dta_file_path}")
        return

    data = datasets[0]
    drt_result = calculate_drt_tr_rbf(
        data, mode='complex', lambda_value=-1e-3, rbf_type='gaussian',
        derivative_order=1, rbf_shape='fwhm', shape_coeff=0.5,
        inductance=False, credible_intervals=False, num_samples=10000,
        maximum_symmetry=0.5, timeout=60, num_procs=0)

    output_dir = out_dir or os.path.join(os.path.dirname(dta_file_path) or ".", "DRT_Analysis")
    os.makedirs(output_dir, exist_ok=True)

    tau, gamma = drt_result.get_drt_data()
    csv_file_path = os.path.join(output_dir, f"{file_prefix}_drt_data.csv")
    with open(csv_file_path, "w") as file:
        file.write("Tau,Gamma\n")
        for t, g in zip(tau, gamma):
            file.write(f"{t},{g}\n")
    print(f"DRT data saved as {csv_file_path}")


def process_directory(parent_path, out_dir=None):
    for root, dirs, files in os.walk(parent_path):
        dta_files = [f for f in files if f.lower().endswith(".dta")]
        for dta_file in tqdm(dta_files, desc="Processing DTA files", unit="file"):
            start_time = time.time()
            dta_file_path = os.path.join(root, dta_file)
            print(f"Processing: {dta_file_path}")
            analyze_drt_save(dta_file_path, out_dir=out_dir)
            print(f"Elapsed time for {dta_file}: {time.time() - start_time:.2f} seconds")


def main():
    ap = argparse.ArgumentParser(
        description="Batch DRT (TR-RBF) over Gamry .DTA EIS spectra.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--input", help="a single .DTA spectrum")
    group.add_argument("--data-dir", help="a folder tree of .DTA spectra to walk")
    ap.add_argument("--out", default=None, help="output directory for the DRT CSVs")
    args = ap.parse_args()

    if args.data_dir:
        process_directory(args.data_dir, out_dir=args.out)
    else:
        target = args.input or os.path.join(
            os.path.dirname(__file__), "examples", "synthetic_randles_zarc.DTA")
        analyze_drt_save(target, out_dir=args.out)


if __name__ == "__main__":
    main()
