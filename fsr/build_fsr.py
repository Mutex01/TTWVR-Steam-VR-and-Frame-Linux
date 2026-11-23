#!/usr/bin/env python3
"""Builds the FSR pieces for TTWVR 1.1.7 (SteamVR / Steam Frame on Linux).

Only reads your original TTWVR.dll and only writes into fsr/out/ (and fsr/reference/).
It changes nothing in the game.

It downloads the reference project ethanfel/ttwvr-linux (GPL-3.0) at the tested commit and uses
its unmodified DLL patcher and DXVK build function.

Usage:  python3 fsr/build_fsr.py [path to your original TTWVR.dll]
"""
import hashlib, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF_URL = 'https://github.com/ethanfel/ttwvr-linux.git'
REF_COMMIT = '52a6cfce4c3a07e3873e052798b0b65a395595d0'
REF = HERE / 'reference' / 'ttwvr-linux'

# Path to the ORIGINAL TTWVR.dll 1.1.7 (inside your TTWVR mod folder).
# First argument, otherwise the Amethyst default path.
ORIGINAL = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else \
    Path.home() / 'Games/Amethyst/Fallout New Vegas/mods/TTWVR/NVSE/Plugins/TTWVR.dll'
ORIGINAL_SHA = '119a085a5b0101f0618b8e076a421b4b89e30d72d9b6eae874f4e5af7bd3fb27'
PATCHED_SHA  = 'ae7dc0d7ba94651af0ccd729122f623d3dbdf0b85c6c787838c04bbc721135d6'
OUT = HERE / 'out'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(['git', '-C', str(REF), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def fetch_reference():
    """Download the reference project at the pinned commit (once) and verify it is unmodified."""
    try:
        if not (REF / '.git').exists():
            print(f'Downloading reference project {REF_URL} @ {REF_COMMIT[:7]} ...')
            REF.mkdir(parents=True, exist_ok=True)
            git('init', '-q')
            git('fetch', '-q', '--depth', '1', REF_URL, REF_COMMIT)
            git('checkout', '-q', 'FETCH_HEAD')
        head, dirty = git('rev-parse', 'HEAD'), git('status', '--porcelain')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f'Could not download the reference project ({e}). '
                 f'Check git and your internet connection, delete {REF} and try again.')
    if head != REF_COMMIT or dirty:
        sys.exit(f'{REF} is not the unmodified commit {REF_COMMIT[:7]}. Delete it and try again.')


def main():
    if not ORIGINAL.is_file():
        sys.exit(f'Original TTWVR.dll not found: {ORIGINAL}\n'
                 'Pass the path as the first argument.')
    fetch_reference()
    sys.path.insert(0, str(REF / 'tools'))
    import setup_linux                              # reference tool, unmodified
    from experimental_author_dlss import build      # reference patcher, unmodified

    # 1. Patched TTWVR.dll, laid out as its own mod folder
    plugin = OUT / 'TTWVR 1.1.7 Linux FSR-Patch/NVSE/Plugins/TTWVR.dll'
    if not plugin.exists():
        if sha(ORIGINAL) != ORIGINAL_SHA:
            sys.exit('Your TTWVR.dll has an unknown checksum (not the original 1.1.7) - stopping.')
        patched = bytes(build(ORIGINAL.read_bytes(), native_fsr=True))
        if hashlib.sha256(patched).hexdigest() != PATCHED_SHA:
            sys.exit('The patched DLL does not have the expected checksum - stopping.')
        plugin.parent.mkdir(parents=True)
        plugin.write_bytes(patched)

    # 2. + 3. Build DXVK and download d3dcompiler_47 (reference function, with its own checks)
    setup_linux.prepare({'fixes': OUT})
    deps = OUT / 'dependencies'

    # The patched d3d11.dll belongs in the mod too (TTWVR.dll looks for it in the plugin folder)
    d3d11_mod = plugin.parent / 'd3d11.dll'
    if not d3d11_mod.exists():
        d3d11_mod.write_bytes((deps / 'dxvk' / 'd3d11.dll').read_bytes())

    print('\n=== Checksums (SHA-256) ===')
    print('TTWVR.dll         ', sha(plugin), '(expected', PATCHED_SHA[:12] + '...)')
    print('d3dcompiler_47 32 ', sha(deps / 'compiler32.dll'))
    for name, known in setup_linux.KNOWN_RENDERER.items():
        h = sha(deps / 'dxvk' / name)
        print(f'{name:18}', h, 'same as author build' if h == known else
              'DIFFERENT from author build (normal: depends on your compiler)')
    print(f'\nDone. Results are in {OUT}')


if __name__ == '__main__':
    main()
