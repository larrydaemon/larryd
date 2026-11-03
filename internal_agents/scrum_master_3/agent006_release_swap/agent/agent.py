"""THE SWAP (agent006_release_swap.py of Scrum Master 3), moved into LARRYD RUNTIME INTERNAL 2026-11-03: its program and every office
module it imports are in scrum_master_3/app beside this file; larryd_main draws its canvas (CALL) and runs it (RUN) as the office did."""
import larryd_main

AGENT_FILE = 'agent006_release_swap.py'
CHAIN = ['agent002_release_freeze.py', 'agent003_release_sync.py', 'agent004_release_test.py', 'agent005_release_memory.py', 'agent006_release_swap.py', 'agent007_release_backup.py', 'agent018_day_main_first.py', 'agent019_day_pick.py', 'agent020_day_build.py', 'agent021_day_prove.py', 'agent022_day_review.py', 'agent023_day_commit.py', 'agent024_day_hot_fix_walk.py', 'agent025_day_cleanup.py']   # THE HAND-OFF: the RELEASE steps, and the DAY its red is healed through (Pick), carried in this folder; its run drives them in this one process as the office's loop did

if __name__ == '__main__':
    larryd_main.main(AGENT_FILE, CHAIN)
