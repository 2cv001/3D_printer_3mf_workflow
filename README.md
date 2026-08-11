# 3D_printer_3mf_workflow

FreeCAD macro exporting smooth 3MF files and preserving all slicer print settings, with automatic workflow to your preferred slicer.


## Purpose

This macro automates and enhances the 3D printing workflow from FreeCAD to your slicer by:

    • Generating smooth 3D prints without visible facets
    
    • Preserving print settings (temperature, supports, speed…) directly within the FreeCAD project
    
    • Launching external programs to streamline the full pipeline: FreeCAD → Slicer → Print 

# Evolution

This macro is the successor to macro 3d_printer_workflow.

While the previous version enabled smooth exports and program launching, it relied on .stl files, which cannot store print settings.

This macro uses .3mf files, allowing full geometry + print configuration to be preserved and reused.

To retain the core functionality of the previous macro, this version also provides an STL export option with adjustable tessellation parameters, 
allowing smooth mesh generation just like before.

# Limitation
The current version can export only a single object, but you can work around this by using links — for example, a Simple Group — to combine multiple objects into one.

# Smoothing Principle

The macro exports the selected objects to a 3MF file using the specified tessellation parameters (LinearDeflection and AngularDeflection). 
It generates temporary mesh objects for the export process and automatically removes them afterward.



<img width="550" height="363" alt="image" src="https://github.com/user-attachments/assets/8d597779-a934-4ad4-9c66-3bbc3c463bba" />

With visible facets

<img width="516" height="438" alt="image" src="https://github.com/user-attachments/assets/0b987465-efbb-4c25-a88b-99053f413377" />

Without visible facets



## Workflow Overview

<img width="1146" height="926" alt="image" src="https://github.com/user-attachments/assets/027e2229-5d79-4ba0-afb9-e2ffd685db95" />


### First Launch

    • FreeCAD exports a .3mf file containing only the object geometry
    
    • The slicer opens the file 
    • The user enters print settings (e.g. 200 °C, PLA, 50 mm/s) 
    
    • The slicer saves the .3mf file with embedded print settings 

    
### Subsequent Launches

    • FreeCAD reads the .3mf file and retrieves the saved print settings
    
    • It generates a new .3mf file with both geometry and configuration 
    
    • The slicer opens the file with all settings preloaded 
    
    • ✅ No need to re-enter anything — changes are preserved 


## Technical Notes / slicer compatibility

    • .3mf files are used instead of .stl to retain print metadata 
    

    • Geometry is extracted from the active FreeCAD document 
    
    • Print settings are stored inside the .3mf file in the same directory as the project FreeCAD
    
    • The macro can be configured to run other commands, such as turning on the printer using a connected smart plug.

    • Compatible with most slicers that support .3mf: 
        tested with QidiSlicer, QidiStudio, Cura, PrusaSlicer, OrcaSlicer, Bambu Studio, Anycubic, Creality. 
    • Not compatible with slicers that do not produce 3MF files containing print settings (e.g., ideaMaker, FlashPrint).
    


### Tested Compatible Slicers

| Slicer           | Family       | 3MF Format             | Includes Print Settings | Status      |
|------------------|--------------|------------------------|-------------------------|-------------|
| QIDISlicer       | qidislicer   | Slic3r_PE.config       | ✔ Yes                   | Compatible  |
| SuperSlicer      | qidislicer   | Slic3r_PE.config       | ✔ Yes                   | Compatible  |
| Cura             | qidislicer   | Slic3r_PE.config       | ✔ Yes                   | Compatible  |
| OrcaSlicer       | qidistudio   | Metadata/*.xml         | ✔ Yes                   | Compatible  |
| QIDIStudio       | qidistudio   | Metadata/*.xml         | ✔ Yes                   | Compatible  |
| Anycubic         | qidistudio   | Metadata/*.xml         | ✔ Yes                   | Compatible  |
| Creality Print   | qidistudio   | Metadata/*.xml         | ✔ Yes                   | Compatible  |

### Tested Incompatible Slicers (because they do not store print settings in 3MF)

| Slicer        | Family       | 3MF Format     | Includes Print Settings  | Status        |
|---------------|--------------|----------------|--------------------------|---------------|
| FlashPrint 5  | qidislicer   | Minimal 3MF    | ❌ No                    | Incompatible  |
| IdeaMaker     | qidislicer   | Minimal 3MF    | ❌ No                    | Incompatible  |
| Raise3D       | qidislicer   | Minimal 3MF    | ❌ No                    | Incompatible  |
    
For other slicers, feel free to try — it should work. Otherwise, please open an issue on GitHub.

## Installation and use
The best way to install the macro is to use the addon manager in Freecad. Then:

       
- Run the macro from FreeCAD.  The slicer path is set directly in the macro’s main dialog, using the dedicated input field.

  - (Linux only) When the Slicer is installed via flatpak, enter flatpak run <slicerID> e.g. flatpak run com.prusa3d.PrusaSlicer
    
- On first launch, enter your print settings in the slicer and save the .3mf file (generally, except in Cura, this is just Ctrl+S or “Save” in the menu).
    
- On next launches, enjoy automatic reuse of your settings 



<img width="1603" height="863" alt="image" src="https://github.com/user-attachments/assets/3e4fe3e8-5ca2-4088-8b3f-57fdbaa668fb" />



## Why 3MF?

Unlike .stl, the .3mf format supports:

    • Embedded print settings 
    
    • Metadata and units 
    
    • Better geometry fidelity 


## User Commands : macro 3D_Printer_3mf_Workflow_ConfigIni.FCMacro
The macro allows you to define custom commands that will be executed automatically after the 3MF file is generated.
This feature is optional and can be used to automate additional steps in your workflow, such as:

 • copying the generated 3MF file to another location
 
 • turning on your 3D printer through a smart plug
 
 • turn a light on
 
 • pre‑heating the build plate
 
 • sending an HTTP request to your home automation system
 
 • launching a script or external tool

### How to configure user commands

A dedicated helper macro is provided to make configuration easy. Your commands are stored in an .ini file used by the workflow.

The ⚙️ button in the options window allows you to both install and open the configuration macro (3D_Printer_3mf_Workflow_ConfigIni.FCMacro).
<img width="781" height="392" alt="Capture d&#39;écran 2026-08-02 090716" src="https://github.com/user-attachments/assets/a64e6207-99c8-46d0-9867-a40d6bd87e70" />


 • Fill in the fields in the configuration window
 
 • Hover your mouse over a column title to display help tooltips
 
 • Each command you define will be executed in order after the 3MF file is produced.
 <img width="897" height="528" alt="Capture d&#39;écran 2026-08-02 085921" src="https://github.com/user-attachments/assets/6b2dad76-2de4-47f7-9472-bd245a9b6b63" />

 
## Using %PROJECT%, %PROJECTDIR%, and %PROJECTNAME% in user commands
When you define custom post‑processing commands in the workflow, you can use three special placeholders.
These placeholders are automatically replaced by values derived from your FreeCAD project file.

### Available placeholders
Placeholder	Meaning
%PROJECT%	Full path of the FreeCAD project without extension
%PROJECTDIR%	Folder containing the FreeCAD project
%PROJECTNAME%	Project file name without extension
## Examples
Copy the generated 3MF file next to the project :

```bash
copy "%PROJECT%.3mf" "%PROJECTDIR%/backup/%PROJECTNAME%.3mf"
```

Run a script stored in the project folder :

```bash
python "%PROJECTDIR%/scripts/postprocess.py" "%PROJECT%.3mf"
```

Send an HTTP request using the project name :

```bash
curl "http://myserver/api/start?job=%PROJECTNAME%"
```
Turn on a Shelly smart plug Gen 1

```bash
curl "http://192.168.xxx.xxx/relay/0?turn=on"
```

Gen2 
```bash
http://192.168.xxx.xxx/rpc/Switch.Set?id=0&on=true
```

Or if your device have a password :
```bash
curl -u admin:yourpassword "http://192.168.xxx.xx/rpc/Switch.Set?id=0&on=true"
```


