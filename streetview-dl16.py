import sys
import os
import subprocess
import hashlib
import zlib
import time
import random

# --- KONFIGURACJA ULTRA MAX (16K) ---
# ZOOM 5 (Pełna sfera matematyczna):
# Szerokosc: 32 kafelki (0-31) -> 16384 px
# Wysokosc: 16 kafelkow (0-15) -> 8192 px
# Liczba plikow: 512
ZOOM_LEVEL = 5
TILE_WIDTH = 512
TILE_HEIGHT = 512

# Definicja siatki (grid)
GRID_X = 31  # Indeks od 0 do 31 (czyli 32 kolumny)
GRID_Y = 15  # Indeks od 0 do 15 (czyli 16 wierszy)
TILE_GEO = "32x16" # Układ kafelków dla ImageMagick

if len(sys.argv) < 2:
    print("Uzycie: python streetview-dl.py <ID_PANORAMY>")
    sys.exit(0)

def execute_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Info: {e}")

def add_exif_equi(path, width, height):
    # Metadane dla 360
    cmd = (f'exiftool -overwrite_original -UsePanoramaViewer=True -ProjectionType=equirectangular '
           f'-PoseHeadingDegrees=180.0 -CroppedAreaLeftPixels=0 -FullPanoWidthPixels={width} '
           f'-CroppedAreaImageHeightPixels={height} -FullPanoHeightPixels={height} '
           f'-CroppedAreaImageWidthPixels={width} -CroppedAreaTopPixels=0 -LargestValidInteriorRectLeft=0 '
           f'-LargestValidInteriorRectTop=0 -LargestValidInteriorRectWidth={width} '
           f'-LargestValidInteriorRectHeight={height} -Model="StreetView 16K Python" "{path}"')
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
        return f"op{id_hash}{crc:08x}"
    def get_id_src(self): return self.id_src
    def get_id_op(self): return self.id_op

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

    def download_aria2c(self):
        path = self.make_tmp_path() + ".txt"
        content = ""
        for item in self.url_list:
            content += f"{item[0]}\n out={item[1]}\n"
        with open(path, "w") as f:
            f.write(content)
        
        # Uzywamy user-agent i limitow, zeby Google nie zerwal polaczenia przy 500 plikach
        cmd = (f'aria2c -x 8 -j 8 --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
               f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36" -i "{path}"')
        execute_command(cmd)
        
        if os.path.exists(path): os.remove(path)

    def remove_files(self):
        for item in self.url_list:
            if os.path.exists(item[1]):
                try: os.remove(item[1])
                except: pass

class OpSt:
    def __init__(self, pano_id):
        self.op_id = OpId(pano_id)
        self.op_url_list = OpUrlList()

    def make_img_list(self):
        self.op_url_list.clear()
        num_file = 1
        codigo = self.op_id.get_id_src()
        id_op = self.op_id.get_id_op()

        # Petla po calej siatce 32x16
        for y_act in range(0, GRID_Y + 1):
            for x_act in range(0, GRID_X + 1):
                url = (f"https://streetviewpixels-pa.googleapis.com/v1/tile?"
                       f"cb_client=maps_sv.tactile&panoid={codigo}&x={x_act}&y={y_act}&zoom={ZOOM_LEVEL}&nbt=1&fover=2")
                
                # Format nazwy pliku musi byc spojny z kolejnoscia petli!
                file_name = f"tmp-f{id_op}_{num_file}.jpg"
                num_file += 1
                self.op_url_list.add_url(url, file_name)

    def make_montage(self):
        id_op = self.op_id.get_id_op()
        id_src = self.op_id.get_id_src()
        
        file_list_data = ""
        total_tiles = (GRID_X + 1) * (GRID_Y + 1) # Powinno wyjsc 512
        
        print(f"Weryfikacja {total_tiles} kafelkow (to wazne dla zachowania geometrii)...")
        
        # Kluczowe: Jesli kafelka brakuje, wstawiamy czarny kwadrat.
        # ImageMagick potrzebuje idealnie 512 plikow, zeby ulozyc siatke 32x16.
        for i in range(1, total_tiles + 1):
            fname = f"tmp-f{id_op}_{i}.jpg"
            
            # Jesli brak pliku lub pusty -> generuj czarny
            if not os.path.exists(fname) or os.path.getsize(fname) == 0:
                subprocess.run(f'magick convert -size {TILE_WIDTH}x{TILE_HEIGHT} xc:black "{fname}"', shell=True)
            
            file_list_data += f"{fname}\n"
        
        file_list_path = os.path.join(os.getcwd(), f"tmp-fl{id_op}.txt")
        with open(file_list_path, "w") as f:
            f.write(file_list_data)

        output_file = f"stl-{id_src}.jpg"
        
        print("Rozpoczynanie sklejania (Montage)... Moze zajac minute.")
        # Parametr limit memory pomaga przy duzych obrazach
        montage_cmd = (f'magick montage @{file_list_path} -tile {TILE_GEO} '
                       f'-geometry {TILE_WIDTH}x{TILE_HEIGHT}+0+0 -quality 97 -define registry:temporary-path=. "{output_file}"')
        
        execute_command(montage_cmd)
        
        if os.path.exists(file_list_path): os.remove(file_list_path)

    def download(self):
        print(f"--- START: Zoom {ZOOM_LEVEL} ---")
        print(f"Rozdzielczosc docelowa: 16384 x 8192 px")
        print(f"Liczba kafelkow: {(GRID_X+1)*(GRID_Y+1)}")
        
        self.make_img_list()
        print("Pobieranie kafelkow...")
        self.op_url_list.download_aria2c()
        
        self.make_montage()
        
        print("Czyszczenie smieci...")
        self.op_url_list.remove_files()

# --- START ---

try:
    target_arg = sys.argv[1]
except IndexError:
    print("Brak ID.")
    sys.exit(0)

if "!" in target_arg:
    try: target_id = target_arg.split("!1s")[1].split("!")[0]
    except: target_id = target_arg
else:
    target_id = target_arg

print(f"ID Panoramy: {target_id}")

op_st = OpSt(target_id)
op_st.download()

pathL = f"stl-{target_id}.jpg"

if not os.path.exists(pathL):
    print("BLAD: Nie udalo sie utworzyc pliku stl-*.jpg. Sprawdz czy masz ImageMagick.")
    sys.exit(1)

# Ustawiamy rozmiary wynikowe dla EXIF
final_w = (GRID_X + 1) * TILE_WIDTH
final_h = (GRID_Y + 1) * TILE_HEIGHT

print(f"Dodawanie tagow EXIF do pliku {pathL}...")
try:
    add_exif_equi(pathL, final_w, final_h)
except:
    pass

print(f"SUKCES. Plik gotowy: {pathL}")