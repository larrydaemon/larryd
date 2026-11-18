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


LANE = {'internal': {'locker': '{locker}',
                     'place_in_place': {'argv': ['python', '-B', 'runtime/app/web/app.py', 'place', '{key}', '{folder}', '--kits', '{folder}', '--slot', 'proof'],
                                        'cwd': '/scratch/runtime', 'env': {'LARRYD_INTERNAL': '1', 'LARRYD_LOCKER': '{locker}'}}},
        'frost': {'python': 'python', 'cwd': '/scratch/fs', 'env': {'WID_ENV': 'localhost.rnd'}}}
KEY = 'MAGT_0123456789AB_CDEF'


@pytest.fixture
def locker(tmp_path):
    return (tmp_path / 'locker').resolve()


@pytest.fixture(autouse=True)
def scratch_lane(tmp_path, locker, monkeypatch):
    locker.mkdir()
    conf = tmp_path / 'ship.json'
    conf.write_text(json.dumps(LANE).replace('{locker}', str(locker)))
    monkeypatch.setattr(ship, 'CONFIG', conf)


@pytest.fixture
def repo(tmp_path):
    work = tmp_path / 'work'   # the working folder (scrum_master_3/<name>), apart from the locker
    (work / '_office').mkdir(parents=True)
    (work / '_office' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    (work / '_office' / 'look.py').write_text('')
    make(work, 'scratch-agent')
    git_repo(work)
    return work


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
    assert 'in place: into' in said[5] and 'scratch-agent/agent' in said[5]
    assert all(c[0] == 'git' for c in out.calls)   # the plan reaches nothing


def test_go_places_in_the_locker_in_place_and_approves_the_exact_hashes(repo, locker, tmp_path):
    out = Outside()
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=out, say=say, scratch=tmp_path))
    assert code == 0, said
    home = locker / 'scratch-agent' / 'agent'
    place = next(c for c in out.calls if 'place' in c and 'runtime/app/web/app.py' in c)
    assert place[3:] == ['place', KEY, str(home), '--kits', str(home), '--slot', 'proof']   # the folder itself: no .larryd file
    assert sorted(p.name for p in home.iterdir()) == ['agent.json', 'agent.py', 'look.py', 'office.py']   # self-contained: its kits inside
    assert (home / 'office.py').read_text() == (repo / '_office' / 'office.py').read_text()
    assert not list(tmp_path.rglob('*.larryd'))
    approve = next(c for c in out.calls if ship.APPROVE in c)
    assert approve[-4:-1] == [KEY, 'c' * 64, 'm' * 64]
    assert f'held in {home}' in said[-2] and 'FROST review 7 approved' in said[-1]


def test_the_runtime_is_told_the_locker(repo, tmp_path):
    seen = []

    class Watch(Outside):
        def __call__(self, argv, cwd=None, env=None, timeout=900):
            if 'runtime/app/web/app.py' in argv:
                seen.append(env)
            return super().__call__(argv, cwd, env, timeout)
    assert ship.ship(repo / 'scratch-agent', go=True, run=Watch(), say=lambda s: None, scratch=tmp_path) == 0
    assert seen[0]['LARRYD_INTERNAL'] == '1' and seen[0]['LARRYD_LOCKER'] == str((tmp_path / 'locker').resolve())


def test_the_pack_is_the_agent_whole_with_its_kits(repo):
    files, _ = ship.pack(repo / 'scratch-agent', 'internal')
    assert sorted(files) == ['agent.json', 'agent.py', 'look.py', 'office.py']
    (repo / 'scratch-agent' / 'agent' / 'look.py').write_text('# its own look, inside agent/\n')   # a kit inside agent/ wins over _office's
    (repo / 'scratch-agent' / 'agent' / 'helper.py').write_text('x = 1\n')
    files, _ = ship.pack(repo / 'scratch-agent', 'internal')
    assert files['look.py'] == b'# its own look, inside agent/\n' and 'helper.py' in files


def test_shipped_again_the_locker_holds_exactly_the_new_pack(repo, locker, tmp_path):
    assert ship.ship(repo / 'scratch-agent', go=True, run=Outside(), say=lambda s: None, scratch=tmp_path) == 0
    home = locker / 'scratch-agent' / 'agent'
    (home / 'stale.py').write_text('# left from an older version\n')
    assert ship.ship(repo / 'scratch-agent', go=True, run=Outside(), say=lambda s: None, scratch=tmp_path) == 0
    assert not (home / 'stale.py').exists() and (home / 'agent.json').is_file()
    assert sorted(p.name for p in home.parent.iterdir()) == ['agent']   # no staging or old copy left beside it


def test_an_agent_worked_on_in_the_locker_only_gains_its_kits(tmp_path, locker):
    (locker / '_office').mkdir()
    (locker / '_office' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    (locker / '_office' / 'look.py').write_text('')
    root = make(locker, 'in-locker')
    git_repo(locker)
    out = Outside()
    assert ship.ship(root, go=True, run=out, say=lambda s: None, scratch=tmp_path) == 0
    assert sorted(p.name for p in (root / 'agent').iterdir()) == ['agent.json', 'agent.py', 'look.py', 'office.py']


def test_the_runtime_held_it_but_wid_did_not_take_it(repo, tmp_path):
    out = Outside(place={'code_sha256': 'c' * 64, 'manifest_sha256': 'm' * 64, 'refused': 'held in the locker, but wid did not take it: down'})
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=out, say=say, scratch=tmp_path))
    assert code == 1 and 'wid did not take it' in said[-1]
    assert not any(ship.APPROVE in c for c in out.calls)


def test_a_lane_with_no_internal_locker_says_so(repo, tmp_path, monkeypatch):
    conf = tmp_path / 'old_lane.json'
    conf.write_text(json.dumps({'internal': {'place': {'argv': ['x', '{pkg}']}}, 'frost': LANE['frost']}))
    monkeypatch.setattr(ship, 'CONFIG', conf)
    out = Outside()
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=out, say=say, scratch=tmp_path))
    assert code == 1 and 'names no internal locker' in said[-1]
    assert all(c[0] == 'git' for c in out.calls)


@pytest.mark.parametrize('environment, where', [('POSITIVE FEEDBACK (INTERNAL-ONLY)', 'internal'), ('POSITIVE FEEDBACK', 'external'), (None, 'internal')])
def test_the_tag_picks_the_road(repo, environment, where):
    from test_internal import CARD
    root = make(repo, 'tagged', {'card': {**CARD, **({'environment': environment} if environment else {})}})
    assert ship.target_of(root) == where   # an office agent with no tag: the old folder-shape rule, internal


def test_a_clean_project_tagged_internal_is_internal_without_a_reach_json(tmp_path):
    from test_internal import CARD
    plain = tmp_path / 'plain'
    plain.mkdir()
    root = make(plain, 'clean', {'office': None, 'libs': None, 'facts': None, 'key': None, 'workflow': None, 'group': None, 'reads': ['nothing'], 'records': {}})
    assert ship.target_of(root) == 'external'
    root = make(plain, 'clean-tagged', {'office': None, 'libs': None, 'facts': None, 'key': None, 'workflow': None, 'group': None, 'reads': ['nothing'], 'records': {},
                                        'card': {**CARD, 'environment': 'POSITIVE FEEDBACK (INTERNAL-ONLY)'}})
    assert ship.target_of(root) == 'internal'


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


def test_an_uncommitted_kit_is_never_placed_either(repo):
    (repo / '_office' / 'look.py').write_text('# changed\n')
    code, said = lines(lambda say: ship.ship(repo / 'scratch-agent', go=True, run=Outside(), say=say))
    assert code == 1 and 'a kit it is packed with holds uncommitted changes' in said[-1]



# ------------------------------------------------ 7 PLATFORMS, 8 CARD: every platform ready from one ship (the owner 2026-11-17)
PLATFORM = {'name': 'production B', 'slot': 'slot-b', 'submit': {'argv': ['submit', '{key}', '--slot', '{slot}']},
            'frost': {'remote': ['ssh-to-b', '--command'], 'python': '/b/python', 'cwd': '/b/fs', 'env': {'WID_ENV': 'frost-b.pf'}}}
HASHES = {'code_sha256': 'c' * 64, 'manifest_sha256': 'm' * 64}


class Lane:
    """the stand-in for the platform commands: what was run, and what each answers"""
    def __init__(self, card_json=None, approve=None):
        self.calls, self.card_json, self.written = [], card_json, None
        self.approve = approve or {'approved': True, 'review': 9, 'card_key': 'MAGT_BBBBBBBBBBBB_0002', 'state': 'approved'}

    def __call__(self, argv, cwd=None, env=None, timeout=900):
        self.calls.append(argv)
        if argv[0] == 'submit':
            return 0, '', ''
        if argv[0] == 'ssh-to-b':
            return 0, json.dumps(self.approve) + '\n', ''
        if argv[0] == 'read':
            return (0, json.dumps(self.card_json), '') if self.card_json is not None else (1, '', 'no such object')
        if argv[0] == 'write':
            self.written = json.loads(argv[1])
            return 0, '', ''
        raise AssertionError(f'an outside command the test did not expect: {argv[:3]}')


def with_lane(tmp_path, monkeypatch, **more):
    conf = tmp_path / 'ship_platforms.json'
    conf.write_text(json.dumps({**LANE, 'platforms': [PLATFORM],
                                'external': {'card_read': {'argv': ['read', '{key}']}, 'card': {'argv': ['write', '{card}']},
                                             'card_there': {'argv': ['read', '{key}']}}, **more}))
    monkeypatch.setattr(ship, 'CONFIG', conf)


def test_each_platform_is_submitted_to_its_slot_and_approved_in_its_own_frost(tmp_path, monkeypatch):
    with_lane(tmp_path, monkeypatch)
    run = Lane()
    assert ship.platforms(KEY, HASHES, 'a note', run, say=lambda s: None) == {'slot-b': 'MAGT_BBBBBBBBBBBB_0002'}
    assert run.calls[0] == ['submit', KEY, '--slot', 'slot-b']
    remote = run.calls[1]
    assert remote[:2] == ['ssh-to-b', '--command'] and len(remote) == 3   # the whole line is the last word, as gcloud compute ssh --command takes it
    assert remote[2].startswith('cd /b/fs && env WID_ENV=frost-b.pf /b/python -B -c ')
    assert KEY in remote[2] and 'c' * 64 in remote[2] and "'a note'" in remote[2]


def test_a_platform_that_will_not_approve_stops_the_ship(tmp_path, monkeypatch):
    with_lane(tmp_path, monkeypatch)
    with pytest.raises(ship.Stop, match='not approved'):
        ship.platforms(KEY, HASHES, 'n', Lane(approve={'approved': False, 'why': '0 waiting reviews'}), say=lambda s: None)


def test_card_json_keeps_what_it_held_and_gains_every_platforms_card(tmp_path, monkeypatch):
    with_lane(tmp_path, monkeypatch)
    run = Lane(card_json={'card_key': 'MAGT_OLD000000000_0000', 'cards': {'proof': 'MAGT_AAAAAAAAAAAA_0001'}})
    said = ship.card(KEY, 'MAGT_AAAAAAAAAAAA_0001', run, {'proof': 'MAGT_AAAAAAAAAAAA_0001', 'slot-b': 'MAGT_BBBBBBBBBBBB_0002'})
    assert run.written == {'card_key': 'MAGT_OLD000000000_0000', 'cards': {'proof': 'MAGT_AAAAAAAAAAAA_0001', 'slot-b': 'MAGT_BBBBBBBBBBBB_0002'}}
    assert said == 'card.json names proof, slot-b'


def test_card_json_already_naming_every_platform_is_not_written_again(tmp_path, monkeypatch):
    with_lane(tmp_path, monkeypatch)
    cards = {'proof': 'MAGT_AAAAAAAAAAAA_0001', 'slot-b': 'MAGT_BBBBBBBBBBBB_0002'}
    run = Lane(card_json={'card_key': 'MAGT_AAAAAAAAAAAA_0001', 'cards': cards})
    assert ship.card(KEY, 'MAGT_AAAAAAAAAAAA_0001', run, cards) == 'card.json already names every platform'
    assert run.written is None


def test_a_new_agent_gets_card_json_with_every_platform(tmp_path, monkeypatch):
    with_lane(tmp_path, monkeypatch)
    run = Lane()
    ship.card(KEY, 'MAGT_AAAAAAAAAAAA_0001', run, {'proof': 'MAGT_AAAAAAAAAAAA_0001', 'slot-b': 'MAGT_BBBBBBBBBBBB_0002'})
    assert run.written == {'card_key': 'MAGT_AAAAAAAAAAAA_0001', 'cards': {'proof': 'MAGT_AAAAAAAAAAAA_0001', 'slot-b': 'MAGT_BBBBBBBBBBBB_0002'}}


def test_a_lane_with_no_platforms_ships_as_before(tmp_path, monkeypatch):
    run = Lane()
    assert ship.platforms(KEY, HASHES, 'n', run, say=lambda s: None) == {}
    assert run.calls == []
