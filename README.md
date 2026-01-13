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

# Smoothing Principle

To eliminate visible facets, the macro adjusts the Deviation and Angular properties before exporting the .3mf file.




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


## Technical Notes

    • The macro modifies ViewObject.Deviation and ViewObject.Angle before export 
    
    • .3mf files are used instead of .stl to retain print metadata 
    
    • Compatible with most slicers that support .3mf: Cura, PrusaSlicer, OrcaSlicer, Bambu Studio, etc. 


## Files and Parameters

    • Geometry is extracted from the active FreeCAD document 
    
    • Print settings are stored inside the .3mf file in the same directiry as the project FreeCAD
    
    • The macro can be configured to run other commands, such as turning on the printer using a connected smart plug.


## Installation

    1. Copy the macro to your FreeCAD macros folder 
    
    3. Run the macro from FreeCAD.  The slicer path is set directly in the macro’s main dialog, using the dedicated input field.
    
    4. On first launch, enter your print settings in the slicer and save the .3mf file (generally, except in Cura, this is just Ctrl+S or “Save” in the menu).
    
    5. On next launches, enjoy automatic reuse of your settings 


## Why 3MF?

Unlike .stl, the .3mf format supports:

    • Embedded print settings 
    
    • Multiple objects 
    
    • Metadata and units 
    
    • Better geometry fidelity 
