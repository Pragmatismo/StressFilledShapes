# Goblin Grange Terrain Set Generator

This folder contains a standalone Python/Pygame tool for authoring terrain packages at:

- `content/locations/<package_id>/location.json`
- `content/locations/<package_id>/assets/*.png`

## Run

```bash
cd asset_creation/TerrainSetTool
python3 terrain_set_tool.py
```

## Current implementation highlights

- Resizable two-panel editor layout with 4 tabs: Location, Terrain, Generate, Validate.
- Package creation/loading through `content/locations`.
- `location.json` read/write with top-level terrain/feature schemas.
- Deterministic seeded terrain generation with per-terrain runtime biases.
- Clear-edge generation for entry side.
- Feature placement with terrain filtering, spacing, footprint checks, and density gradient.
- Template generation that **never overwrites existing files**:
  - static terrain tile (512x256)
  - animated terrain strips (`frame_count * 512 x 256`)
  - autotile sheet (2048x1024)
  - feature isometric box templates based on tile width/height/depth
  - destroyed feature templates for destructible features
- Import image workflow (using tkinter file picker when available).
- Validation tab with errors and warnings.

## Keyboard shortcuts

- `Enter` (Location tab): create package from typed package id
- `C`: create package
- `S`: save `location.json`
- `T`: add terrain layer
- `F`: add feature rule
- `A`: create missing template assets
- `I`: import image for first terrain layer
- `G`: generate map
- `R`: randomize seed + generate
- `V`: run validation
- `3/4/5`: toggle preview overlays (grid/features/anchors)

## Notes

This is intentionally self-contained and does not depend on other repository code.
