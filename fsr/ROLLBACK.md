# Undo the FSR setup

Close the game and SteamVR first.

## 1. Remove the DLLs from the game folder

These three files were added to the game folder (next to `FalloutNV.exe`). `rm -i` asks before
each file:

```bash
G=~/.local/share/Steam/steamapps/common/Fallout\ New\ Vegas
rm -i "$G/d3d9.dll" "$G/dxgi.dll" "$G/d3dcompiler_47.dll"
```

To make sure they are the files you installed, compare their checksums (`sha256sum`) with the
ones `build_fsr.py` printed:
- `d3dcompiler_47.dll` is always `2ad0d4987fc4624566b190e747c9d95038443956ed816abfd1e2d389b5ec0851`.
- `d3d9.dll` and `dxgi.dll` are built on your machine, so their checksums depend on your compiler.

## 2. Disable the patch mod

In your mod manager, disable the mod "TTWVR 1.1.7 Linux FSR-Patch" and deploy again.
- **What the mod contains:**
  - `NVSE/Plugins/TTWVR.dll`: patched,
    `ae7dc0d7ba94651af0ccd729122f623d3dbdf0b85c6c787838c04bbc721135d6`
  - `NVSE/Plugins/d3d11.dll`: patched DXVK
- **Your original:** the original `TTWVR.dll`
  (`119a085a5b0101f0618b8e076a421b4b89e30d72d9b6eae874f4e5af7bd3fb27`) in your TTWVR mod is
  never changed.

## 3. Reset the Steam launch options

In Steam → Fallout: New Vegas → Properties → Launch options, enter only:

```
PROTON_USE_WOW64=1 PROTON_ENABLE_NVAPI=1 PROTON_HIDE_NVIDIA_GPU=0 DXVK_CONFIG="d3d11.disableDirectImageMapping = True"
```

## Build files

The folders `fsr/out/` and `fsr/reference/` only contain build results and the downloaded
reference project. You can delete both, and `fsr/build_fsr.py` rebuilds everything.
