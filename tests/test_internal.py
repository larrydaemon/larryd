"""`larryd doctor --internal` (CORE_CLEANUP_IV 55, 98; the owner: "we want them to work the same internal and external"): an internal
agent is checked for the same things as an external one, by the internal contract's three rules. Scratch repositories only."""
import json

import pytest

from larryd import cli, internal

DAM = '1d0eb4d13f8a91b4d0cc67f8b5cb157a4b74ec2c937779d49d4bb80beecc670a'
CARD = {'class': 'MARK I AGENT (NORMAL)', 'pitch': 'A scratch internal agent', 'price': '0', 'type': 'DEVELOPER', 'residency': 'INTERNAL',
        'authorization': 'PRIVATE', 'screen': 'larryd/jobs/home', 'product': 'LARRYD', 'module': 'Jobs', 'developer': 'LARRYD', 'sends_to': '', 'data_sent': ''}
CODE = '''"""a scratch office agent"""
import office


def canvas(given):
    return office.view(office.said('hello'))


def run(given):
    return office.done('GREEN · ok')


if __name__ == '__main__':
    office.main(canvas, run)
'''


@pytest.fixture
def repo(tmp_path):
    """a scratch internal repository: _office (the office library and a kit), and one office agent"""
    (tmp_path / '_office').mkdir()
    (tmp_path / '_office' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    (tmp_path / '_office' / 'look.py').write_text('')
    make(tmp_path, 'scratch-agent')
    return tmp_path


def make(repo, name, card=None, code=CODE):
    agent = repo / name / 'agent'
    agent.mkdir(parents=True)
    manifest = {'key': 'MAGT_0123456789AB_CDEF', 'name': 'Scratch Agent', 'office': 'operations_manager', 'workflow': '', 'group': 'LIVE',
                'entry': 'agent.py', 'libs': ['look'], 'about': 'A scratch internal agent for the internal doctor\'s tests.',
                'does': ['canvas', 'run'], 'calls': ['canvas'], 'records': {'agnt': ['read'], 'jobs': ['read']},
                'run': {'do': 'run', 'hands': []}, 'gives': ['view', 'delivery', 'light', 'job'], 'skills': [], 'knowledge': [],
                'facts': {'most': 3}, 'card': CARD, 'internal': {'seconds': 60}}
    manifest.update(card or {})
    for k, v in list(manifest.items()):
        if v is None:
            manifest.pop(k)
    (agent / 'agent.json').write_text(json.dumps(manifest))
    (agent / 'agent.py').write_text(code)
    return repo / name


def failed(root):
    return {(p.check, p.wrong) for p in internal.check(root)}


def test_an_office_agent_on_the_jobs_page_with_larryds_own_records_passes(repo):
    assert internal.check(repo / 'scratch-agent') == []


def test_the_external_doctor_refuses_it_and_the_internal_mode_says_why_not(repo):
    from larryd import doctor
    assert doctor.check(repo / 'scratch-agent') != []   # the external contract: unchanged


@pytest.mark.parametrize('change, wrong', [
    ({'key': 'agent-1'}, '"key" is not its runtime key'),
    ({'office': 'kitchen'}, '"office" is \'kitchen\''),
    ({'libs': ['night']}, '"libs" names night'),
    ({'internal': {'seconds': 999999}}, '"internal" is not'),
    ({'records': {'zzzz': ['read']}}, '"records" is not {species: [verbs]}'),
    ({'card': {**CARD, 'screen': 'nowhere/home'}}, 'not a screen of the platform'),
    ({'does': ['canvas', 'run', 'missing']}, 'no function missing'),
])
def test_each_internal_rule_names_its_fault(repo, change, wrong):
    root = make(repo, 'faulty', change)
    assert any(wrong in w for _, w in failed(root)), failed(root)


def test_an_agent_that_names_no_office_carries_no_office_fields(repo):
    root = make(repo, 'clean', {'office': None, 'libs': None, 'facts': None, 'key': None, 'workflow': None, 'group': None,
                                'reads': ['nothing'], 'records': {}}, code='"""a clean project"""\nimport json\n\n\ndef canvas(job):\n    return {}\n\n\ndef run(job):\n    return {}\n\n\nif __name__ == "__main__":\n    print(json.dumps({}))\n')
    assert internal.check(root) == []   # its time limit ("internal") is any internal agent's
    root = make(repo, 'clean-with-key', {'office': None, 'libs': None, 'reads': ['nothing']})
    assert any('belongs to an office agent' in w for _, w in failed(root))


def test_an_entry_handed_to_its_kits_main_answers_canvas_and_run(repo):
    code = '"""a night step"""\nimport office\nimport night\n\n\ndef work(given):\n    return {}\n\n\nif __name__ == "__main__":\n    night.main(work=work)\n'
    (repo / '_office' / 'night.py').write_text('')
    assert internal.check(make(repo, 'night-step', {'libs': ['night']}, code=code)) == []
    assert any('no function canvas' in w for _, w in failed(make(repo, 'not-handed', {'libs': []}, code='import office\n\n\ndef work(given):\n    return {}\n\n\nif __name__ == "__main__":\n    work({})\n')))


def test_a_reach_off_this_mac_fails_unless_reach_json_says_why(repo):
    code = CODE.replace('import office\n', 'import office\nimport urllib.request\n')
    root = make(repo, 'reacher', code=code)
    assert any(c == 'no reach outside this Mac' and 'by itself' in w for c, w in failed(root))
    (repo / 'reach.json').write_text(json.dumps({'reacher': 'its own VM over ssh, until the owner says otherwise (IV 92)'}))
    assert not any('by itself' in w for _, w in failed(root))


def test_an_import_must_be_the_standard_library_its_own_a_named_kit_or_the_runtimes(repo, tmp_path, monkeypatch):
    runtime = tmp_path / 'runtime'
    (runtime / '.venv' / 'lib' / 'python3.14' / 'site-packages' / 'flaskish').mkdir(parents=True)
    monkeypatch.setenv('LARRYD_INTERNAL_RUNTIME', str(runtime))
    ok = make(repo, 'importer', code=CODE.replace('import office\n', 'import office\nimport look\nimport flaskish\nfrom helper import x\n'))
    (ok / 'agent' / 'helper.py').write_text('x = 1\n')
    assert internal.check(ok) == []
    bad = make(repo, 'stranger', code=CODE.replace('import office\n', 'import office\nimport numpy\n'))
    assert any('it imports numpy' in w for _, w in failed(bad))


def test_the_cli_runs_the_internal_mode(repo, capsys):
    assert cli.main(['doctor', '--internal', str(repo / 'scratch-agent')]) == 0
    assert 'larryd doctor --internal:' in capsys.readouterr().out
    make(repo, 'bad', {'key': 'x'})
    assert cli.main(['doctor', '--internal', str(repo / 'bad')]) == 1


@pytest.mark.parametrize('every', [['reviews'], ['count', 'roster'], ['count']])
def test_star_takes_what_the_shape_lets_it_hold_each_once(repo, every):
    assert internal.check(make(repo, 'star-' + '-'.join(every), {'records': {'*': every}})) == []


def test_star_refuses_anything_else_or_twice(repo):
    for bad in (['count', 'count'], ['everything'], []):
        assert any('"records" is not' in w for _, w in failed(make(repo, 'bad-star-' + str(len(bad)) + ''.join(bad), {'records': {'*': bad}})))


def test_the_service_key_hand_needs_a_service_named_first(repo):
    card = {**CARD, 'sends_to': 'monday.com (monday.com Ltd.)', 'data_sent': 'the board ids'}
    ok = make(repo, 'connector', {'run': {'do': 'run', 'hands': ['job', 'service_key']}, 'inputs': {'boards': '001'}, 'card': card})
    assert internal.check(ok) == []
    bad = make(repo, 'connector-unnamed', {'run': {'do': 'run', 'hands': ['job', 'service_key']}, 'inputs': {'boards': '001'}})
    assert any('names no service' in w for _, w in failed(bad))



def test_kits_inside_its_own_agent_folder_need_no_office_beside_it(tmp_path):
    """the locker made agents self-contained (<repo>/<name>/agent/office.py ...): no _office in the repository at all"""
    root = make(tmp_path, 'self-contained')
    (root / 'agent' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    (root / 'agent' / 'look.py').write_text('')
    assert internal.check(root) == []
    (root / 'agent' / 'look.py').unlink()
    assert any('"libs" names look, but look.py is neither in its agent/ nor' in w for _, w in failed(root))
    (root / 'agent' / 'office.py').unlink()
    assert any('it has no office.py' in w for _, w in failed(root))


def test_a_kit_inside_agent_is_checked_as_its_own_code(tmp_path):
    root = make(tmp_path, 'kit-reaches')
    (root / 'agent' / 'office.py').write_text('def main(canvas, run=None):\n    import numpy\n')
    (root / 'agent' / 'look.py').write_text('')
    assert any('it imports numpy' in w for _, w in failed(root))


SELF_PATH = 'import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n'


def test_an_entry_importing_a_sibling_is_told_the_one_line_production_needs(repo):
    """production runs every agent with python -I: its own folder is not on sys.path, so `import office` fails there"""
    root = make(repo, 'no-path-line')
    (root / 'agent' / 'office.py').write_text('def main(canvas, run=None):\n    pass\n')
    warns = internal.warnings(root)
    assert len(warns) == 1 and warns[0].line == 2 and 'it imports office, a file beside it' in warns[0].wrong
    assert warns[0].todo.endswith(SELF_PATH.strip())
    assert internal.check(root) == []   # said, not failed, for now


@pytest.mark.parametrize('top, ok', [
    (SELF_PATH, True),
    ('import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))\n', True),
    ('import os, sys\nHERE = os.path.dirname(os.path.abspath(__file__))\nif HERE not in sys.path:\n    sys.path.insert(0, HERE)\n', True),
    ('import sys\nsys.path.insert(0, "lib")\n', False),          # not its own folder
    ('import os, sys\nsys.path.append(os.path.dirname(__file__))\n', False),   # last, not first
])
def test_the_line_before_its_first_sibling_import(repo, top, ok):
    root = make(repo, 'p' + str(abs(hash(top)))[:8], code='"""doc"""\n' + top + CODE.split('"""\n', 1)[1])
    assert (internal.warnings(root) == []) is ok, internal.warnings(root)


def test_the_line_after_the_import_is_too_late_and_no_sibling_needs_none(repo):
    late = make(repo, 'late', code=CODE.replace('import office\n', 'import office\n' + SELF_PATH))
    assert 'its line comes after' in internal.warnings(late)[0].wrong
    alone = make(repo, 'alone', {'office': None, 'libs': None, 'facts': None, 'key': None, 'workflow': None, 'group': None, 'reads': ['nothing'], 'records': {}},
                 code='"""a clean project"""\nimport json\n\n\ndef canvas(job):\n    return {}\n\n\ndef run(job):\n    return {}\n\n\nif __name__ == "__main__":\n    print(json.dumps({}))\n')
    assert internal.warnings(alone) == []


def test_the_external_doctor_takes_the_line_too(tmp_path, monkeypatch):
    from larryd import doctor, new
    monkeypatch.chdir(tmp_path)
    root = new.make('pathline')
    entry = root / 'agent' / 'agent.py'
    entry.write_text('"""doc"""\n' + SELF_PATH + entry.read_text().split('"""', 2)[2])
    assert doctor.check(root) == [], [p.text() for p in doctor.check(root)]


@pytest.mark.parametrize('value, ok', [('POSITIVE FEEDBACK (INTERNAL-ONLY)', True), ('POSITIVE FEEDBACK', True), ('somewhere', False), (3, False)])
def test_the_tag_is_one_the_platform_knows(repo, value, ok):
    root = make(repo, 'env-' + str(abs(hash(str(value))))[:8], {'card': {**CARD, 'environment': value}})
    assert (not any('card "environment" is' in w for _, w in failed(root))) is ok


def test_the_cli_picks_the_mode_from_the_tag(repo, capsys):
    tagged = make(repo, 'tagged-internal', {'card': {**CARD, 'environment': 'POSITIVE FEEDBACK (INTERNAL-ONLY)'}})
    assert cli.main(['doctor', str(tagged)]) == 0 and 'larryd doctor --internal:' in capsys.readouterr().out   # no --internal needed
    external = make(repo, 'tagged-external', {'card': {**CARD, 'environment': 'POSITIVE FEEDBACK'}})
    assert cli.main(['doctor', '--internal', str(external)]) == 2 and 'EXTERNAL' in capsys.readouterr().err
    assert cli.main(['doctor', str(external)]) == 1 and 'larryd doctor:' in capsys.readouterr().out   # the external contract refuses an office agent
    assert cli.main(['doctor', str(repo / 'scratch-agent')]) == 0   # no tag: the folder's shape (an office agent) says internal


def test_the_cli_says_the_warning_and_its_json_carries_it(repo, capsys):
    assert cli.main(['doctor', '--internal', str(repo / 'scratch-agent')]) == 0
    assert 'WARN its own folder first on sys.path' in capsys.readouterr().out
    assert cli.main(['doctor', '--internal', '--json', str(repo / 'scratch-agent')]) == 0
    got = json.loads(capsys.readouterr().out)
    assert got['ok'] and got['warnings'][0]['check'] == 'its own folder first on sys.path'
