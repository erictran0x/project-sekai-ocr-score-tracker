import math
from ctypes import windll

import win32ui
from PIL import ImageChops, ImageStat, Image
from tesserocr import PyTessBaseAPI, PSM
import win32gui


def screenshot(offset=None, size=None):
    x, y, x1, y1 = win32gui.GetClientRect(hwnd)
    if size is None:
        w, h = x1 - x, y1 - y
    elif offset is None:
        w, h = size
    else:
        w, h = (sum(s) for s in zip(offset, size))

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    save_bit_map = win32ui.CreateBitmap()
    save_bit_map.CreateCompatibleBitmap(mfc_dc, w, h)

    save_dc.SelectObject(save_bit_map)

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 1)

    bmpinfo = save_bit_map.GetInfo()
    bmpstr = save_bit_map.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(save_bit_map.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    if result > 0:
        return im.crop((offset[0], offset[1], w, h)) if offset is not None else im
    else:
        return None


def diff_ratio(img_1, img_2):
    diff_img = ImageChops.difference(img_1, img_2)
    diff = ImageStat.Stat(diff_img)
    return sum(diff.mean) / (len(diff.mean) * 255)


def closest_match(match, datadict):
    # Perfect match? don't try to find closest one
    if match in datadict:
        return match
    best_score, best_match = 0.7, match

    # Convert input title to byte array
    match = match.lower()
    v1 = list(match.encode('utf8'))
    for z in datadict.keys():
        # Same title but different casing? found match
        z_old, z = z, z.lower()
        if match == z:
            return z_old

        # Convert expected title to byte array
        v2 = list(z.encode('utf8'))

        # Compute Jaro distance
        l1, l2 = len(v1), len(v2)
        max_dist = math.floor(max(l1, l2) / 2) - 1
        hash_v1, hash_v2 = [0] * l1, [0] * l2
        m = 0
        for i in range(l1):
            for j in range(max(0, i - max_dist), min(l2, i + max_dist + 1)):
                if v1[i] == v2[j] and hash_v2[j] == 0:
                    hash_v1[i] = 1
                    hash_v2[j] = 1
                    m += 1
                    break
        if m == 0:
            continue
        t = 0
        point = 0
        for i in range(l1):
            if hash_v1[i] == 1:
                while hash_v2[point] == 0:
                    point += 1
                if v1[i] != v2[point]:
                    t += 1
                point += 1
        t /= 2
        score = ((m / l1) + (m / l2) + ((m - t) / m)) / 3
        if score > best_score:
            best_score, best_match = score, z_old
    return best_match


class TessWrapper:

    def __init__(self, lang):
        self._obj = PyTessBaseAPI(lang=lang)
        self._obj.SetPageSegMode(PSM.SINGLE_BLOCK)
        self._cache = {}

    def __del__(self):
        self._obj.End()

    def get(self, img, cache=True):
        if cache:
            hs = self._hash_img(img)
            if hs not in self._cache:
                self._obj.SetImage(img)
                self._cache[hs] = self._obj.GetUTF8Text().strip()
            return self._cache[hs]
        else:
            self._obj.SetImage(img)
            return self._obj.GetUTF8Text().strip()

    @staticmethod
    def _hash_img(img):
        img = img.resize((40, 40), Image.ANTIALIAS).convert("L")
        pixel_data = list(img.getdata())
        avg_pixel = sum(pixel_data) / len(pixel_data)
        bits = "".join(['1' if (px >= avg_pixel) else '0' for px in pixel_data])
        return str(hex(int(bits, 2)))[2:][::-1].upper()


hwnd = None
tess_en = TessWrapper('eng')
tess_jp = TessWrapper('jpn')
