from PIL import ImageOps, ImageEnhance, ImageStat

import utils
from states.state import State


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
        # Get live type: solo or multi?, brighten as needed
        live_type_img = utils.screenshot(offset=(113, 13), size=(230, 36)).convert('L')
        lt_bright = ImageStat.Stat(live_type_img).rms[0]
        live_type_img = ImageEnhance.Brightness(live_type_img).enhance(100 / (lt_bright if lt_bright > 0 else 1))
        live_type_img = live_type_img.point(lambda p: p > 75 and 255)

        # Get bottom text on top left, brighten as needed
        bt_img = utils.screenshot(offset=(133, 53), size=(230, 22)).convert('L')
        bt_rms = ImageStat.Stat(bt_img).rms[0]
        bt_img = ImageEnhance.Brightness(bt_img).enhance(100 / (bt_rms if bt_rms > 0 else 1))
        bt_img = ImageOps.invert(bt_img)
        bt_img = bt_img.point(lambda p: p > 150 and 255)

        live_type, bt = utils.tess_en.get(live_type_img).lower(), utils.tess_jp.get(bt_img)
        valid_live = live_type == TeamSelect.SOLO or live_type == TeamSelect.MULTI
        valid_bt = bt == TeamSelect.SOLO_SELECT if live_type == TeamSelect.SOLO else bt == TeamSelect.MULTI_SELECT

        # Song select menu check
        if valid_live and not valid_bt:
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
            large_jacket_img = utils.screenshot(offset=(478, 78), size=(325, 325)).resize((70, 70))
            storage['jacket_img'] = self._jacket_img
            similar = utils.diff_ratio(self._jacket_img, large_jacket_img) <= 0.085
            if similar:
                self.__init__()
            return similar, storage, True
        elif self._samejacket < 3:
            # Get jacket from bottom left (position based on live type)
            if live_type == TeamSelect.SOLO:
                jacket_pos = (30, 525)
            elif live_type == TeamSelect.MULTI:
                jacket_pos = (31, 422)
            else:
                return False, storage, False
            jacket_img = utils.screenshot(offset=jacket_pos, size=(70, 70))
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