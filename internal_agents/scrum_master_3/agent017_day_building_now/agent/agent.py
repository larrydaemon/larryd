"""BUILDING NOW (agent017_day_building_now.py of Scrum Master 3), moved into LARRYD RUNTIME INTERNAL 2026-11-03: its program and every office
module it imports are in scrum_master_3/app beside this file; larryd_main draws its canvas (CALL) and runs it (RUN) as the office did."""
import larryd_main

AGENT_FILE = 'agent017_day_building_now.py'
CHAIN = ['agent016_day_the_requests.py', 'agent017_day_building_now.py', 'agent018_day_main_first.py', 'agent019_day_pick.py', 'agent020_day_build.py', 'agent021_day_prove.py', 'agent022_day_review.py', 'agent023_day_commit.py', 'agent024_day_hot_fix_walk.py', 'agent025_day_cleanup.py']   # THE HAND-OFF: the DAY steps after it, carried in this folder; its run drives them in this one process as the office's loop did

if __name__ == '__main__':
    larryd_main.main(AGENT_FILE, CHAIN)
