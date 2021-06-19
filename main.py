from win32gui import FindWindow
import sys
import time
import utils
import global_


def log(s):
    print(f'[Main] {s}')


def output_np_info(np, pb):
    if not global_.stream_mode:
        return
    print(np, pb)
    with open('now_playing.txt', 'w', encoding='utf-8') as fp:
        fp.write(np)
    with open('personal_best.txt', 'w') as fp:
        fp.write(pb)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        log('Too few arguments. Usage: window_name [google_sheets_id] [--stream]')
    elif len(sys.argv) > 4:
        log('Too many arguments. Usage: window_name [google_sheets_id] [--stream]')
    else:
        # Find window by title
        utils.hwnd = FindWindow(None, sys.argv[1])
        if utils.hwnd:
            import google_sheets
            import state_machine
            if len(sys.argv) >= 3 and sys.argv[2 - len(sys.argv)] != '--stream':
                sheet_id = sys.argv[2 - len(sys.argv)]
            else:
                sheet_id = None
            global_.stream_mode = len(sys.argv) >= 3 and sys.argv[-1] == '--stream'
            if global_.stream_mode:
                log('Stream mode enabled. Now playing and personal best will be outputted to file.')
            if sheet_id is not None:
                global_.gsheets = google_sheets.SheetsWrapper(sheet_id)
            sm = state_machine.StateMachine()  # Assume initial state of 0
            log('Ready.')
            try:
                target = 0.0167  # Only run at ~60fps
                while True:
                    start = time.time()
                    sm.update()
                    diff = time.time() - start
                    if diff < target:
                        time.sleep(target - diff)
            except KeyboardInterrupt:
                log('Detected KeyboardInterrupt. Stopping...')
        else:
            log(f'Unable to find window \"{sys.argv[1]}\". Exiting...')
