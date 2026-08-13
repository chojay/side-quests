"""
Monkey-patches for known bugs in pysrim v0.5.10.

IMPORTANT: Call apply_patches() BEFORE importing anything from srim.
The yaml.load bug triggers at module-level during class definition,
so yaml.load must be patched before `import srim` ever happens.

Bug 1: elementdb.py uses yaml.load() without Loader argument,
        causing a TypeError on PyYAML 6+.

Bug 2: srim.py TRIM.__init__ reads kwargs.get('ranges', 0) where it
        should read kwargs.get('sputtered', 0).
"""
import logging

logger = logging.getLogger(__name__)

_patches_applied = False


def apply_patches():
    """
    Apply all pysrim patches. MUST be called before `import srim`.

    Safe to call multiple times  -  only applies patches once.
    """
    global _patches_applied
    if _patches_applied:
        return
    _patch_yaml_load()
    _patches_applied = True
    logger.info("pysrim v0.5.10 patches applied successfully")


def _patch_yaml_load():
    """
    Patch yaml.load to auto-add Loader=SafeLoader when called without it.

    This must happen BEFORE `import srim` because elementdb.py calls
    yaml.load() at class definition time (line 10 of elementdb.py:
    `_db = create_elementdb()` which calls `yaml.load(open(...))`).
    """
    import yaml

    _original_load = yaml.load

    def _safe_load_wrapper(*args, **kwargs):
        if 'Loader' not in kwargs and len(args) < 2:
            kwargs['Loader'] = yaml.SafeLoader
        return _original_load(*args, **kwargs)

    yaml.load = _safe_load_wrapper
    logger.debug("Patched yaml.load to default to SafeLoader")


def patch_sputtered_kwarg():
    """
    Fix TRIM.__init__ reading wrong kwarg for sputtered output.

    Call AFTER `import srim` (this patches an already-imported class).
    """
    try:
        import srim.srim as srim_module
        import inspect

        source = inspect.getsource(srim_module.TRIM.__init__)
        if "kwargs.get('ranges', 0)" in source:
            original_init = srim_module.TRIM.__init__

            def patched_trim_init(self, target, ion, **kwargs):
                if 'sputtered' in kwargs and 'ranges' not in kwargs:
                    kwargs['ranges'] = kwargs.get('ranges', 0)
                original_init(self, target, ion, **kwargs)
                if 'sputtered' in kwargs:
                    self._sputtered = kwargs['sputtered']

            srim_module.TRIM.__init__ = patched_trim_init
            logger.debug("Patched TRIM sputtered kwarg bug")
    except Exception as e:
        logger.warning(f"Could not patch sputtered kwarg: {e}")


def verify_installation():
    """Quick check that pysrim is importable and functional."""
    try:
        # Ensure patches are applied first
        apply_patches()

        from srim import Ion, Layer, Target, TRIM
        from srim.output import Range, Ioniz, Vacancy

        ion = Ion('N', energy=100e3)
        layer = Layer(
            {'Si': {'stoich': 1.0, 'E_d': 15, 'lattice': 2, 'surface': 4.70},
             'O':  {'stoich': 2.0, 'E_d': 28, 'lattice': 3, 'surface': 2.00}},
            density=2.20, width=50000
        )
        target = Target([layer])

        # Also patch the sputtered kwarg now that srim is imported
        patch_sputtered_kwarg()

        logger.info("pysrim installation verified: Ion, Layer, Target all functional")
        return True
    except Exception as e:
        logger.error(f"pysrim installation check failed: {e}")
        return False
