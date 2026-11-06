"""`larryd ship` (CORE_CLEANUP_IV 55, 98): ONE place-and-approve command, the same steps internal and external, only the target differs.
Every outside step is a stand-in here (the runtime, FROST, the bucket): nothing is placed, approved or written for real."""
import json
import subprocess

import pytest

from larryd import ship
from test_internal import make


def git_repo(path):
    subprocess.run(['git', '-C', str(path), 'init', '-q'], check=True)
    subprocess.run(['git', '-C', str(path), '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(path), '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'scratch'], check=True)


LANE = {'internal': {'place': {'argv': ['python', '-B', 'runtime/app/web/app.py', 'place', '{key}', '{pkg}', '--slot', 'proof'], 'cwd': '/scratch/runtime'}},
        'frost': {'python': 'python', 'cwd': '/scratch/fs', 'env': {'WID_ENV': 'localhost.rnd'}}}


@pytest.fixture(autouse=True)
def scratch_lane(tmp_path, monkeypatch):
    conf = tmp_path / 'ship.json'
    conf.write_text(json.dumps(LANE))
    monkeypatch.setattr(ship, 'CONFIG', conf)


@pytest.fixture
def repo(tmp_path):
    (tmp_path / '_office').mkdir()
    (tmp_path / '_office' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    (tmp_path / '_office' / 'look.py').write_text('')
    make(tmp_path, 'scratch-agent')
    git_repo(tmp_path)
    return tmp_path


class Outside:
    """the stand-in for every outside command: git is real, the runtime and FROST answer as told"""
    def __init__(self, place=None, approve=None):
        self.calls, self.place, self.approve = [], place, approve

    def __call__(self, argv, cwd=None, env=None, timeout=900):
        self.calls.append(argv)
        if argv[0] == 'git':
            got = subprocess.run(argv, capture_output=True, text=True)
            return got.returncode, got.stdout, got.stderr
        if 'place' in argv and 'runtime/app/web/app.py' in argv:
            return 0, json.dumps(self.place or {'code_sha256': 'c' * 64, 'manifest_sha256': 'm' * 64}) + '\n', ''
        if '-c' in argv and ship.APPROVE in argv:
            return 0, json.dumps(self.approve or {'approved': True, 'review': 7, 'card_key': 'MAGT_AAAAAAAAAAAA_0001', 'state': 'approved'}) + '\n', ''
        raise AssertionError(f'an outside command the test did not expect: {argv[:3]}')


def lines(fn):
    said = []
    code = fn(said.append)
    return code, said


def test_the_plan_places_nothing(repo):
    out = Outside()
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', run=out, say=say))
    assert code == 0
    assert [s.split()[0] for s in said[1:]] == ['1', '2', '3', '4', '5', '6']
    assert 'INTERNAL' in said[0] and 'MAGT_0123456789AB_CDEF' in said[4]
    assert all(c[0] == 'git' for c in out.calls)   # the plan reaches nothing


def test_go_places_in_the_internal_runtime_and_approves_the_exact_hashes(repo, tmp_path):
    out = Outside()
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=out, say=say, scratch=tmp_path))
    assert code == 0, said
    place = next(c for c in out.calls if 'place' in c and 'runtime/app/web/app.py' in c)
    assert place[3:5] == ['place', 'MAGT_0123456789AB_CDEF'] and place[-2:] == ['--slot', 'proof'] and place[5].endswith('MAGT_0123456789AB_CDEF.larryd')
    approve = next(c for c in out.calls if ship.APPROVE in c)
    assert approve[-4:-1] == ['MAGT_0123456789AB_CDEF', 'c' * 64, 'm' * 64]
    assert 'FROST review 7 approved' in said[-1]


def test_the_pack_is_what_place_sh_packed(repo):
    import io
    import zipfile
    data, _ = ship.pack(repo / 'scratch-agent')
    assert sorted(zipfile.ZipFile(io.BytesIO(data)).namelist()) == ['agent.json', 'agent.py', 'look.py', 'office.py']


def test_uncommitted_work_is_never_placed(repo):
    (repo / 'scratch-agent' / 'agent' / 'agent.py').write_text('# changed\n')
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=Outside(), say=say))
    assert code == 1 and 'uncommitted' in said[-1]


def test_a_doctor_problem_stops_it_before_anything_is_placed(repo):
    make(repo, 'faulty', {'key': 'bad'})
    git_repo(repo)
    out = Outside()
    code, said = lines(lambda say: ship.ship(repo / 'faulty', go=True, run=out, say=say))
    assert code == 1 and 'the doctor --internal found' in said[-1]
    assert all(c[0] == 'git' for c in out.calls)


def test_not_exactly_one_waiting_review_is_never_approved(repo, tmp_path):
    out = Outside(approve={'approved': False, 'why': '2 waiting reviews of exactly this key and these hashes, not one'})
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=out, say=say, scratch=tmp_path))
    assert code == 1 and 'not approved: 2 waiting reviews' in said[-1]


def test_an_internal_clean_project_is_placed_under_its_place_json_key(repo):
    make(repo, 'clean', {'office': None, 'libs': None, 'facts': None, 'key': None, 'workflow': None, 'group': None, 'reads': ['nothing'], 'records': {}})
    (repo / 'clean' / 'place.json').write_text(json.dumps({'key': 'MAGT_BBBBBBBBBBBB_0002'}))
    (repo / 'reach.json').write_text('{}')
    assert ship.key_of(repo / 'clean', json.loads((repo / 'clean' / 'agent' / 'agent.json').read_text()), 'internal') == 'MAGT_BBBBBBBBBBBB_0002'
    (repo / 'clean' / 'place.json').unlink()
    with pytest.raises(ship.Stop):
        ship.key_of(repo / 'clean', {}, 'internal')


def test_without_a_lane_it_says_so_and_places_nothing(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(ship, 'CONFIG', tmp_path / 'none.json')
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=Outside(), say=say, scratch=tmp_path))
    assert code == 1 and 'not a ship lane' in said[-1]
