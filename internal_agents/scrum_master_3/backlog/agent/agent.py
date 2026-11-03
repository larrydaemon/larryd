"""SCRUM MASTER 3 · BACKLOG: the office's agent026_day_backlog.py (moved whole into scrum_master_3/app/agent/), run in LARRYD RUNTIME INTERNAL.
A CALL draws its canvas as the office's /internal/view drew it; a RUN runs the office's own run() (sm3_internal.py)."""
import sm3_internal

FILE = 'agent026_day_backlog.py'   # its program
CHAIN = ['agent026_day_backlog.py']   # itself


def canvas():
    sm3_internal.main(FILE, CHAIN)


def run():
    sm3_internal.main(FILE, CHAIN)


if __name__ == '__main__':
    sm3_internal.main(FILE, CHAIN)
