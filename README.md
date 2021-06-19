# Project SEKAI OCR Score Tracker

## Purpose
This program stores accuracy data (# perfects, greats, etc.) to a Google spreadsheet.
SEGA/Colorful Palette doesn't do this for some reason, hence why this was made.

## Requiresments
- [tesserocr](https://github.com/sirfz/tesserocr), an API for [Google's Tesseract](https://github.com/tesseract-ocr/tesseract)
- Python 3.7 (may not work with 3.8+)
- everything in `requirements.txt`

## Usage
For Android users, I recommend [scrcpy](https://github.com/Genymobile/scrcpy) for fast, low-latency capturing.
For Apple users, [iOS Screen Recorder](https://drfone.wondershare.com/ios-screen-recorder.html) probably works.

This program uses Google Sheets API to create spreadsheets and read/write their entries.
To obtain your credentials, you will have to create a Google Cloud Platform project and enable the Google Sheets API.
More information about this can be found [here](https://developers.google.com/workspace/guides/create-project)
and [here](https://developers.google.com/workspace/guides/create-credentials#desktop).

To create a profile for your device, refer to the provided profile at `profiles/pixel3a_1280_624.txt`.
Note that dimensions for jacket images must be exact, but such for everything else can have some margin of error.

Execute `python main.py profile_name window_name [google_sheets_id] [--stream]` to run the program.
- `profile_name` is the file name of the profile, minus the `profiles` directory and `.txt` file format.
- `window_name` is the name of the window used to capture your device.
- `google_sheets_id` is the id of the Google spreadsheet of the stored data.
- `--stream` outputs the currently playing song to `now_playing.txt`
  and your personal best to `personal_best.txt`.
  
Execute `python update_scores.py username password` to generate a Google spreadsheet
containing accuracy data derived by clear status.
- `username` is your [sekai.best](https://sekai.best) username.
- `password` is your sekai.best password.
- Make sure that you link your Project SEKAI profile to your sekai.best account.

## Testing
Tested using a Google Pixel 3a and Python 3.7.

## TODO
- Add support for challenge lives and cheerful lives
- Ensure correctness for multi lives