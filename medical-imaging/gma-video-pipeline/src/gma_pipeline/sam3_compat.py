"""SAM 3 on Apple Silicon compatibility layer.

SAM 3 imports `triton` (and `triton.language`) at module load. Triton has no
macOS arm64 wheels at all as of May 2026, which makes SAM 3 fail to import
even when CUDA paths would never be hit. This module:

1. Installs a stub `triton` and `triton.language` into sys.modules so that
   SAM 3 imports succeed. The stub provides only the surface SAM 3 touches
   at module load (decorators, Config, cdiv); kernel bodies decorated with
   @triton.jit are never executed because we override their callers.

2. Monkey-patches `sam3.model.edt.edt_triton` with a cv2-based implementation.
   The SAM 3 author explicitly documents that edt_triton "should be equivalent
   to a batched version of cv2.distanceTransform(input, cv2.DIST_L2, 0)", so
   the swap is semantically faithful.

3. Same patch is applied wherever else SAM 3 imports edt_triton from
   (currently just sam3.model.sam3_tracker_utils).

Call install_triton_stub() BEFORE `import sam3`. Then call patch_edt() AFTER
the relevant SAM 3 submodules have been imported.

Caveat: this only covers the EDT operation. If SAM 3 calls other
triton-decorated kernels at runtime (sigmoid_focal_loss is training-only;
perflib/triton/{nms,connected_components} may be inference-time), those will
fail when actually invoked. Empirical testing will tell us which surface
the image predictor actually touches.
"""

from __future__ import annotations

import logging
import sys
import types

import cv2
import numpy as np
import torch

logger = logging.getLogger(__name__)

_INSTALLED = False


class _StubFinder:
    """Meta path finder that creates stub modules for any triton.* import.

    PyTorch's inductor pokes at triton.backends.compiler and similar paths even
    when MPS is the only backend used. We accept any triton submodule import
    and synthesize an empty stub that satisfies Python's import machinery.
    """

    def find_spec(self, fullname, path, target=None):
        if fullname == "triton" or fullname.startswith("triton."):
            from importlib.machinery import ModuleSpec

            spec = ModuleSpec(fullname, loader=_StubLoader(), is_package=True)
            return spec
        return None


class _StubLoader:
    def create_module(self, spec):
        return None  # use default module creation

    def exec_module(self, module):
        module._is_gma_stub = True
        module.__path__ = []  # mark as package so subpackages can be loaded
        # Provide commonly accessed attributes with no-op semantics
        if module.__name__ == "triton":
            module.jit = lambda fn=None, **_kw: (fn if fn is not None else (lambda f: f))
            module.heuristics = lambda *_a, **_kw: (lambda f: f)
            module.autotune = lambda *_a, **_kw: (lambda f: f)
            module.Config = lambda *_a, **_kw: None
            module.cdiv = lambda a, b: (a + b - 1) // b
            module.next_power_of_2 = lambda n: 1 << (max(int(n) - 1, 0)).bit_length()


def install_triton_stub() -> None:
    """Install a minimal triton stub via a meta path finder. Idempotent."""
    global _INSTALLED
    if _INSTALLED:
        return
    if "triton" in sys.modules:
        existing = sys.modules["triton"]
        if hasattr(existing, "jit") and not getattr(existing, "_is_gma_stub", False):
            logger.info("Real triton already loaded, not replacing")
            _INSTALLED = True
            return
        # Clear stale stubs so the finder gets to recreate them as packages.
        for mod in list(sys.modules):
            if mod == "triton" or mod.startswith("triton."):
                del sys.modules[mod]

    # Install finder if not already present
    if not any(isinstance(f, _StubFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _StubFinder())

    # Eagerly create triton + triton.language with the surface SAM 3 needs
    triton = types.ModuleType("triton")
    triton._is_gma_stub = True
    triton.__path__ = []

    def _decorator_factory(fn=None, **_kw):
        if fn is None:
            return lambda f: f
        return fn

    triton.jit = _decorator_factory
    triton.heuristics = lambda *_a, **_kw: (lambda f: f)
    triton.autotune = lambda *_a, **_kw: (lambda f: f)
    triton.Config = lambda *_a, **_kw: None
    triton.cdiv = lambda a, b: (a + b - 1) // b
    triton.next_power_of_2 = lambda n: 1 << (max(int(n) - 1, 0)).bit_length()

    triton_lang = types.ModuleType("triton.language")
    triton_lang._is_gma_stub = True

    class _ConstexprMeta(type):
        def __getitem__(cls, item):
            return cls

    class constexpr(metaclass=_ConstexprMeta):
        pass

    triton_lang.constexpr = constexpr
    triton_lang.tensor = type("tensor", (), {})
    triton_lang.dtype = type("dtype", (), {})

    # Make every other tl.<name> a no-op callable so kernel-body accesses don't
    # raise AttributeError at module parse time. Kernel bodies are never run.
    class _NoOp:
        def __init__(self, name="_noop"):
            self._name = name

        def __call__(self, *args, **kwargs):
            return None

        def __getattr__(self, name):
            return _NoOp(name)

    common_names = [
        "program_id", "arange", "load", "store", "where", "minimum", "maximum",
        "zeros", "ones", "full", "sum", "min", "max", "sqrt", "log", "exp",
        "float16", "float32", "float64", "int1", "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64", "bfloat16",
        "cdiv", "static_assert", "static_print", "libdevice",
        "cast", "ravel", "atomic_min", "atomic_max", "atomic_add",
        "debug_barrier", "reshape", "broadcast_to", "expand_dims", "view",
        "math", "extra", "core", "advance", "make_block_ptr",
    ]
    for name in common_names:
        setattr(triton_lang, name, _NoOp(name))

    triton.language = triton_lang
    sys.modules["triton"] = triton
    sys.modules["triton.language"] = triton_lang
    _INSTALLED = True
    logger.info("Installed triton stub (no real triton on macOS arm64)")


def edt_cv2(data: torch.Tensor) -> torch.Tensor:
    """Drop-in replacement for sam3.model.edt.edt_triton using cv2.distanceTransform.

    Original signature: data is (B, H, W) binary tensor, returns (B, H, W) float32 EDT.
    SAM 3 asserts data.is_cuda; we remove that assertion implicitly by replacing
    the function.
    """
    assert data.dim() == 3, f"Expected (B, H, W), got shape {tuple(data.shape)}"
    device = data.device
    dtype = torch.float32
    B, H, W = data.shape
    data_np = data.detach().to(torch.uint8).cpu().numpy()
    output = np.zeros((B, H, W), dtype=np.float32)
    for b in range(B):
        binary = (data_np[b] > 0).astype(np.uint8)
        # cv2.DIST_L2 with mask size 0 means precise; matches SAM 3's docstring claim
        output[b] = cv2.distanceTransform(binary, cv2.DIST_L2, 0)
    return torch.from_numpy(output).to(device=device, dtype=dtype)


def patch_edt() -> None:
    """Replace edt_triton with our cv2 implementation in every SAM 3 module
    that imported it. Call this AFTER importing sam3 (or its submodules).
    """
    import sam3.model.edt as _edt_mod

    _edt_mod.edt_triton = edt_cv2

    try:
        import sam3.model.sam3_tracker_utils as _tu_mod

        _tu_mod.edt_triton = edt_cv2
    except ImportError:
        pass
    logger.info("Patched sam3.model.edt.edt_triton with cv2-based implementation")


def addmm_act_unfused(activation, linear, mat1):
    """Drop-in replacement for sam3.perflib.fused.addmm_act using plain PyTorch.

    SAM 3's original calls torch.ops.aten._addmm_activation with BF16 inputs,
    which (a) MPS doesn't support cleanly (the matmul accumulator dtype check
    in Metal fails) and (b) is unavailable on CPU at the right dtype combos
    when CUDA autocast is disabled.

    Plain unfused implementation: linear projection then activation. Slower
    than the fused CUDA kernel but correct on every backend.
    """
    out = torch.nn.functional.linear(mat1, linear.weight, linear.bias)
    if activation in (torch.nn.functional.gelu, torch.nn.GELU):
        return torch.nn.functional.gelu(out)
    if activation in (torch.nn.functional.relu, torch.nn.ReLU):
        return torch.nn.functional.relu(out)
    raise ValueError(f"Unexpected activation {activation}")


def patch_fused_ops() -> None:
    """Replace sam3.perflib.fused.addmm_act with the unfused PyTorch fallback.

    Must be called AFTER importing sam3 but BEFORE building the model (the
    model captures the function reference at construction time in some paths,
    so patching the module attribute then rebuilding is the safe order).
    """
    import sam3.perflib.fused as _fused

    _fused.addmm_act = addmm_act_unfused
    # Some modules import addmm_act directly into their namespace; patch those too.
    import sam3.model.vitdet as _vitdet

    if hasattr(_vitdet, "addmm_act"):
        _vitdet.addmm_act = addmm_act_unfused
    logger.info("Patched sam3.perflib.fused.addmm_act with unfused PyTorch fallback")


def patch_cuda_strings(target_device: str = "mps") -> int:
    """Patch hardcoded device='cuda' strings in the installed SAM 3 package.

    SAM 3 was written assuming CUDA is always present. Several module-level
    initializers and default arguments are hardcoded. We rewrite the installed
    .py files in-place so they use `target_device` instead.

    Returns the number of files modified. Idempotent.
    """
    import sam3 as _sam3

    sam3_root = _sam3.__path__[0]
    marker = f"# GMA_PIPELINE_PATCHED_FOR_{target_device.upper()}"
    files_to_patch = [
        "model/position_encoding.py",
        "model/decoder.py",
        "model/vl_combiner.py",
        "model/sam3_image_processor.py",
    ]
    modified = 0
    for rel in files_to_patch:
        path = f"{sam3_root}/{rel}"
        with open(path) as fh:
            src = fh.read()
        if marker in src:
            continue
        new_src = src.replace('device="cuda"', f'device="{target_device}"')
        new_src = new_src.replace("device='cuda'", f"device='{target_device}'")
        if new_src == src:
            continue
        new_src = f"{marker}\n" + new_src
        with open(path, "w") as fh:
            fh.write(new_src)
        modified += 1
        logger.info("Patched %s for device=%s", path, target_device)
    return modified


def patch_mps_incompat() -> int:
    """Strip CUDA-only memory optimizations that fail on MPS.

    Specifically:
    - `.pin_memory()` calls become no-ops (pin_memory is a CUDA-only async
      H2D transfer optimization; on MPS it raises or causes downstream
      "storage device mismatch" errors).
    - `.cuda(non_blocking=True)` becomes `.to(device, non_blocking=False)`
      so the call targets whatever device is being used at runtime.
    - `non_blocking=True` in `.to(...)` calls is left alone (PyTorch ignores
      it on backends that don't support it).

    Returns number of files modified. Idempotent via marker comment.
    """
    import sam3 as _sam3

    sam3_root = _sam3.__path__[0]
    marker = "# GMA_PIPELINE_PATCHED_MPS_INCOMPAT"
    files_to_patch = [
        "model/geometry_encoders.py",
        "model/sam3_multiplex_base.py",
        "model/sam3_tracker_base.py",
        "model/sam3_tracking_predictor.py",
        "model/sam3_video_inference.py",
        "model/sam3_multiplex_tracking.py",
    ]
    modified = 0
    for rel in files_to_patch:
        path = f"{sam3_root}/{rel}"
        try:
            with open(path) as fh:
                src = fh.read()
        except FileNotFoundError:
            continue
        if marker in src:
            continue
        # Strip .pin_memory() and .pin_memory(device) - common chained patterns
        new_src = src
        for chained in [".pin_memory()\n", ".pin_memory(device)\n"]:
            new_src = new_src.replace(chained, "\n")
        new_src = new_src.replace(".pin_memory()", "")
        new_src = new_src.replace(".pin_memory(device)", "")
        # Replace .cuda(non_blocking=True) with no-op (tensor will be moved by
        # the surrounding device parameter in the caller).
        new_src = new_src.replace(".cuda(non_blocking=True)", "")
        new_src = new_src.replace(".cuda()", "")
        if new_src == src:
            continue
        new_src = f"{marker}\n" + new_src
        with open(path, "w") as fh:
            fh.write(new_src)
        modified += 1
        logger.info("Patched MPS-incompat in %s", path)
    return modified


def install_and_patch(target_device: str = "mps") -> None:
    """Convenience: install stub, patch source files, import sam3, patch edt.

    Order matters: source files must be patched before sam3 modules are
    imported so the new strings take effect.
    """
    install_triton_stub()
    n_cuda = patch_cuda_strings(target_device=target_device)
    n_mps = patch_mps_incompat()
    if n_cuda or n_mps:
        # Clear cached sam3 modules so re-import picks up patched source
        for mod in list(sys.modules):
            if mod == "sam3" or mod.startswith("sam3."):
                del sys.modules[mod]
    import sam3  # noqa: F401  forces module load with stub in place

    patch_edt()
    patch_fused_ops()
