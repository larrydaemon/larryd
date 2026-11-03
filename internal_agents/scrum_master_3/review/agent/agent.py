"""SCRUM MASTER 3 · REVIEW: the office's agent022_day_review.py (moved whole into scrum_master_3/app/agent/), run in LARRYD RUNTIME INTERNAL.
A CALL draws its canvas as the office's /internal/view drew it; a RUN runs the office's own run() and the steps of its chain after it (sm3_internal.py)."""
import sm3_internal

FILE = 'agent022_day_review.py'   # its program
CHAIN = ['agent018_day_main_first.py', 'agent019_day_pick.py', 'agent020_day_build.py', 'agent021_day_prove.py', 'agent022_day_review.py', 'agent023_day_commit.py', 'agent024_day_hot_fix_walk.py', 'agent025_day_cleanup.py']   # the steps of its chain, the office own loop runs each next one


def canvas():
    sm3_internal.main(FILE, CHAIN)


def run():
    sm3_internal.main(FILE, CHAIN)


if __name__ == '__main__':
    sm3_internal.main(FILE, CHAIN)
