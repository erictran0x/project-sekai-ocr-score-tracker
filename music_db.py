import os
import pickle
import time

import requests

import utils
from consts import DIFFICULTIES

SEKAI_MUSIC_DB = r'https://sekai-world.github.io/sekai-master-db-diff/musics.json'
SEKAI_LEVEL_DB = r'https://sekai-world.github.io/sekai-master-db-diff/musicDifficulties.json'
CACHE_FILE = r'cache.pk1'
music = {}
level = {}


def init(force=False):
    global music, level
    if force or not os.path.exists(CACHE_FILE) or (time.time() - os.path.getmtime(CACHE_FILE)) >= 259200:
        # Store project sekai music database to a dict (song title -> song id)
        r = requests.get(SEKAI_MUSIC_DB)
        for m in r.json():
            music[m['title']] = int(m['id'])
            level[int(m['id'])] = [0] * 5

        # Store project sekai level database to a dict (song id -> [easy, normal, hard, expert, master])
        r = requests.get(SEKAI_LEVEL_DB)
        for d in r.json():
            level[d['musicId']][DIFFICULTIES[d['musicDifficulty']]] = d['playLevel']
        with open(CACHE_FILE, 'wb') as fp:
            pickle.dump(music, fp, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open(CACHE_FILE, 'rb') as fp:
            music = pickle.load(fp)


def title_to_id(m_title):
    global music
    if m_title not in music:
        init(True)
    return music[m_title] if m_title in music else None


def id_to_level(m_id, diff_id):
    global level
    if m_id not in level:
        init(True)
    return level[m_id][diff_id] if m_id in level else None


def closest_match(m_title):
    global music
    if m_title not in music:
        init(True)
    return utils.closest_match(m_title, music)
