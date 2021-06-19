import math
import os
import time
import pickle
import requests
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
    # Perfect match? don't try to find closest one
    if m_title in music:
        return m_title
    best_score, best_title = 0, m_title

    # Convert input title to byte array
    m_title = m_title.lower()
    v1 = list(m_title.encode('utf8'))
    for z in music.keys():
        # Same title but different casing? found match
        z_old, z = z, z.lower()
        if m_title == z:
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
            best_score, best_title = score, z_old
    return best_title
