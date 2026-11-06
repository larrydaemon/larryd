"""The doctor's "no secret" check: a name is not a secret (CORE_CLEANUP_IV 55, frost-05: the CMO app's TOKENS = 'press_tokens.json'
was taken for a secret). A file's name or path assigned to a word like token or secret passes; a real-looking value still fails."""
import pytest

from larryd import doctor, new


@pytest.fixture
def agent(tmp_path):
    return new.make('names', tmp_path)


def plant(root, line):
    (root / 'agent' / 'helper.py').write_text(line + '\n')
    return [p for p in doctor.check(root) if p.check == 'no secret']


@pytest.mark.parametrize('line', [
    "TOKENS = 'press_tokens.json'",
    "SECRET_FILE = '~/.frost_session_secret.txt'",
    "password_log = 'logs/passwords_tried.log'",
    "API_KEY_PATH = 'keys/settings.yaml'",
])
def test_a_file_name_is_not_a_secret(agent, line):
    assert plant(agent, line) == []


@pytest.mark.parametrize('line', [
    "TOKEN = 'a8f9c2e1d4b7a6c3e0f1'",
    "password = 'hunter2hunter2'",
    "api_key = 'AbCdEfGh12345678'",
    "SECRET = 'not-a-file-name-at-all'",
])
def test_a_value_is_still_a_secret(agent, line):
    found = plant(agent, line)
    assert len(found) == 1 and 'a secret written into the code' in found[0].wrong
