# ScreenClippingToolMaster
A screen clipping tool that makes clipping the screen easy

# Features
Global Hotkeys:
-- Use windows-key + Z to create a clip (can be changed in the settings)  
-- Use windows-key + C to create a gif (can be changed in the settings)  

Tesseract:  
-- Has the ability to use the OCR engine linked below, just add the engine in a folder called "tess_folder" in the same directory as the file  
[![GitHub license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://raw.githubusercontent.com/tesseract-ocr/tesseract/master/LICENSE)  
[![Downloads](https://img.shields.io/badge/download-all%20releases-brightgreen.svg)](https://github.com/tesseract-ocr/tesseract/releases/)  

System Tray:  
-- Program hides in the system tray to stay out of your way  
-- Can access various settings  

ZoomIn/ZoomOut:  
-- Use the scroll wheel to zoom in/out on the clip 

AHK Hotkeys:  
-- Has the ability to create autohotkey hotkeys that execute AHK code upon press while also activating the clip/gif  

Copy/Save:  
-- Use Ctrl + S to prompt a save window, can save the clip as Png, Jpg, Tiff, ect  
-- Use Ctrl + C to copy the clip to clipboard, using either win32 clipboard, or print screen  

Other Features:  
-- Tab will add the title bar back, and allow to be put in the task bar  
-- Right click on the clip will bring up a menu full of options  
-- Drawing on clips  
-- Reload button (if you make it into an EXE)  
-- Snapshot mode : freezes the screen while you choose an area to clip  
-- Delay mode : holds a picture of the screen in memory until you press the clip button again, then allows you to clip it  
-- Multi mode : lets you create any number of clips with the same clipping window (right click to close clipping window)  
-- Can open images as clips in the settings menu  
-- Can change the outline color of clips  
-- Auto copy clip  
-- Auto hide the clip in the task bar  
-- Can see a console window to check bugs and execute python code  
-- Change border thickness of the clip  
-- Enable/Disable a crosshair when in clipping window  

#Known Issues:  
-- Windows key hotkeys are not suppressed  
-- Copying the clip after drawing on it is a bit buggy  
-- Tray icon may persist if the program is closed without using the quit button  
