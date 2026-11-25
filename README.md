# 3D_printer_3mf_workflow

FreeCAD macro exporting smooth 3MF files and preserving all slicer print settings, with automatic workflow to your preferred slicer.

Documentation on the FreeCAD wiki: [Macro 3D Printer 3mf Workflow](https://wiki.freecad.org/Macro_3D_Printer_3mf_Workflow)

## Purpose

This macro automates and enhances the 3D printing workflow from FreeCAD to your slicer by:

- Generating smooth 3D prints without visible facets.
- **Preserving print settings (temperature, supports, speed…)** in a way that keeps them linked to the FreeCAD project.
- Launching external programs to streamline the full pipeline: FreeCAD → Slicer → Print.

## At a glance

- **Smooth prints**: curved surfaces come out without visible facets.
- **Your slicer settings are kept**: set them once in the slicer (temperature, supports, infill…); every new export from FreeCAD keeps them.
- **From FreeCAD to the slicer in one click**: the macro exports the 3MF and opens it in your slicer.
- **Several objects at once**, each one with its own settings.
- **You see what you export**: a preview of the selected objects and the estimated export time.
- **Works with most slicers**: QIDISlicer, QIDIStudio, PrusaSlicer, OrcaSlicer, Bambu Studio, Cura, Creality Print, Anycubic.

## Principle of smoothing

<img width="550" height="363" alt="With visible facets" src="https://github.com/user-attachments/assets/8d597779-a934-4ad4-9c66-3bbc3c463bba" />

With visible facets

<img width="516" height="438" alt="Without visible facets" src="https://github.com/user-attachments/assets/0b987465-efbb-4c25-a88b-99053f413377" />

Without visible facets

The macro exports the selected objects to a 3MF file using the specified tessellation parameters (LinearDeflection and AngularDeflection). The meshes are computed in memory, still controlled by these two parameters: nothing is added to the FreeCAD document.

## Workflow Overview

<img width="1086" height="907" alt="image" src="https://github.com/user-attachments/assets/a4bb7d4c-5e6d-402e-b2bb-730c757a543a" />



### First Launch

- FreeCAD exports a .3mf file containing only the object geometry.
- The slicer opens the file.
- The user enters print settings (e.g. 200 °C, PLA, 50 mm/s).
- The slicer saves the .3mf file with embedded print settings.

### Subsequent Launches

- FreeCAD reads the .3mf file and retrieves the saved print settings.
- It generates a new .3mf file with both geometry and configuration: only the geometry of the objects is replaced, everything else in the file is kept as is.
- The slicer opens the file with all settings preloaded.
- ✅ No need to re-enter anything — changes are preserved.

## Use

Install the macro with the **Addon Manager** of FreeCAD, then select the objects to print in the tree.

Run the macro from FreeCAD. The slicer path is set directly in the macro's main dialog, using the dedicated input field.

- (Linux only) When the slicer is installed via flatpak, enter `flatpak run <slicerID>`, e.g. `flatpak run com.prusa3d.PrusaSlicer`.

On first launch, enter your print settings in the slicer and save the .3mf file (generally, except in Cura, this is just Ctrl+S or "Save" in the menu).

On next launches, enjoy automatic reuse of your settings.
<img width="1811" height="814" alt="image" src="https://github.com/user-attachments/assets/abeb4cee-a33a-45f1-9a06-cba8176c124f" />



## Launching other programs or commands

The macro allows you to define custom commands that will be executed automatically after the 3MF file is generated. This feature is optional and can be used to automate additional steps in your workflow, such as:

- copying the generated 3MF file to another location
- turning on your 3D printer through a smart plug
- turning a light on
- pre‑heating the build plate
- sending an HTTP request to your home automation system
- launching a script or external tool

### Setup (optional: to add additional commands)

A dedicated helper macro is provided to make configuration easy. Your commands are stored in an .ini file used by the workflow.

The ⚙️ button in the options window allows you to both install and open the configuration macro (3D_Printer_3mf_Workflow_ConfigIni.FCMacro).

<img width="1134" height="805" alt="image" src="https://github.com/user-attachments/assets/86b85935-095a-40db-98c6-453d60be281e" />



- Fill in the fields in the configuration window.
- Hover your mouse over a column title to display help tooltips.
- Each command you define will be executed in order after the 3MF file is produced.

<img width="897" height="528" alt="Configuration window" src="https://github.com/user-attachments/assets/6b2dad76-2de4-47f7-9472-bd245a9b6b63" />

### Using project and export placeholders in user commands

Custom post-processing commands can refer to both the FreeCAD project and the export (named after the selected objects). Commands that process the generated 3MF should use `%EXPORT%.3mf`.

| Placeholder | Meaning |
|-------------|---------|
| `%PROJECT%` | Full path of the FreeCAD project without extension |
| `%PROJECTDIR%` | Folder containing the FreeCAD project |
| `%PROJECTNAME%` | Project file name without extension |
| `%EXPORT%` | Full path of the export (named after the selected objects) without extension |
| `%EXPORTNAME%` | Export file name without extension |

### Examples

Copy the generated 3MF file next to the project:

```bash
copy "%EXPORT%.3mf" "%PROJECTDIR%/backup/%EXPORTNAME%.3mf"
```

Run a script stored in the project folder:

```bash
python "%PROJECTDIR%/scripts/postprocess.py" "%EXPORT%.3mf"
```

Send an HTTP request using the project name:

```bash
curl "http://myserver/api/start?job=%PROJECTNAME%"
```

Turn on a Shelly smart plug Gen 1:

```bash
curl "http://192.168.xxx.xxx/relay/0?turn=on"
```

Gen 2:

```bash
http://192.168.xxx.xxx/rpc/Switch.Set?id=0&on=true
```

Or if your device has a password:

```bash
curl -u admin:yourpassword "http://192.168.xxx.xx/rpc/Switch.Set?id=0&on=true"
```

## Going further

### Exporting several objects

Select one or more objects (Ctrl+click in the tree) and run the macro. All the selected objects go into a single 3MF, each one as a separate object in the slicer, with its own print settings.

The top right corner of the options window shows a small isometric image of the selected objects, with their colors (for a PartDesign Body, the color of its visible feature), so you can check what will be exported. It is drawn by the macro from a very coarse mesh, without OpenGL, in a few hundredths of a second; the document and the 3D view are not touched.

- **First export**: the objects keep exactly their FreeCAD layout (X, Y and Z). The group is centered on the plate and the lowest object rests on it. If objects overlap, QIDISlicer / PrusaSlicer ask whether to load them as a single object having multiple parts: answer **Yes** to keep them assembled, **No** to get separate objects (then arrange them on the plate).
- **Next exports**: each FreeCAD object is matched with the slicer object of the same name. Its geometry is replaced; its settings and its position and rotation on the plate are kept, and it is put back on the plate.
- Objects that are no longer selected are removed from the 3MF; newly selected objects are added at their FreeCAD position.
- Copies made on the plate in the slicer (duplicated objects or added instances) are kept as long as the object has not changed in FreeCAD. When it has changed, the macro asks: **Keep the copies** (each one gets the new geometry and keeps its place; if the part got bigger they may overlap, use "Arrange" in the slicer) or **Remove the copies**. With **Do not recover slicer position/rotation** checked, the copies are removed.
- With a single selected object and a 3MF whose object has another name, the first object on the plate is replaced and renamed after the FreeCAD object, so 3MF files made by previous versions keep working.
- With the STL option, all the selected objects go into one STL file.
- Objects inside an App::Part are exported at their global position.

#### Choosing the base 3MF

The **3MF file for print parameters** list chooses the 3MF whose print settings and objects are reused:

- **No base (new 3MF)**: a new 3MF containing only the geometry. If the 3MF of the selection already exists, it is kept as a `.old` backup.
- **This selection's 3MF**: the usual choice, selected by default when it exists. When it does not exist yet, the most recent 3MF of the project folder that contains an object with the same name is selected instead (for example the 3MF of several objects, when you export one of them alone), so its settings are not lost.
- The other 3MF files of the project folder, most recent first.
- The last 8 bases used in other folders (remembered from one session to the next), shown with their folder and date, so that several "Body.3mf" from different projects can be told apart. Hover over a line to see its full path.
- **Browse…** picks a 3MF anywhere, for example in another project.

Each 3MF of the list shows its thumbnail: the preview image saved in the file by the slicer (plate image for QIDIStudio / Bambu / Orca, thumbnail for Cura / SuperSlicer / FreeCAD). It is only read from the file, so it costs nothing; a 3MF without a preview image simply has no thumbnail.

Below the list, the macro shows the name the 3MF will be saved as and explains what the chosen base will do: for which objects the existing settings are kept, which objects are new (they get the general settings), and whether the base has no slicer settings at all. The text turns orange when object settings may not be reused (no object of the base has a selected name, or "No base" while the 3MF of the selection exists). The base file itself is never modified; if the 3MF of the selection already exists and another base is chosen, it is backed up first (`.old` file).

From the base, the macro always keeps the **general settings**: printer, filament (type, temperatures, cooling… and all the filaments of a multi-color printer) and print profile (layer height, speeds, walls, default infill and supports…). The **settings of an object** (its own infill, walls, layer height, supports, filament, modifiers…) are kept only for the objects matched by name. Objects of the base that match no selected object are removed; new objects get the general settings and the first filament.

#### Settings applied to faces and modifiers

Some print settings are attached to specific faces of an object: enforced or blocked supports, seams, colors (and other per-face data). They, as well as modifiers and extra parts, are tied to the old geometry and cannot be kept when it changes. If some would be lost, the macro tells you which objects are concerned and asks you to **Continue** or **Cancel** (the 3MF is then left unchanged).

Objects whose geometry has not changed in FreeCAD since the last export are left exactly as they are in the slicer: their settings applied to faces, modifiers, copies and position are all kept, and the warning only lists the objects that really changed. For example, with `Housing_Lid.3mf`, modifying only the Housing keeps the enforced supports of the Lid. (Changing the precision or the angular tolerance changes the mesh, so all objects are then replaced. With **Do not recover slicer position/rotation** checked, all objects are replaced and placed as in FreeCAD.)

### Mesh fineness and export time

Very small values make the mesh huge, and FreeCAD is frozen while it is computed. Before meshing, the macro quickly estimates the number of triangles and the time needed (from a few coarse test meshes, in less than a second). If the mesh would take more than about 30 seconds or have more than a million triangles, it asks first: **Continue** or **Back to options** to choose coarser values.

The **Mesh fineness** panel of the options window holds the **Precision** (LinearDeflection, in mm) and the **Angular tolerance** (AngularDeflection, in degrees); their tooltips explain them. On the right, **Export time** shows the estimated time for the selected objects, with the number of triangles and the 3MF size below. It is computed when the window opens and updated live while you change the values; it turns orange above the warning limits.

**Optimize fineness** chooses the finest precision and angular tolerance whose estimated export fits in the **Target export time** (remembered between sessions), keeping the ratio between the two values. It never goes below 0.01 mm and 2°: below that, the printed part does not change (0.4 mm nozzle, 0.1 to 0.2 mm layers), only the file and the time grow. You can still type finer values yourself.

The time estimate adjusts itself to your computer: after each export, the real meshing time is compared with the estimate and a correction factor is kept in the .ini file.

### Export filenames

The 3MF is named after the selected objects' visible names (their **Label** in the FreeCAD tree), sorted alphabetically and joined with `_`, in the same directory as the saved FreeCAD document. For example, selecting `Housing` creates `Housing.3mf` and, if enabled, `Housing.stl`; selecting `Lid` and `Housing` (in any order) creates `Housing_Lid.3mf`. Very long names are shortened and get a unique suffix. Each set of objects has its own 3MF print settings and backups.

For a PartDesign Body, selecting a face or edge in the 3D view, or a feature such as a Pad or Pocket in the tree, exports the whole Body using the **Body's Label**. Selecting several features of the same Body still counts as one object. Objects outside a Body retain their own labels and geometry.

Filename-incompatible characters are replaced with underscores. Names that collide within the document (including after sanitizing or ignoring letter case) receive the object's internal name as a suffix. Workflow backup/temporary suffixes and Windows device names are also adjusted to avoid conflicts. Use distinct, stable labels: renaming an object changes its export filename. Objects from different documents in the same folder should also have distinct labels.

Existing exports named after the project are not renamed automatically. To reuse their print settings, choose the old `.3mf` in the **3MF file for print parameters** list (or with **Browse…**) on the first export of a part. Save subsequent slicer changes in that part's new `.3mf` file.

Each selected object becomes one object in the slicer; the macro does not split individual contours of a sketch or solids inside a single selected object (use "Split to objects" in the slicer if needed).

### Slicer path

The slicer path must be the slicer program itself (on Windows, its .exe file): a part file such as a .3mf or .stl is refused. On Windows, the **Browse…** button of the slicer line only lists programs, so that it is not confused with the **Browse…** button of the base 3MF.

## Technical Notes / slicer compatibility

- Geometry is extracted from the active FreeCAD document.
- .3mf files are used instead of .stl to retain print metadata.
- Print settings are stored inside the .3mf file in the same directory as the FreeCAD document.
- Compatible with most slicers that support .3mf (see the tables below).
- Not compatible with slicers that do not produce 3MF files containing print settings. For other slicers, feel free to try — it should work. Otherwise, please open an issue on GitHub.
- The macro can be configured to run other commands, such as turning on the printer using a connected smart plug.

### Tested Compatible Slicers

| Slicer           | Family in macro | Includes Print Settings in 3mf | Status     |
|------------------|-----------------|--------------------------------|------------|
| QIDISlicer       | qidislicer      | ✔ Yes                          | Compatible |
| SuperSlicer      | qidislicer      | ✔ Yes                          | Compatible |
| Cura             | qidislicer      | ✔ Yes                          | Compatible |
| OrcaSlicer       | qidistudio      | ✔ Yes                          | Compatible |
| QIDIStudio       | qidistudio      | ✔ Yes                          | Compatible |
| Anycubic         | qidistudio      | ✔ Yes                          | Compatible |
| Creality Print   | qidistudio      | ✔ Yes                          | Compatible |
| Bambu Studio     | qidistudio      | ✔ Yes                          | Compatible |

### Tested Incompatible Slicers (they do not store print settings in 3MF)

| Slicer        | Includes Print Settings in 3mf | Status       |
|---------------|--------------------------------|--------------|
| FlashPrint 5  | ❌ No                          | Incompatible |
| IdeaMaker     | ❌ No                          | Incompatible |
| Raise3D       | ❌ No                          | Incompatible |

## History

This macro is the successor to the [3d_printer_workflow](https://wiki.freecad.org/Macro_3D_Printer_Workflow) macro.

The 3D_Printer_Workflow macro was already capable of producing smooth, facet‑free exports. Its main limitation was that it relied on STL files, which cannot store slicer or printing parameters.

This macro uses .3mf files, allowing all print settings to be saved and reused. Unlike .stl, the .3mf format supports embedded print settings, metadata and units, and better geometry fidelity.

To retain the core functionality of the previous macro, this version also provides an STL export option with adjustable tessellation parameters, allowing smooth mesh generation just like before.

## Discussion

- English: https://forum.freecad.org/viewtopic.php?t=102503
- French: https://forum.freecad.org/viewtopic.php?t=103419
