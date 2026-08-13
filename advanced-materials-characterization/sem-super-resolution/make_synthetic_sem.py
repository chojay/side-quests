#!/usr/bin/env python3
"""
Generate a synthetic grayscale "SEM-like" micrograph so the tools in this folder
run end-to-end with no real instrument data.

The image is deliberately fake: a blurred noise background with scattered bright
"particles" and light Poisson noise, plus a dark info bar along the bottom edge
(the way real SEM software burns in scale/HV/magnification). Nothing here is a
real sample. Regenerate any time with:

    python make_synthetic_sem.py --out examples/dummy_sem_image.tif

Requires: numpy, scipy, tifffile.
"""
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter
import tifffile


def make_synthetic_sem(size=256, n_particles=90, seed=0):
    rng = np.random.default_rng(seed)

    # blurred noise background (fine "surface texture")
    bg = gaussian_filter(rng.normal(0.45, 0.18, (size, size)), sigma=2.0)

    # scattered bright particles of varying radius and intensity
    img = bg.copy()
    yy, xx = np.mgrid[0:size, 0:size]
    for _ in range(n_particles):
        cy, cx = rng.uniform(0, size, 2)
        r = rng.uniform(2.5, 9.0)
        amp = rng.uniform(0.25, 0.7)
        img += amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r ** 2))

    # normalize to 0..1, add light shot noise, clip
    img = (img - img.min()) / (img.ptp() + 1e-9)
    img = np.clip(img + rng.normal(0, 0.03, img.shape), 0, 1)
    gray = (img * 235).astype(np.uint8)  # leave headroom below 255

    # burn in a dark info bar along the bottom (mimics SEM metadata strip)
    bar_h = max(12, size // 12)
    gray[size - bar_h:, :] = 18
    # a few light "tick" marks on the bar, purely cosmetic
    for x in range(size // 8, size, size // 8):
        gray[size - bar_h + 3: size - 3, x:x + 2] = 150

    return gray


def main():
    ap = argparse.ArgumentParser(description="Write a synthetic grayscale SEM TIFF.")
    ap.add_argument("--out", default="examples/dummy_sem_image.tif")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    gray = make_synthetic_sem(size=args.size, seed=args.seed)
    # write a plain, single-channel TIFF with no descriptive metadata
    tifffile.imwrite(args.out, gray, photometric="minisblack")
    print(f"[DONE] wrote {args.out}  shape={gray.shape}  dtype={gray.dtype}")


if __name__ == "__main__":
    main()
