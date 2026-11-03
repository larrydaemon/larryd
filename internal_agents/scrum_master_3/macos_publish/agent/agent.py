"""SCRUM MASTER 3 · MACOS PUBLISH: the office's agent035_night_macos_publish.py (moved whole into scrum_master_3/app/agent/), run in LARRYD RUNTIME INTERNAL.
A CALL draws its canvas as the office's /internal/view drew it; a RUN runs the office's own run() and the steps of its chain after it (sm3_internal.py)."""
import sm3_internal

FILE = 'agent035_night_macos_publish.py'   # its program
CHAIN = ['agent027_night_web_take_in.py', 'agent028_night_web_build.py', 'agent029_night_web_publish.py', 'agent030_night_iphone_take_in.py', 'agent031_night_iphone_build.py', 'agent032_night_iphone_publish.py', 'agent033_night_macos_take_in.py', 'agent034_night_macos_build.py', 'agent035_night_macos_publish.py', 'agent002_release_freeze.py', 'agent003_release_sync.py', 'agent004_release_test.py', 'agent005_release_memory.py', 'agent006_release_swap.py', 'agent007_release_backup.py', 'agent018_day_main_first.py', 'agent019_day_pick.py', 'agent020_day_build.py', 'agent021_day_prove.py', 'agent022_day_review.py', 'agent023_day_commit.py', 'agent024_day_hot_fix_walk.py', 'agent025_day_cleanup.py']   # THE HAND-OFF (2026-11-03): from the freeze (November 15) macOS publish hands the RELEASE on (Freeze), whose red heals through the DAY (Pick): both carried here


def canvas():
    sm3_internal.main(FILE, CHAIN)


def run():
    sm3_internal.main(FILE, CHAIN)


if __name__ == '__main__':
    sm3_internal.main(FILE, CHAIN)
