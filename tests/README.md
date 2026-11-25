# Tests of the 3D Printer 3mf Workflow macro

These test benches run the macro without its windows (the dialogs are replaced
by fixed answers), with `freecadcmd`, on real 3MF projects saved by the slicers.
They are not needed to use the macro: the Addon Manager only installs the macro
files.

## Running

```bash
python tests/run_all.py            # all the tests
python tests/run_all.py copies     # only the tests whose name contains "copies"
```

`run_all.py` looks for `freecadcmd` in the usual places; set the `FREECADCMD`
environment variable to use another FreeCAD. Results and logs go to `tests/out/`
(ignored by git). Each test can also be run alone: `freecadcmd tests/test_copies_qidi.py`.

`test_slicers_cli.py` also has the results re-read by the slicers installed on the
computer (QIDIStudio, Bambu Studio, OrcaSlicer, in command line).
`test_copies_prusa.py` uses PrusaSlicer in command line.

## Tests

| Test | What it checks |
|------|----------------|
| `test_unchanged.py` | Objects not modified in FreeCAD are left untouched (settings applied to faces kept); only modified objects are replaced and listed in the warning (QIDIStudio and QIDISlicer projects) |
| `test_copies_qidi.py` | Copies made in QIDIStudio (duplicated objects sharing one mesh): kept, removed, unchanged object; re-read by Bambu Studio |
| `test_copies_prusa.py` | Copies made in PrusaSlicer / QIDISlicer (instances pointing to the original mesh): kept, removed, unchanged object; re-read by PrusaSlicer |
| `test_slicers_cli.py` | Multi-object scenarios (add, remove, rename, App::Part, shared meshes) re-read by the slicers in command line |
| `test_heavy_flow.py` | Warning before a very long meshing, "Back to options", texts in three languages |
| `test_estimate.py` | Estimated triangles and time compared with measured values (`fixtures/mesh_scaling_ref.txt`) |
| `test_optimize.py` | Options window (offscreen): live export time, "Optimize fineness", floors, target time saved, time calibration |
| `test_thumbs.py` | Thumbnails of the 3MF files in the base list |
| `test_preview.py` | Preview of the selected objects (images in `tests/out/`) |
| `test_colors.py` | Colors of the preview (appearance per object or per face, PartDesign Body) |
| `test_base3mf_labels.py`, `test_base3mf_match.py`, `test_base3mf_info.py` | Base 3MF list: labels of bases from other folders, default base by object name, explanation text |

## Fixtures

The tests use 3MF projects saved by the slicers' interface, placed in
`tests/fixtures/`. They are personal parts, so they are **not** in the repository
(ignored by git): put your own projects there under these names to run the tests.

| File | Content |
|------|---------|
| `qidistudio.3mf` | QIDIStudio project, one object |
| `qidistudio9obj.3mf` | QIDIStudio project, 9 objects |
| `qidistudio_copies.3mf` | QIDIStudio project, one object duplicated twice (3 objects with the same name sharing one mesh) |
| `bambu.3mf` | Bambu Studio project, one object |
| `qidislicer.3mf` | QIDISlicer project, one object |
| `prusa_copies.3mf` | the same with 3 instances (`prusa-slicer-console --duplicate 3 --export-3mf`) |
| `superslicer.3mf`, `cura.3mf` | SuperSlicer and Cura projects |
| `freecad.3mf` | 3MF exported by FreeCAD (no slicer settings) |
| `unknown.3mf` | 3MF from another program |

`mesh_scaling_ref.txt` (triangles and times measured on simple shapes) is in the
repository.
