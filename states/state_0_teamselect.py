from PIL import ImageOps, ImageEnhance, ImageStat

import utils
from states.state import State
from consts import LIVE_TYPES


class TeamSelect(State):

    SOLO = 'solo live'
    MULTI = 'multi live'
    SOLO_SELECT = u'最終確認'
    MULTI_SELECT = u'難易度選択'

    def __init__(self):
        super().__init__(0)
        self._samescreen = 0
        self._samejacket = 0
        self._jacket_img = None
        self._jacket_img_tmp = None
        self._reset_np = True

    def update(self, storage):
        if self._reset_np:
            from main import output_np_info
            output_np_info('np: Looking for a song to play...', '')
            self._reset_np = False
        from global_ import profile
        # Get live type: solo or multi?, brighten as needed
        live_type_img = utils.screenshot(*profile['LIVE_TYPE']).convert('L')
        lt_bright = ImageStat.Stat(live_type_img).rms[0]
        live_type_img = ImageEnhance.Brightness(live_type_img).enhance(100 / (lt_bright if lt_bright > 0 else 1))
        live_type_img = live_type_img.point(lambda p: p > 75 and 255)

        # Get bottom text on top left, brighten as needed
        bt_img = utils.screenshot(*profile['LIVE_BT']).convert('L')
        bt_rms = ImageStat.Stat(bt_img).rms[0]
        bt_img = ImageEnhance.Brightness(bt_img).enhance(100 / (bt_rms if bt_rms > 0 else 1))
        bt_img = ImageOps.invert(bt_img).point(lambda p: p > 150 and 255)

        live_type, bt = utils.tess_en.get(live_type_img).lower(), utils.tess_jp.get(bt_img)

        # Song select menu check
        if live_type in LIVE_TYPES and bt != LIVE_TYPES[live_type]:
            if self._jacket_img is not None:
                self._samescreen += 1
                if self._samescreen == 10:
                    self.log(f'Resetting jacket image in {live_type}')
                    self._samescreen = 0
                    self._samejacket = 0
                    self._jacket_img = None
                    self._jacket_img_tmp = None
            return False, storage, False

        self._samescreen = 0
        if self._jacket_img is not None:
            # Look for jacket somewhere on the center, then compare it with the "smaller" one that we got initially
            # Assume w,h in SM_JACKET_SOLO and SM_JACKET_MULTI are equal
            large_jacket_img = utils.screenshot(*profile['LG_JACKET']).resize(profile['SM_JACKET_SOLO'][1])
            storage['jacket_img'] = self._jacket_img
            similar = utils.diff_ratio(self._jacket_img, large_jacket_img) <= 0.085
            if similar:
                self.__init__()
            return similar, storage, True
        elif self._samejacket < 3:
            # Get jacket from bottom left (position based on live type)
            if live_type == TeamSelect.SOLO:
                dims = profile['SM_JACKET_SOLO']
            elif live_type == TeamSelect.MULTI:
                dims = profile['SM_JACKET_MULTI']
            else:
                return False, storage, False
            jacket_img = utils.screenshot(*dims)
            if self._jacket_img_tmp is None:
                self._samejacket = 0
                self._jacket_img_tmp = jacket_img
            else:
                if utils.diff_ratio(self._jacket_img_tmp, jacket_img) <= 0.001:
                    self._samejacket += 1
                    if self._samejacket == 3:
                        self.log(f'Obtaining jacket image in {live_type}')
                        self._jacket_img = jacket_img
                else:
                    self._samejacket = 0
                self._jacket_img_tmp = jacket_img
        return False, storage, False
