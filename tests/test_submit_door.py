"""LARRYD's submit door: every guard frost-41 named has a planted test (size cap, the hourly limit, the doctor re-run
here, nothing sent ever run, deleted at 10 minutes), and the claim takes only the SSO proxy's signed hand-off for the
sign-in started for that file, in that browser, once. A scratch proxy key signs; nothing live."""
import io
import json
import pathlib
import re
import sqlite3
import zipfile
from urllib.parse import parse_qs, urlsplit

import pytest

from larryd import bundle, new, sso_handoff, submit_door

ORIGIN, ISSUER, NOW = 'https://login.example.test', 'login.example.test', 1_800_000_000


@pytest.fixture
def world(tmp_path):
    private, public = sso_handoff.new_key()
    conf = json.loads(json.dumps(submit_door.CONFIG))
    conf.update(origin=ORIGIN, uploads_per_address_per_hour=3)
    conf['proxy'] = {'start': f'https://{ISSUER}/sso/start', 'issuer': ISSUER, 'public_key': public.decode()}
    clock = {'now': NOW}
    app = submit_door.create_app(tmp_path / 'instance', conf, now=lambda: clock['now'])
    project = new.make('weather', tmp_path)
    return {'c': app.test_client(), 'private': private, 'clock': clock, 'instance': tmp_path / 'instance', 'project': project, 'conf': conf}


def _upload(w, data=None):
    data = bundle.make(w['project'])[0] if data is None else data
    return w['c'].post('/submit/upload', data=data, content_type='application/octet-stream')


def _held_id(answer):
    return answer.get_json()['claim'].rsplit('/', 1)[1]


def _start(w, held, provider='google'):
    started = w['c'].get(f'/submit/start/{held}/{provider}')
    q = {k: v[0] for k, v in parse_qs(urlsplit(started.headers['Location']).query).items()}
    return started, q


def _handoff(w, q, **over):
    args = dict(iss=ISSUER, aud=ORIGIN, provider=q['provider'], sub='dev-sub', email='dev@example.com', email_verified=True,
                state=q['state'], nonce=q['nonce'], now=w['clock']['now'])
    args.update(over)
    key = args.pop('key', w['private'])
    return sso_handoff.sign(key, **args)


def _signed_in(w, token, state, client=None):
    return (client or w['c']).post('/submit/signed-in', data={'handoff': token, 'state': state})


def _rows(w, table):
    con = sqlite3.connect(w['instance'] / 'larryd_submit.db')
    rows = con.execute(f'SELECT * FROM {table}').fetchall()
    con.close()
    return rows


# ---------------------------------------------------------------- the whole way
def test_upload_claim_sign_in_queued(world):
    w = world
    up = _upload(w)
    assert up.status_code == 201 and up.get_json()['claim'].startswith(f'{ORIGIN}/submit/claim/') and up.get_json()['minutes'] == 10
    held = _held_id(up)
    page = w['c'].get(f'/submit/claim/{held}').get_data(as_text=True)
    assert 'weather' in page and f'/submit/start/{held}/google' in page and f'/submit/start/{held}/apple' in page
    started, q = _start(w, held)
    assert started.headers['Location'].startswith(f'https://{ISSUER}/sso/start?') and q['back'] == ORIGIN + '/submit/signed-in'
    done = _signed_in(w, _handoff(w, q), q['state'])
    text = done.get_data(as_text=True)
    assert done.status_code == 200 and 'is in the review queue' in text and 'dev@example.com' in text
    [row] = _rows(w, 'queue')
    assert row[1] == 'weather' and row[4:7] == ('google', 'dev-sub', 'dev@example.com') and row[8] == 'waiting'
    assert _rows(w, 'held') == [] and len(list((w['instance'] / 'queue').iterdir())) == 1 and not list((w['instance'] / 'held').iterdir())


# ---------------------------------------------------------------- the upload's guards
def test_the_size_cap(world):
    answer = _upload(world, b'x' * (bundle.MOST_BYTES + 1))
    assert answer.status_code == 413 and _rows(world, 'held') == []


def test_the_hourly_limit_per_address(world):
    for _ in range(3):
        assert _upload(world).status_code == 201
    assert _upload(world).status_code == 429
    world['clock']['now'] += 3601
    assert _upload(world).status_code == 201


def test_the_doctor_is_run_here_and_nothing_is_kept(world):
    code = world['project'] / 'agent' / 'agent.py'
    code.write_text(code.read_text() + '\nimport socket\n')
    answer = _upload(world)
    assert answer.status_code == 422 and answer.get_json()['problems'][0]['check'] == 'the air gap'
    assert _rows(world, 'held') == [] and not list((world['instance'] / 'held').iterdir())


def test_nothing_sent_is_ever_run(world, tmp_path):
    planted = tmp_path / 'ran.txt'
    code = world['project'] / 'agent' / 'agent.py'
    code.write_text(code.read_text() + f'\nopen({str(planted)!r}, "w").write("ran")\n')   # the doctor refuses the path; nothing runs either way
    _upload(world)
    assert not planted.exists()


def _zip(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for name, body, mode in entries:
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED   # a bomb packs small and unpacks big
            z.writestr(info, body)
    return out.getvalue()


@pytest.mark.parametrize('entries', [
    [('../escape.py', b'x', 0o100644)],
    [('/abs.py', b'x', 0o100644)],
    [('link', b'/etc/passwd', 0o120777)],
    [('agent.json', b'0' * (bundle.MOST_BYTES + 10), 0o100644)],
    [(f'f{i}.txt', b'x', 0o100644) for i in range(bundle.MOST_FILES + 1)],
])
def test_an_unsafe_zip_is_refused_and_nothing_is_written(world, tmp_path, entries):
    data = _zip(entries)
    assert len(data) < bundle.MOST_BYTES   # small enough that the zip's own check, not the size cap, refuses it
    answer = _upload(world, data)
    assert answer.status_code == 400 and _rows(world, 'held') == []
    assert not (tmp_path / 'escape.py').exists()


def test_not_a_zip(world):
    assert _upload(world, b'not a zip').status_code == 400


def test_held_ten_minutes_then_deleted(world):
    held = _held_id(_upload(world))
    world['clock']['now'] += 601
    assert world['c'].get(f'/submit/claim/{held}').status_code == 404
    assert _rows(world, 'held') == [] and not list((world['instance'] / 'held').iterdir())


# ---------------------------------------------------------------- the claim's guards
def test_a_claim_works_once(world):
    held = _held_id(_upload(world))
    _, q = _start(world, held)
    token = _handoff(world, q)
    assert _signed_in(world, token, q['state']).status_code == 200
    assert _signed_in(world, token, q['state']).status_code == 400
    assert len(_rows(world, 'queue')) == 1


def test_another_browser_is_refused(world):
    held = _held_id(_upload(world))
    _, q = _start(world, held)
    other = submit_door.create_app(world['instance'], world['conf'], now=lambda: world['clock']['now']).test_client()
    assert _signed_in(world, _handoff(world, q), q['state'], client=other).status_code == 400
    assert _rows(world, 'queue') == [] and len(_rows(world, 'held')) == 1


@pytest.mark.parametrize('over', [
    {'aud': 'https://app.example.test'}, {'iss': 'someone.else'}, {'nonce': 'N' * 32}, {'provider': 'apple'},
])
def test_a_hand_off_not_for_this_claim_is_refused(world, over):
    held = _held_id(_upload(world))
    _, q = _start(world, held)
    assert _signed_in(world, _handoff(world, q, **over), q['state']).status_code == 400
    assert _rows(world, 'queue') == []


def test_another_key_is_refused(world):
    held = _held_id(_upload(world))
    _, q = _start(world, held)
    other, _ = sso_handoff.new_key()
    assert _signed_in(world, _handoff(world, q, key=other), q['state']).status_code == 400


def test_an_old_hand_off_is_refused(world):
    held = _held_id(_upload(world))
    _, q = _start(world, held)
    token = _handoff(world, q)
    world['clock']['now'] += 120
    assert _signed_in(world, token, q['state']).status_code == 400


def test_the_address_is_kept_only_as_a_hash(world):
    _upload(world)
    [(address, _)] = _rows(world, 'hits')
    assert re.fullmatch(r'[0-9a-f]{64}', address) and '127.0.0.1' not in address


def test_the_pages_run_no_script(world):
    held = _held_id(_upload(world))
    page = world['c'].get(f'/submit/claim/{held}')
    assert '<script' not in page.get_data(as_text=True) and "default-src 'none'" in page.headers['Content-Security-Policy']


def test_the_door_carries_the_live_proxys_name():
    assert submit_door.CONFIG['origin'] == 'https://login.positivefeedback.ai'
    assert submit_door.CONFIG['proxy']['issuer'] == 'login.positivefeedback.ai'
    assert submit_door.CONFIG['proxy']['public_key'].startswith('-----BEGIN PUBLIC KEY-----')


def test_the_bundle_keeps_its_own_size_cap(tmp_path):
    """Two layers: the door's cap refuses the body first; the bundle refuses it too, for any other caller."""
    assert bundle.open_safely(b'x' * (bundle.MOST_BYTES + 1), tmp_path) == [f'the file is larger than {bundle.MOST_BYTES} bytes']
    assert not (tmp_path / 'agent').exists()


def test_the_same_agent_packs_to_the_same_file(tmp_path):
    root = new.make('same', tmp_path)
    assert bundle.make(root) == bundle.make(root)
    names = zipfile.ZipFile(io.BytesIO(bundle.make(root)[0])).namelist()
    assert names == ['agent.json', 'agent.py']   # agent/ only: no project file, no key, no cache
