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
    log('{0} | {1}'.format(np, pb))
    with open('now_playing.txt', 'w', encoding='utf-8') as fp:
        fp.write(np)
    with open('personal_best.txt', 'w') as fp:
        fp.write(pb)


def parse_profile(f):
    with open(f'profiles/{f}.txt', 'r') as fp:
        line = fp.readline()
        while line:
            line = line.strip()
            # Skip blank lines or commented lines
            if len(line) > 0 and not line.startswith('#'):
                # Assume line is in format key=val
                key, val = line.split('=')
                val = tuple(map(int, val.split(',')))

                # Assume val is in format x,y,w,h or x,y
                if len(val) == 4:
                    val = (val[0], val[1]), (val[2], val[3])
                global_.profile[key] = val
            line = fp.readline()
    log(f'Using profile {f}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        log('Too few arguments. Usage: profile_name window_name [google_sheets_id] [--stream]')
    elif len(sys.argv) > 5:
        log('Too many arguments. Usage: profile_name window_name [google_sheets_id] [--stream]')
    else:
        # Find window by title
        utils.hwnd = FindWindow(None, sys.argv[2])
        if utils.hwnd:
            parse_profile(sys.argv[1])
            import google_sheets
            import state_machine
            if len(sys.argv) >= 4 and sys.argv[3 - len(sys.argv)] != '--stream':
                sheet_id = sys.argv[3 - len(sys.argv)]
            else:
                sheet_id = None
            global_.stream_mode = len(sys.argv) >= 4 and sys.argv[-1] == '--stream'
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
            log(f'Unable to find window \"{sys.argv[2]}\". Exiting...')
