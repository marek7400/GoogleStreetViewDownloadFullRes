import sys
import os
import subprocess
import hashlib
import zlib
import time
import random
import urllib.request  # Dodane do pobierania z opóźnieniem

# --- KONFIGURACJA ---
# ZOOM_LEVEL 4 (High):
# - Szerokosc: 16 kafli (8192px) - pelne 360 stopni
# - Wysokosc: 8 kafli (4096px) - proporcja 2:1
ZOOM_LEVEL = 4 

# OPÓŹNIENIE (w milisekundach):
# 0 = brak opóźnienia (używa aria2c, tryb szybki/równoległy)
# >0 = pobieranie sekwencyjne z pauzą (bezpieczniejsze dla IP)
DELAY_MS = 500 

if len(sys.argv) < 2:
    print("Uzycie: python streetview-dl.py <ID_PANORAMY>")
    sys.exit(0)

def execute_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Blad komendy: {cmd}")

def resize_equi(path_src, path_dst, width):
    height = int(width / 2)
    cmd = f'magick "{path_src}" -resize {width}x{height}! -quality 95 "{path_dst}"'
    execute_command(cmd)

def add_exif_equi(path, width):
    height = int(width / 2)
    cmd = (f'exiftool -overwrite_original -UsePanoramaViewer=True -ProjectionType=equirectangular '
           f'-PoseHeadingDegrees=180.0 -CroppedAreaLeftPixels=0 -FullPanoWidthPixels={width} '
           f'-CroppedAreaImageHeightPixels={height} -FullPanoHeightPixels={height} '
           f'-CroppedAreaImageWidthPixels={width} -CroppedAreaTopPixels=0 -LargestValidInteriorRectLeft=0 '
           f'-LargestValidInteriorRectTop=0 -LargestValidInteriorRectWidth={width} '
           f'-LargestValidInteriorRectHeight={height} -Model="StreetView DL Python" "{path}"')
    execute_command(cmd)

class OpId:
    def __init__(self, raw_id):
        self.id_src = raw_id
        self.id_op = self.make_id(raw_id)

    def make_id(self, raw_id):
        ripemd = hashlib.new('ripemd160')
        ripemd.update(raw_id.encode('utf-8'))
        id_hash = ripemd.hexdigest()
        crc = zlib.crc32(id_hash.encode('utf-8')) & 0xffffffff
        id_crc = f"{crc:08x}"
        return f"op{id_hash}{id_crc}"

    def get_id_src(self):
        return self.id_src
    def get_id_op(self):
        return self.id_op

class OpUrlList:
    def __init__(self):
        self.url_list = []
    def clear(self):
        self.url_list = []
    def add_url(self, url, file_path):
        self.url_list.append((url, file_path))
    def make_tmp_path(self):
        seed = str(time.time() + random.randint(1, 100000))
        h = hashlib.new('ripemd160')
        h.update(seed.encode('utf-8'))
        return os.path.join(os.getcwd(), "tmp-" + h.hexdigest())

    def download(self):
        if DELAY_MS > 0:
            self.download_slow()
        else:
            self.download_aria2c()

    def download_slow(self):
        print(f"Tryb bezpieczny: Pobieranie sekwencyjne (opóźnienie {DELAY_MS}ms)...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        for i, (url, file_path) in enumerate(self.url_list):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
                    out_file.write(response.read())
                
                if i < len(self.url_list) - 1:
                    time.sleep(DELAY_MS / 1000.0)
            except Exception as e:
                print(f"Blad pobierania kafelka {i}: {e}")

    def download_aria2c(self):
        path = self.make_tmp_path() + ".txt"
        content = ""
        for item in self.url_list:
            content += f"{item[0]}\n out={item[1]}\n"
        
        with open(path, "w") as f:
            f.write(content)
        
        # -x 8: wiecej polaczen dla szybkosci
        cmd = f'aria2c -x 8 -j 8 -i "{path}"'
        execute_command(cmd)
        
        if os.path.exists(path):
            os.remove(path)

    def remove_files(self):
        for item in self.url_list:
            if os.path.exists(item[1]):
                try: os.remove(item[1])
                except: pass

class OpSt:
    def __init__(self, pano_id):
        self.op_id = OpId(pano_id)
        self.op_url_list = OpUrlList()
        
        if ZOOM_LEVEL == 4:
            self.x_fin = 15 
            self.y_fin = 7   
            self.tile_geo = "16x8"
        else:
            self.x_fin = 25
            self.y_fin = 12
            self.tile_geo = "26x13"

    def make_img_list(self):
        self.op_url_list.clear()
        num_file = 1
        codigo = self.op_id.get_id_src()
        id_op = self.op_id.get_id_op()

        for y_act in range(0, self.y_fin + 1):
            for x_act in range(0, self.x_fin + 1):
                url = (f"https://streetviewpixels-pa.googleapis.com/v1/tile?"
                       f"cb_client=maps_sv.tactile&panoid={codigo}&x={x_act}&y={y_act}&zoom={ZOOM_LEVEL}&nbt=1&fover=2")
                
                file_name = f"tmp-f{id_op}_{num_file}.jpg"
                num_file += 1
                self.op_url_list.add_url(url, file_name)

    def make_montage(self):
        id_op = self.op_id.get_id_op()
        id_src = self.op_id.get_id_src()
        
        file_list_data = ""
        total_tiles = (self.x_fin + 1) * (self.y_fin + 1)
        
        for i in range(1, total_tiles + 1):
            fname = f"tmp-f{id_op}_{i}.jpg"
            if not os.path.exists(fname) or os.path.getsize(fname) == 0:
                subprocess.run(f'magick convert -size 512x512 xc:black "{fname}"', shell=True)
            file_list_data += f"{fname}\n"
        
        file_list_path = os.path.join(os.getcwd(), f"tmp-fl{id_op}.txt")
        with open(file_list_path, "w") as f:
            f.write(file_list_data)

        output_file = f"stl-{id_src}.jpg"
        
        montage_cmd = (f'magick montage @{file_list_path} -tile {self.tile_geo} -geometry 512x512+0+0 '
                       f'-quality 100 "{output_file}"')
        
        print(f"Skladanie (Montage) -> {output_file}...")
        execute_command(montage_cmd)
        
        if os.path.exists(file_list_path):
            os.remove(file_list_path)

    def download(self):
        print(f"Pobieranie (Zoom {ZOOM_LEVEL}, Siatka {self.tile_geo})...")
        self.make_img_list()
        self.op_url_list.download() # Uzywa nowej logiki wyboru metody
        print("Montaz...")
        self.make_montage()
        print("Czyszczenie...")
        self.op_url_list.remove_files()

# --- START ---

try:
    target_arg = sys.argv[1]
except IndexError:
    print("Blad: Nie podano ID.")
    sys.exit(0)

if "!" in target_arg:
    try:
        target_id = target_arg.split("!1s")[1].split("!")[0]
    except:
        target_id = target_arg
else:
    target_id = target_arg

print(f"ID: {target_id}")

op_st = OpSt(target_id)
op_st.download()

pathL = f"stl-{target_id}.jpg"

if not os.path.exists(pathL):
    print("Blad: Plik nie powstal.")