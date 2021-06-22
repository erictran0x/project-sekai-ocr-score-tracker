from PIL import ImageOps

import music_db
import utils
from consts import DIFFICULTIES
from states.state import State


class InGame(State):

    DIFF_COLORS = [0x65dd11, 0x32bcef, 0xffa900, 0xef4366, 0xbc32ee]
    DIFF_TITLES = ['easy', 'normal', 'hard', 'expert', 'master']

    def __init__(self):
        super().__init__(1)
        self._samedata = 0
        self._result = None

    def update(self, storage):
        # Obtain title and diff names for the first time
        from global_ import profile
        if self._samedata < 5:
            metadata_img = utils.screenshot()
            o, s = profile['TITLE']
            title_img = ImageOps.invert(metadata_img.convert('L')) \
                .crop((o[0], o[1], o[0] + s[0], o[1] + s[1])) \
                .point(lambda p: p > 140 and 255)

            # Get diff from pixel color and title from ocr
            diff_name = self._get_best_diff(*metadata_img.getpixel(profile['DIFF_PXL']))
            ocr_result = utils.tess_jp.get(title_img)

            if len(ocr_result) == 0 or diff_name is None:
                return False, storage, False
            if self._result != (diff_name, ocr_result):
                self._result = diff_name, ocr_result
                self._samedata = 0
            else:
                self._samedata += 1
                if self._samedata == 5:
                    storage['diff'], storage['title'] = self._result[0], music_db.closest_match(self._result[1])
                    self.log('Now playing: {1} [{0}]'.format(storage['diff'], storage['title']))
                    from main import output_np_info
                    from global_ import gsheets
                    pb = self._print_pb(
                        *gsheets.get_score(music_db.title_to_id(storage['title']),
                                           storage['diff'])) if gsheets is not None else 'N/A'
                    output_np_info('np: {1} [{0} {2}]'
                                   .format(storage['diff'], storage['title'],
                                           music_db.id_to_level(music_db.title_to_id(storage['title']),
                                                                DIFFICULTIES[storage['diff']])),
                                   'pb: {0}'
                                   .format(pb))
            return False, storage, False

        # If jacket found at top left, then result screen
        jacket_img_exp = storage['jacket_img']
        jacket_img_act = utils.screenshot(*profile['JACKET_RES'])
        if utils.diff_ratio(jacket_img_exp, jacket_img_act) <= 0.085:
            self.__init__()
            self.log('Entered result screen.')
            return True, storage, True

        # If add crystal button found, then no longer in game
        add_crystals_img = utils.screenshot(size=tuple(map(lambda x: x + 3, profile['PLUS_SYM'])))
        if _color_difference(*add_crystals_img.getpixel(profile['PLUS_SYM']), 0x00CCBB) <= 1500:
            self.__init__()
            self.log('Exited from live.')
            return True, storage, False

        # Still in game
        return False, storage, False

    @staticmethod
    def _print_pb(greats, goods, bads, misses):
        greats = int(greats) if greats.isnumeric() else 9999
        goods = int(goods) if goods.isnumeric() else 9999
        bads = int(bads) if bads.isnumeric() else 9999
        misses = int(misses) if misses.isnumeric() else -1
        if misses == -1:
            return 'N/A'
        if greats + goods + bads + misses == 0:
            return 'ALL PERFECT'
        if goods + bads + misses == 0:
            return 'Full Combo {0}'.format(f'({greats}great)' if greats < 5000 else '')
        return 'Cleared {0}'.format(f'({greats}great {goods}good {bads}bad {misses}miss)'
                                    if greats + goods + bads + misses < 5000 else '')

    @staticmethod
    def _get_best_diff(r, g, b):
        # Get diff title with lowest color difference that meets threshold
        best = float('inf'), None
        for i, dc in enumerate(InGame.DIFF_COLORS):
            d = _color_difference(r, g, b, dc)
            if d <= 750000 and d < best[0]:
                best = d, InGame.DIFF_TITLES[i]
        return best[1]


def _color_difference(ar, ag, ab, target):
    act = (ar << 16) | (ag << 8) | ab
    return abs(target - act)
