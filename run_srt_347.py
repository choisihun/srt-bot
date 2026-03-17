import time
import keyring
from srtgo.srt import SRT, SeatType, SRTError, SRTNetFunnelError

DATE = '20260318'
TIME = '155600'
DEP = '수서'
ARR = '동대구'
TARGET_TRAIN = '347'
INTERVAL = 0.7


def login():
    uid = keyring.get_password('SRT', 'id') or '2391153851'
    pw = keyring.get_password('SRT', 'pass') or 'bksa2354!@#$'
    return SRT(uid, pw, verbose=False)


def main():
    rail = login()
    tries = 0
    while True:
        tries += 1
        try:
            trains = rail.search_train(dep=DEP, arr=ARR, date=DATE, time=TIME, available_only=False)
            target = None
            for t in trains:
                if getattr(t, 'train_number', None) == TARGET_TRAIN:
                    target = t
                    break

            if target is None:
                print(f'[{tries}] train-not-found', flush=True)
                time.sleep(INTERVAL)
                continue

            general = target.general_seat_available()
            special = target.special_seat_available()
            print(f'[{tries}] general={target.general_seat_state} special={target.special_seat_state}', flush=True)

            if general:
                res = rail.reserve(target, option=SeatType.GENERAL_ONLY)
                print('RESERVED', res, flush=True)
                return

            time.sleep(INTERVAL)

        except SRTError as ex:
            msg = getattr(ex, 'msg', str(ex))
            print(f'[{tries}] SRTError: {msg}', flush=True)
            if '로그인 후 사용하십시오' in msg:
                rail = login()
            elif '정상적인 경로로 접근 부탁드립니다' in msg or isinstance(ex, SRTNetFunnelError):
                try:
                    rail.clear()
                except Exception:
                    pass
            time.sleep(INTERVAL)
        except Exception as ex:
            print(f'[{tries}] Error: {ex}', flush=True)
            time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
