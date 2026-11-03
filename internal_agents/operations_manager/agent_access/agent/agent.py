"""Agent Access (the Operations Manager office's agent003_top_agent_access.py), moved into LARRYD RUNTIME INTERNAL (2026-11-03). The office's own code is in
operations_manager/app (its programs, its page, its frame); office.py draws this agent's canvas (a CALL) and runs its program (a RUN)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import office  # noqa: E402

if __name__ == '__main__':
    office.main('agent003_top_agent_access.py')
