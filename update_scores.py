import sys
import requests

from consts import DIFFICULTIES
import music_db
from google_sheets import SheetsWrapper

SEKAI_BEST_LOGIN = r'https://strapi.sekai.best/auth/local'
SEKAI_BEST_ME = r'https://strapi.sekai.best/sekai-profiles/me'
GOOGLE_SHEETS_SCOPE = []


def main():
    if len(sys.argv) < 3:
        print('Too few arguments. Parameters: sekai_username sekai_password google_oauth [spreadsheet id]')

    sess = requests.Session()

    # Get sekai.best login data
    r = sess.post(SEKAI_BEST_LOGIN, {
        'identifier': sys.argv[1],
        'password': sys.argv[2]
    })
    if r.status_code != 200:
        if r.status_code == 400:
            j = r.json()
            if j['data'][0]['messages'][0]['id'] == 'Auth.form.error.invalid':
                print('Incorrect username and/or password.')
            else:
                print('Unknown error: {}'.format(j['data'][0]['messages'][0]['message']))
        else:
            print(f'Unknown error code {r.status_code}')
        return
    jwt = r.json()['jwt']
    r = sess.get(SEKAI_BEST_ME, headers={'authorization': f'Bearer {jwt}'})
    j = r.json()

    # Get user's project sekai score data from sekai.best login data
    if len(j['sekaiUserId']) == 0:
        print('Project Sekai profile not linked.')
        return
    scores = {}

    for s in j['sekaiUserProfile']['userMusics']:
        scores[s['musicId']] = [[]] * 5
        for u in s['userMusicDifficultyStatuses']:
            ind = DIFFICULTIES[u['musicDifficulty']]
            if len(u['userMusicResults']) == 0:  # not played check
                scores[s['musicId']][ind] = ['', '', '', '-1']
            else:
                pfc, fc = False, False
                for z in u['userMusicResults']:
                    if z['fullPerfectFlg']:
                        pfc = True
                    elif z['fullComboFlg']:
                        fc = True
                if pfc:   # all perfect check
                    scores[s['musicId']][ind] = ['0', '0', '0', '0']
                elif fc:  # full combo check
                    scores[s['musicId']][ind] = ['9999', '0', '0', '0']
                else:     # clear only check
                    scores[s['musicId']][ind] = ['9999', '9999', '9999', '9999']
    music_db.init()

    # 5 sheets (1 for each difficulty): id, title, great, good, bad, miss
    sw = SheetsWrapper()
    sw.create_new()
    sw.add_sheets(music_db.music, scores)
    sw.sort_entries()


if __name__ == '__main__':
    main()
