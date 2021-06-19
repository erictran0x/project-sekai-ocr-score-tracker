import os
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from consts import TITLES, DIFFICULTIES
from music_db import id_to_level


class SheetsWrapper:

    def __init__(self, sheet=None):
        if os.path.exists('credentials.json'):
            scopes = [r'https://www.googleapis.com/auth/spreadsheets']
            """ Taken from Google Sheets API Python Quickstart """
            creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', scopes)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', scopes)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            self._obj = service.spreadsheets()
            self._sheet = sheet
            self._sheet_id_cache = {}
            self._score_cache = {}

            # Check that spreadsheet exists
            if self._sheet is not None:
                r = self._obj.get(spreadsheetId=self._sheet).execute()
                if 'error' in r and r['error']['code'] == 404:
                    self.log('Spreadsheet id not found. Scores will be logged to a new spreadsheet.')
                    self.create_new()
                else:
                    self.log(f'Scores will be logged to spreadsheet with id: {self._sheet}')
        else:
            self.log('credentials.json not found. Scores will not be logged.')
            self._obj = None
            self._sheet = None
            self._sheet_id_cache = None

    def __del__(self):
        if self._obj is not None:
            self._obj.close()

    def create_new(self):
        if self._obj is None:
            return
        # Create spreadsheet, store its id
        b = {'properties': {'title': f'project-sekai-ocr-score-tracker-{datetime.now().strftime("%c")}'}}
        r = self._obj.create(body=b, fields='spreadsheetId').execute()
        res = r.get('spreadsheetId')

        # Current session spreadsheet id = result; always return result
        self._sheet = res
        self.log(f'New spreadsheet id: {res}')

    def add_sheets(self, musics=None, scores=None):
        if self._obj is None or self._sheet is None:
            return
        # Add blank sheets
        self.batch([{'addSheet': {'properties': {'title': t}}} for t in TITLES])

        for i, t in enumerate(TITLES):
            # Add table headers to each sheet
            self.edit(f'{t}!A1:H1', [['ID', 'Title', 'Level', 'Status', 'Greats', 'Goods', 'Bads', 'Misses']])

        # Add scores if music database is available
        if musics is not None:
            self.add_songs(musics, scores)

        # Hide Sheet0 from visibility, will be used for lookups instead
        self.batch([{'updateSheetProperties': {
            'properties': {'sheetId': 0, 'hidden': True}, 'fields': 'hidden'}
        }])

    def add_songs(self, musics, scores=None):
        if self._obj is None or self._sheet is None:
            return
        # Only find first empty cell in column Easy!A, assuming all music titles exist in all sheets
        col = len(self.get('Easy!A1:A')) + 1

        # Add music id and title (and score if available) to all sheets
        for i, t in enumerate(TITLES):
            data = [
                ([musics[k], k, id_to_level(musics[k], DIFFICULTIES[t.lower()])]
                 + write_scores(int(musics[k]), i, scores))
                for j, k in enumerate(musics.keys())]
            self.edit(f'{t}!A{col}:H', data)
        return col

    def sort_entries(self):
        if self._obj is None or self._sheet is None:
            return
        # Sort sheets
        self.batch([{'sortRange': {
            'range': {
                'sheetId': self.get_sheet_id(t),
                'startRowIndex': 1,
                'startColumnIndex': 0,
                'endColumnIndex': 8
            },
            'sortSpecs': [
                {'sortOrder': 'ASCENDING', 'dimensionIndex': 2}, {'sortOrder': 'ASCENDING', 'dimensionIndex': 0}
            ]}} for t in TITLES])

    def cache_scores(self):
        if self._obj is None or self._sheet is None:
            return
        for t in TITLES:
            for row in self.get(f'{t}!A2:H'):
                music_id = row[0]
                score = row[4:8]
                if music_id.isnumeric():
                    music_id = int(music_id)
                else:
                    continue
                if music_id not in self._score_cache:
                    self._score_cache[music_id] = [['', '', '', '-1']] * 5
                self._score_cache[music_id][DIFFICULTIES[t.lower()]] = score

    def update_score_cache(self, music_id, diff, score):
        if music_id not in self._score_cache:
            self._score_cache[music_id] = [['', '', '', '-1']] * 5
        self._score_cache[music_id][DIFFICULTIES[diff]] = score

    def get_score(self, music_id, diff):
        if music_id not in self._score_cache:
            self.cache_scores()
        return self._score_cache[music_id][DIFFICULTIES[diff]] if music_id in self._score_cache else ['', '', '', '-1']

    def find(self, music_id, diff):
        if self._obj is None or self._sheet is None:
            return
        # Get row number by music_id
        rng = 'Sheet1!A1'
        self.edit(rng, [[f'=MATCH({music_id}, {diff}!A2:A, 0)+1']])
        res = self.get(rng)[0][0]
        return res if res != '#N/A' else None

    def edit(self, rng, values):
        if self._obj is None or self._sheet is None:
            return
        self._obj.values().update(
            spreadsheetId=self._sheet, range=rng, valueInputOption='USER_ENTERED', body={'values': values}
        ).execute()

    def batch(self, body):
        if self._obj is None or self._sheet is None:
            return
        self._obj.batchUpdate(spreadsheetId=self._sheet, body={'requests': body}).execute()

    def get(self, rng):
        if self._obj is None or self._sheet is None:
            return
        r = self._obj.values().get(spreadsheetId=self._sheet, range=rng).execute()
        return r.get('values')

    def get_sheet_id(self, s_name):
        if s_name not in self._sheet_id_cache:
            r = self._obj.get(spreadsheetId=self._sheet).execute()
            for s in r.get('sheets'):
                p = s['properties']
                self._sheet_id_cache[p['title']] = p['sheetId']
        return self._sheet_id_cache[s_name]

    @staticmethod
    def log(s):
        print(f'[SheetsWrapper] {s}')


def write_scores(music_id, diff_index, scores=None):
    status = '=IF(SUM(INDIRECT(CONCAT("E", ROW())&":"&CONCAT("H", ROW())))=0,"ALL PERFECT",' \
              'IF(SUM(INDIRECT(CONCAT("F", ROW())&":"&CONCAT("H", ROW())))=0,"Full Combo",' \
              'IF(INDIRECT(CONCAT("H", ROW()))=-1,"not played", "Cleared")))'
    if scores is None or music_id not in scores:
        return [status, '', '', '', '-1']
    return [status] + scores[music_id][diff_index]
