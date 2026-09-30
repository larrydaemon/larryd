"""{name}: what it answers, in one plain sentence (change this line to say it).
LARRYD runs this file as its own process: one JSON object comes in on stdin, one JSON object goes out on stdout.
It has no network and no files outside its own run; everything it needs is handed to it in the job."""
import json
import sys


def answer(job):
    """Answer one job. `job` is what LARRYD hands a RUN: {{"do": "answer", ...the inputs in agent.json run.hands}}.
    Return one dict; its "delivery" is what lands in the member's job."""
    return {{'delivery': '{name} answered the job.'}}


def main():
    job = json.load(sys.stdin)
    do = {{'answer': answer}}.get(job.get('do'))
    if do is None:
        raise SystemExit('this agent does: answer')
    print(json.dumps(do(job)))


if __name__ == '__main__':
    main()
