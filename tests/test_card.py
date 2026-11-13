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
    monkeypatch.setattr(place, 'WAIT', 0.6)
    root = new.make('lonely', tmp_path)
    with pytest.raises(place.Refused) as no:
        place.place(root)
    assert 'no LARRYD runtime answers' in no.value.wrong and 'run `larryd`' in no.value.todo


def test_place_asks_a_starting_runtime_again_before_giving_up(monkeypatch):
    """frost-92's rc16 X1: `larryd card` right after `larryd` found none; a refused connection is asked again for WAIT seconds."""
    answers = [(0, {'refused': 'no LARRYD runtime answers'})] * 2 + [(201, {'held': {}})]
    monkeypatch.setattr(place, '_post_once', lambda url, data, timeout: answers.pop(0))
    monkeypatch.setattr(place.time, 'sleep', lambda s: None)
    assert place._post('http://127.0.0.1:1/x', b'') == (201, {'held': {}}) and answers == []


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


def test_a_look_is_no_manifest_field_and_fix_removes_it(tmp_path):   # the platform draws the card from its data (the owner 2026-11-03)
    root = _with_card(tmp_path, 'mark2', {'class': 'MARK II SUPER AGENT (HARNESS)'})
    path, manifest = _manifest(root)
    manifest['look'] = {'effect': 'crt'}
    path.write_text(json.dumps(manifest))
    assert any('"look" is not a manifest field' in p.wrong for p in doctor.check(root))
    changed = doctor.fix(root)
    assert any('"look" removed' in c for c in changed) and 'look' not in _manifest(root)[1]
    assert doctor.check(root) == []


def test_the_allowed_values_are_in_the_guide_and_every_project(tmp_path):
    from larryd import sheet
    table = sheet.card_table()
    assert table in (pathlib.Path(doctor.__file__).parent / 'GUIDE.md').read_text()
    assert table in (new.make('vals', tmp_path) / 'CLAUDE.md').read_text()
    for name in ('MARK I AGENT (NORMAL)', 'OFF-THE-SHELF', 'INTERNAL', 'cont/card', 'larry/home', 'agnt/home'):
        assert name in table


def test_authorization_is_the_developer_s_starting_setting(tmp_path):
    """The owner: the developer sets the original setting; the authorize panel can change it at any time after."""
    root = new.make('auth', tmp_path)
    assert _manifest(root)[1]['card']['authorization'] == 'PUBLIC' and doctor.check(root) == []
    assert doctor.check(_with_card(tmp_path, 'priv', {'authorization': 'PRIVATE'})) == []
    wrong = [p.wrong for p in doctor.check(_with_card(tmp_path, 'odd', {'authorization': 'SECRET'}))]
    assert wrong == ['card "authorization" is "SECRET", not one the platform knows']
    path, manifest = _manifest(root)
    del manifest['card']['authorization']
    path.write_text(json.dumps(manifest))
    assert any('card "authorization" is missing' in p.wrong for p in doctor.check(root))
    doctor.fix(root)
    assert _manifest(root)[1]['card']['authorization'] == 'PUBLIC' and doctor.check(root) == []
    from larryd import sheet
    assert 'the platform\'s authorize panel can change it at any time after' in sheet.card_table()



def test_module_is_the_platform_s_own_name_for_the_screen(tmp_path):
    """frost-92 on rc17 (Y2): one name everywhere, the platform's (engine.json: agnt is Agents), checked like product."""
    for root in (new.make('blankm', tmp_path), new.make('examplem', tmp_path, example='marketplace')):
        assert _manifest(root)[1]['card']['module'] == 'Agents' and doctor.check(root) == []
    assert doctor.check(_with_card(tmp_path, 'lower', {'module': 'agents'})) == []   # the same name, any case
    wrong = [p for p in doctor.check(_with_card(tmp_path, 'oldname', {'module': 'AGENT'}))]
    assert [p.wrong for p in wrong] == ['card "module" is "AGENT", but the screen agnt/home is in Agents']
    assert 'set card "module" to "Agents"' in wrong[0].todo
    from larryd import sheet
    assert '| agnt/home, agnt/list, agnt/card | LARRYD | Agents |' in sheet.card_table()


def test_a_missing_authorization_says_fix_fills_it(tmp_path):
    root = new.make('noauth', tmp_path)
    path, manifest = _manifest(root)
    del manifest['card']['authorization']
    path.write_text(json.dumps(manifest))
    todo = next(p.todo for p in doctor.check(root) if 'authorization' in p.wrong)
    assert todo.endswith('or run `larryd doctor --fix`, or larryd_doctor with "fix": true (fills PUBLIC)')


def test_class_and_residency_carry_their_meanings(tmp_path):
    """The owner: residency is which marketplaces it is offered on; the class, as a guide, how complex it is."""
    from larryd import sheet
    todo = next(p.todo for p in doctor.check(_with_card(tmp_path, 'res', {'residency': 'CLOUD'})) if 'residency' in p.wrong)
    assert todo == ("use one of: INTERNAL (Positive Feedback's own agent marketplace only), EXTERNAL (other marketplaces only "
                    "(e.g. the Microsoft marketplace), not Positive Feedback), BOTH (Positive Feedback and at least one other marketplace)")
    todo = next(p.todo for p in doctor.check(_with_card(tmp_path, 'cls', {'class': 'MARK IV'})) if 'class' in p.wrong)
    assert '(simple)' in todo and '(complex)' in todo and '(extremely complex)' in todo
    table, guide = sheet.card_table(), (pathlib.Path(doctor.__file__).parent / 'GUIDE.md').read_text()
    assert 'MARK I AGENT (NORMAL): simple;' in table and 'effect' not in table and 'INTERNAL: Positive Feedback\'s own agent marketplace only' in table
    assert table in (new.make('mean', tmp_path) / 'CLAUDE.md').read_text() and table in guide
    assert 'It is not where the agent runs: every LARRYD agent runs in LARRYD.' in guide and 'where it runs' not in table


@pytest.mark.parametrize('site', ['https://positivefeedback.ai', 'https://www.example.co.uk/agents/hello?x=1', 'https://a-b.example.com/'])
def test_a_developers_site_is_optional_and_a_plain_https_address_passes(tmp_path, site):   # the card links the developer's name to it
    root = _with_card(tmp_path, 's' + re.sub(r'[^a-z0-9]', '', site)[:20], {'developer_site': site})
    assert [p.wrong for p in doctor.check(root) if p.check == 'the manifest'] == []
    assert 'developer_site' not in shape.CARD and 'developer_site' in shape.CARD_OPTIONAL   # a fresh project carries none and passes


@pytest.mark.parametrize('site', ['', 'http://positivefeedback.ai', 'positivefeedback.ai', '//positivefeedback.ai', 'javascript:alert(1)', 'https://127.0.0.1/',
                                  'https://localhost', 'https://user@example.com', 'https://example.com:8443', 'https://example.com/a b', 'https://example.com/"x',
                                  'https://example.com/<b>', 'https://exa mple.com', 5, None, ['https://example.com']])
def test_a_developers_site_that_is_not_plain_https_is_refused_with_what_to_do(tmp_path, site):
    root = _with_card(tmp_path, 'n' + re.sub(r'[^a-z0-9]', '', str(site))[:20], {'developer_site': site})
    problems = [p for p in doctor.check(root) if p.check == 'the manifest']
    assert any('card "developer_site" is' in p.wrong and 'not a plain https address' in p.wrong for p in problems), [p.wrong for p in problems]
    assert all(p.todo for p in problems)


def test_the_tool_and_the_runtime_agree_on_a_developers_site():   # what the doctor passes, the runtime's gate draws
    from larryd_runtime.core_engine import view
    for site in ('https://positivefeedback.ai', 'https://www.example.co.uk/agents/hello?x=1', 'https://a-b.example.com/', 'http://positivefeedback.ai', 'https://127.0.0.1/',
                 'https://localhost', 'https://user@example.com', 'https://example.com:8443', 'https://example.com/a b', 'javascript:alert(1)', ''):
        assert bool(re.fullmatch(shape.SITE, site)) == view.link_address(site), site


def test_an_offline_agent_says_so_on_its_card_and_only_that_word_passes(tmp_path):
    assert [p.wrong for p in doctor.check(_with_card(tmp_path, 'off1', {'availability': 'offline'})) if p.check == 'the manifest'] == []
    assert [p.wrong for p in doctor.check(_with_card(tmp_path, 'adm1', {'availability': 'ADMINS ONLY'})) if p.check == 'the manifest'] == []   # an account admins' agent (the owner 2026-11-13): the one other word
    for n, bad in enumerate(('online', 'OFFLINE', '', True, None, 'admins only', 'ADMINS')):
        problems = [p for p in doctor.check(_with_card(tmp_path, f'off{n + 2}', {'availability': bad})) if p.check == 'the manifest']
        assert any('card "availability" is' in p.wrong for p in problems), bad
