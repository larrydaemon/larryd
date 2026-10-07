"""THE CARD IN THE SHAPE: a new project carries its card and passes the doctor; the doctor refuses a card the marketplace
could not show, in the gate's own words; place and card talk only to this computer's LARRYD and say what to do when
none answers."""
import json
import pathlib
import re

import pytest

from larryd import cli, doctor, new, place, shape


def _manifest(root):
    path = root / shape.AGENT / shape.MANIFEST
    return path, json.loads(path.read_text())


def _with_card(tmp_path, name, change):
    root = new.make(name, tmp_path)
    path, manifest = _manifest(root)
    card = dict(manifest['card'])
    card.update(change)
    manifest['card'] = card
    path.write_text(json.dumps(manifest, indent=2))
    return root


def test_a_new_project_carries_a_card_the_doctor_accepts(tmp_path):
    root = new.make('carded', tmp_path)
    assert doctor.check(root) == []
    _, manifest = _manifest(root)
    assert set(manifest['card']) == set(shape.CARD)
    assert manifest['card']['price'] == '0' and re.fullmatch(shape.SCREEN, manifest['card']['screen'])


def test_the_card_is_a_field_the_kit_explains(tmp_path):
    root = new.make('explained', tmp_path)
    text = (root / 'CLAUDE.md').read_text()
    assert '`card`' in text and 'larryd card' in text and 'larryd place' in text


@pytest.mark.parametrize('change, wrong', [
    ({'price': '1.5'}, 'not a whole mTok rate'),
    ({'price': 3.5}, 'not a whole mTok rate'),
    ({'price': 'free'}, 'not a whole mTok rate'),
    ({'price': -1}, 'not a whole mTok rate'),
    ({'price': True}, 'not a whole mTok rate'),
    ({'screen': ''}, 'not a screen of the platform'),
    ({'screen': 'contacts'}, 'not a screen of the platform'),
    ({'screen': 'zzzz/card'}, 'not a screen of the platform'),
    ({'screen': 'app/cont/card'}, "the screen's address"),
    ({'screen': 'invc/card'}, 'is a INVOICE MAPS screen, but "product" is'),
    ({'class': 'MARK IV'}, 'card "class" is "MARK IV", not one the platform knows'),
    ({'type': 'CUSTOM'}, 'card "type" is "CUSTOM", not one the platform knows'),
    ({'residency': 'PRIVATE'}, 'card "residency" is "PRIVATE", not one the platform knows'),
    ({'product': 'Widgets'}, 'card "product" is "Widgets", not one the platform knows'),
    ({'pitch': ''}, '"pitch" is empty'),
    ({'developer': '   '}, '"developer" is empty'),
    ({'pitch': 'x' * (shape.MOST_PITCH + 1)}, 'longer than'),
    ({'extra': 'x'}, '"extra" is not a card field'),
])
def test_the_doctor_refuses_a_card_the_marketplace_could_not_show(tmp_path, change, wrong):
    root = _with_card(tmp_path, 'c' + re.sub(r'[^a-z0-9]', '', str(sorted(change))[:20]), change)
    problems = [p for p in doctor.check(root) if p.check == 'the manifest']
    assert problems, change
    assert any(wrong in p.wrong for p in problems), [p.wrong for p in problems]
    assert all(p.todo for p in problems)


def test_a_missing_card_is_one_problem_that_says_how_to_add_it(tmp_path):
    root = new.make('bare', tmp_path)
    path, manifest = _manifest(root)
    del manifest['card']
    path.write_text(json.dumps(manifest))
    problems = [p for p in doctor.check(root) if 'card' in p.wrong]
    assert len(problems) == 1 and '"card" is missing' in problems[0].wrong and 'add "card"' in problems[0].todo


def test_a_card_that_sends_data_out_names_what(tmp_path):
    root = _with_card(tmp_path, 'teller', {'sends_to': 'An outside model', 'data_sent': ''})
    problems = [p for p in doctor.check(root) if p.check == 'the manifest']
    assert problems and 'data_sent' in problems[0].wrong
    root = _with_card(tmp_path, 'teller2', {'sends_to': 'An outside model', 'data_sent': 'the city'})
    assert doctor.check(root) == []


def test_a_card_key_is_a_card_key_made_from_the_name():
    key = place.key_for('Weather')
    assert re.fullmatch(r'DAGT_[0-9A-F]{12}_[0-9A-F]{4}', key)
    assert key == place.key_for('Weather') and key != place.key_for('Weather 2')


def test_place_says_to_start_larryd_when_none_answers(tmp_path, monkeypatch):
    monkeypatch.setenv('LARRYD_PORT', '1')   # nothing listens on port 1
    root = new.make('lonely', tmp_path)
    with pytest.raises(place.Refused) as no:
        place.place(root)
    assert 'no LARRYD runtime answers' in no.value.wrong and 'run `larryd`' in no.value.todo


def test_place_refuses_before_sending_when_the_doctor_finds_problems(tmp_path, monkeypatch):
    monkeypatch.setenv('LARRYD_PORT', '1')
    root = _with_card(tmp_path, 'broken', {'price': 'lots'})
    with pytest.raises(place.Refused) as no:
        place.place(root)
    assert 'the doctor found problems' in no.value.wrong and no.value.more['problems']


def test_the_cli_knows_place_and_card():
    p = cli.parser()
    assert p.parse_args(['place']).command == 'place'
    args = p.parse_args(['card', 'somewhere', '--no-browser', '--json'])
    assert (args.command, args.path, args.no_browser, args.json) == ('card', 'somewhere', True, True)


@pytest.mark.parametrize('price', [3, '3', 0, '0'])
def test_a_whole_price_is_a_number_or_its_text(tmp_path, price):
    assert doctor.check(_with_card(tmp_path, f'p{price!r}'.replace("'", 'q'), {'price': price})) == []


def test_a_card_failure_is_always_named_and_counted(tmp_path, capsys):
    """frost-92's second agent: price "3.5" printed all 8 checks PASS, then "1 of 8 checks failed"; --json named none."""
    from larryd import cli
    root = _with_card(tmp_path, 'half', {'price': '3.5'})
    assert cli.main(['doctor', str(root)]) == 1
    out = capsys.readouterr().out
    assert 'FAIL the manifest · agent/agent.json: card "price" is "3.5", not a whole mTok rate' in out
    assert out.count('\nFAIL ') == 1 and '1 of 8 checks failed · 1 problem' in out
    assert cli.main(['doctor', '--json', str(root)]) == 1
    data = json.loads(capsys.readouterr().out)
    assert [c['check'] for c in data['checks'] if not c['ok']] == ['the manifest'] and sum(len(c['problems']) for c in data['checks']) == 1


def test_the_failure_count_always_equals_the_named_problems():
    from larryd.doctor import Problem, report, as_json
    problems = [Problem('the manifest', 'a', 0, 'x', 'y'), Problem('a check of its own', 'b', 0, 'z', 'w')]
    text = report('.', problems)
    assert text.count('\nFAIL ') == len(problems) and '2 of 8 checks failed' in text
    assert sum(len(c['problems']) for c in as_json(problems)['checks']) == len(problems)


def test_the_class_picks_the_effect(tmp_path):
    root = _with_card(tmp_path, 'mark2', {'class': 'MARK II SUPER AGENT (HARNESS)'})
    path, manifest = _manifest(root)
    manifest['look'] = {'effect': 'crt'}
    path.write_text(json.dumps(manifest))
    assert any('but the class MARK II SUPER AGENT (HARNESS) draws wellness' in p.wrong for p in doctor.check(root))
    changed = doctor.fix(root)
    assert any('look "effect" = "wellness"' in c for c in changed) and _manifest(root)[1]['look']['effect'] == 'wellness'
    assert doctor.check(root) == []


def test_the_allowed_values_are_in_the_guide_and_every_project(tmp_path):
    from larryd import sheet
    table = sheet.card_table()
    assert table in (pathlib.Path(doctor.__file__).parent / 'GUIDE.md').read_text()
    assert table in (new.make('vals', tmp_path) / 'CLAUDE.md').read_text()
    for name in ('MARK I AGENT (NORMAL)', 'OFF-THE-SHELF', 'INTERNAL', 'cont/card', 'larry/home', 'agnt/home'):
        assert name in table
