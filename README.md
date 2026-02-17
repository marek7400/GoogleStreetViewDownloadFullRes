# Google Street View Panorama Download Full Resolution

The free version of **Street View Download 360** does not allow you to download panoramas in full resolution  
(free max **3328×1664**).

Full resolution download is available only in the paid **PRO** version.

This script downloads panorama tiles and combines them into a complete image.

---

## INSTALLATION

### 1. Install Python 3
If you don’t have it installed, download Python 3 from:  
https://www.python.org/downloads/

---

### 2. Install ImageMagick (DLL version)

Download from:  
https://imagemagick.org/script/download.php#windows

During installation, make sure to select:

- ✅ **Install legacy utilities (e.g. convert)**
- ✅ **Add application directory to your system path**

> ⚠️ If you do not select “Install legacy utilities,” the script will fail on the `convert` command.

---

### 3. Install aria2 (win-64bit version)

Download from GitHub:  
https://github.com/aria2/aria2/releases

Steps:
- Unzip the archive
- Locate `aria2c.exe`
- Copy `aria2c.exe` to `C:\Windows`  
  *(easiest method to make it globally accessible)*  

**OR**

- Add the folder containing `aria2c.exe` to your system `PATH`

---

### 4. Install ExifTool

Download from:  
https://exiftool.org

Steps:
- Unzip the archive
- Find the file: `exiftool(-k).exe`
- Rename it to: `exiftool.exe` (remove `(-k)`)
- Move `exiftool.exe` to `C:\Windows`  
  *(or add its folder to PATH)*

Copy the entire folder:
exiftool_files

to:

C:\Windows


---

## Download the Python Script

Download the appropriate script file:

- `streetview-dl8.py` → for **8192×4096** (zoom4)
- `streetview-dl16.py` → for **16384×8192** (zoom5)

---

# RUNNING THE SCRIPT

### For 16384×8192:

`python streetview-dl16.py "https://www.google.com/maps/@41.3881837,2.1698939,3a,75y,143.45h,92.72t/data=!3m6!1e1!3m4!1sr3vUp9U2ss5fwoq1Roxizw!2e0!7i16384!8i8192"`

Or using Panorama ID:

python streetview-dl16.py PANORAMA_ID

python streetview-dl16.py dATvHl4xpoL8FDbu5Elkmw

Or using a full Google Maps Street View link:

`python streetview-dl16.py "https://www.google.pl/maps/place/Kraków/@50.0615594,19.9386523,3a,75y,253.11h,88.2t/data=!3m7!1e1!3m5!1sdATvHl4xpoL8FDbu5Elkmw!2e0!6shttps:%2F%2Fstreetviewpixels-pa.googleapis.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D1.8004397899011906%26panoid%3DdATvHl4xpoL8FDbu5Elkmw%26yaw%3D253.1113592416134!7i16384!8i8192!4m6!3m5!1s0x471644c0354e18d1:0xb46bb6b576478abf!8m2!3d50.0646501!4d19.9449799!16zL20vMDQ5MXk?entry=ttu&g_ep=EgoyMDI2MDIxMS4wIKXMDSoASAFQAw%3D%3D"`

#  Viewing the Panorama Correctly

To properly view the downloaded panorama (otherwise it will appear distorted), load the image into a viewer such as:

Street View Download 360

https://svd360.com/

Use the menu option:
360 degrees Panorama Viewer
From there, you can export (take a screenshot of) a selected section of the panorama.

![360 degrees Panorama Viewer](SVD360view.jpg)



