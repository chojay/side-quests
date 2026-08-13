#!/usr/bin/env python3
"""
sem_sr.py - Super-resolution for grayscale SEM images on Apple Silicon.
Supports: realesrgan | bsrgan | swinir | swin2sr | hat
Example:
    python sem_sr.py examples/dummy_sem_image.tif --model realesrgan --out sr.png
"""
import os, sys, argparse, urllib.request, tempfile, cv2, tifffile, numpy as np, torch
from PIL import Image
torch.set_grad_enabled(False)

# ------------------------- device selection -------------------------
device = (
    torch.device("cuda") if torch.cuda.is_available() else
    torch.device("mps")  if torch.backends.mps.is_available() else
    torch.device("cpu")
)
print(f"[INFO] Using device: {device}")

# ------------------------- model loaders ----------------------------
def load_realesrgan(scale=4):
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=23, num_grow_ch=32, scale=scale)
    weight_url = f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x{scale}plus.pth"
    weight_path = os.path.join(tempfile.gettempdir(), os.path.basename(weight_url))
    if not os.path.exists(weight_path):
        print(f"[DL] Real-ESRGAN weights -> {weight_path}")
        urllib.request.urlretrieve(weight_url, weight_path)
    return RealESRGANer(scale=scale, model_path=weight_path,
                        model=model, device=device, tile=0, tile_pad=10, half=False)

def load_bsrgan():
    from bsrgan import BSRGAN
    return BSRGAN(weights='kadirnar/bsrgan', device=device)

def load_swinir():
    from basicsr.archs.swinir_arch import SwinIR
    weights_url = ("https://github.com/JingyunLiang/SwinIR/releases/"
                   "download/v0.0/003_realSR_BSRGAN_DFOWM54_SwinIR-L_x4_GAN.pth")
    weights = os.path.join(tempfile.gettempdir(), "swinir_x4.pth")
    if not os.path.exists(weights):
        print(f"[DL] SwinIR weights -> {weights}")
        urllib.request.urlretrieve(weights_url, weights)
    model = SwinIR(upscale=4, in_chans=3, img_size=64, window_size=8,
                   img_range=1., depths=[6,6,6,6], embed_dim=180,
                   num_heads=[6,6,6,6], mlp_ratio=2,
                   upsampler='nearest+conv', resi_connection='1conv')
    model.load_state_dict(torch.load(weights, map_location='cpu'), strict=True)
    model.eval().to(device)
    return model

def load_swin2sr():
    from transformers import Swin2SRForImageSuperResolution
    model = Swin2SRForImageSuperResolution.from_pretrained(
        "caidas/swin2sr-lightweight-x4-64", torch_dtype=torch.float32
    ).to(device)
    return model

def load_hat():
    from basicsr.utils.download_util import load_file_from_url
    from basicsr.archs.hat_arch import HAT
    ckpt = load_file_from_url(
        "https://github.com/XPixelGroup/HAT/releases/download/v1.0.0/HAT_SRx4_DF2K.pth",
        model_dir=os.path.join(tempfile.gettempdir(), "hat"), progress=True)
    model = HAT(upscale=4, in_chans=3, img_size=64, window_size=16,
                img_range=1., depth=28, embed_dim=192, num_heads=6,
                mlp_ratio=4, upsampler='nearest+conv')
    model.load_state_dict(torch.load(ckpt, map_location='cpu'), strict=True)
    model.eval().to(device)
    return model

# mapping
MODEL_ZOO = {
    'realesrgan': (load_realesrgan, True),   # tuple: loader, returns_upsampler?
    'bsrgan'    : (load_bsrgan,    False),
    'swinir'    : (load_swinir,    False),
    'swin2sr'   : (load_swin2sr,   False),
    'hat'       : (load_hat,       False)
}

# ------------------------- helpers ----------------------------------
def read_sem(path):
    img = tifffile.imread(path) if path.lower().endswith(('.tif', '.tiff')) else cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img.ndim == 2:            # grayscale
        gray = img
    elif img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Unsupported image format.")
    return gray

def to_3ch(gray):
    return np.stack([gray, gray, gray], axis=2)

def save_gray(path, arr):
    if arr.ndim == 3:            # RGB 0-255
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(path, arr)

def upscale(img_gray, model_name):
    loader, returns_upsampler = MODEL_ZOO[model_name]
    model = loader()
    rgb = to_3ch(img_gray)
    if model_name == 'realesrgan':
        upsampler = model   # RealESRGANer
        sr_rgb, _ = upsampler.enhance(rgb, outscale=upsampler.scale)
    elif model_name == 'bsrgan':
        sr_rgb = model.predict_array(rgb)     # BSRGAN wrapper
    elif model_name == 'swin2sr':
        import torch.nn.functional as F
        tensor = torch.from_numpy(rgb).permute(2,0,1).unsqueeze(0).float().to(device) / 255.
        sr = model(pixel_values=tensor).reconstruction
        sr_rgb = (sr.squeeze().clamp(0,1).cpu().permute(1,2,0).numpy()*255).astype(np.uint8)
    else:                                      # swinir | hat
        tensor = torch.from_numpy(rgb).permute(2,0,1).unsqueeze(0).float().to(device) / 255.
        sr = model(tensor)
        sr_rgb = (sr.squeeze().clamp(0,1).cpu().permute(1,2,0).numpy()*255).astype(np.uint8)
    return sr_rgb

# ------------------------- main -------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input",  help="SEM grayscale image (tif/png)")
    parser.add_argument("--model", choices=list(MODEL_ZOO.keys()),
                        default="realesrgan", help="which SR engine to use")
    parser.add_argument("--out",   default="sr_output.png",
                        help="output filename (PNG)")
    args = parser.parse_args()

    img_gray = read_sem(args.input)
    print(f"[INFO] Input shape: {img_gray.shape}")

    sr_rgb = upscale(img_gray, args.model)
    save_gray(args.out, sr_rgb)
    print(f"[DONE] Saved super-resolved image -> {args.out}")

if __name__ == "__main__":
    main()
