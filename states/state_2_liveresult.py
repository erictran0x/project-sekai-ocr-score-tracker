from PIL import ImageOps, ImageStat, ImageEnhance, Image

import music_db
import utils
from consts import DIFFICULTIES, CHALLENGE_LIVE
from states.state import State


class LiveResult(State):

    AUTO = 'auto live'
    SCORE = 'score'

    def __init__(self):
        super().__init__(2)
        self._samedata = 0
        self._result = None

    def update(self, storage):
        # Check if in individual result screen
        from global_ import profile
        live_type = 'CHALLENGE' if storage['live_type'] in CHALLENGE_LIVE else 'SOLOMULTI'

        score_img = utils.screenshot(*profile[f'SCORE_LBL_{live_type}']).convert('L')
        score_img = ImageOps.invert(score_img).point(lambda p: p > 50 and 255)
        ocr_result = utils.tess_en.get(score_img).lower()
        if ocr_result != LiveResult.SCORE:
            return False, storage, False

        # Check if auto is enabled
        auto_img = utils.screenshot(*profile['AUTO_LBL']).convert('L')
        auto_img = ImageOps.invert(auto_img).point(lambda p: p > 55 and 255)
        ocr_result = utils.tess_en.get(auto_img).lower()
        if ocr_result == LiveResult.AUTO:
            self._samedata += 1
            if self._samedata == 8:
                self.log('Detected auto-live.')
                self.__init__()
                return True, storage, True
            return False, storage, False

        # Obtain judgement data
        result_img = utils.screenshot(*profile[f'LIVE_RESULT_{live_type}'])
        srcs = tuple(map(lambda x: x.point(lambda p: p > 170 and 255), result_img.split()))
        result_img = Image.merge('RGB', srcs).convert('L')
        result_img = ImageOps.invert(result_img)
        ocr_result = utils.tess_en.get(result_img, cache=False)
        ocr_result = [] if len(ocr_result) == 0 else list(filter(None, ocr_result.split('\n')))
        if len(ocr_result) != 4:
            return False, storage, False
        ocr_result_int = list(map(lambda s: int(s) if s.isnumeric() else -99999, ocr_result))

        # Non-positive = data hasn't shown up yet or not read correctly
        if sum(ocr_result_int) <= 0:
            return False, storage, False

        # Store result once actually found it
        if self._result != ocr_result_int:
            self._result = ocr_result_int
            self._samedata = 0
        else:
            self._samedata += 1
            if self._samedata == 10:
                self.log(f'Live result: {self._result}')
                self.update_score_to_gsheets(storage['title'], storage['diff'])
                self.__init__()
                return True, storage, True
        return False, storage, False

    def update_score_to_gsheets(self, title, diff):
        # Get row number by song title
        m_id = music_db.title_to_id(title)
        if m_id is None:
            self.log(f'{title} not in music database.')
            return
        from global_ import gsheets
        row = gsheets.find(m_id, diff)
        if row is None:
            # Just add new score if possible, no need to compare since this will be the first score
            self.log(f'Adding {title} to spreadsheet...')
            score = {m_id: [['', '', '', '-1']] * 5}
            score[m_id][DIFFICULTIES[diff]] = self._result
            if gsheets.add_songs({title: m_id}, score) is None:
                self.log(f'Unable to add {title} to spreadsheet. Live result will not be recorded.')
            else:
                gsheets.update_score_cache(m_id, diff, list(map(str, self._result)))
                gsheets.sort_entries()
            return

        # Get score data stored in cache
        old_res = list(map(lambda x: int(x) if x.isnumeric() else 9999, gsheets.get_score(m_id, diff)))

        # Compare with current result
        if self.calc_result_score(*self._result) > self.calc_result_score(*old_res):
            self.log(f'Higher score than previously recorded live result')

            # Update score data in sheet with current result
            gsheets.edit(f'{diff}!E{row}:H{row}', [self._result])
            gsheets.update_score_cache(m_id, diff, list(map(str, self._result)))
        else:
            self.log(f'Lower/same score than previously recorded live result')

    @staticmethod
    def calc_result_score(greats, goods, bads, misses):
        # all perfect = 0 (max score) ; not played < clear only < full combo < 0
        return float('-inf') if misses == -1 else greats * -1 + (goods + bads + misses) * -10000
