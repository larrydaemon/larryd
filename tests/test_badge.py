"""THE DOCTOR BADGE: `larryd doctor --badge` writes a small SVG beside agent/ for a README; its words follow the result
(PASS in the brand's gold, FAIL in red), with the day and the checks' version."""
import datetime
import re
import xml.etree.ElementTree as ET

import pytest

from larryd import cli, doctor, new


@pytest.fixture
def agent(tmp_path):
    return new.make('badged', tmp_path)


def _words(svg):
    return ' '.join(t.text for t in ET.fromstring(svg).iter('{http://www.w3.org/2000/svg}text'))


def test_a_passing_agent_gets_a_gold_pass(agent, capsys):
    assert cli.main(['doctor', str(agent), '--badge']) == 0
    svg = (agent / doctor.BADGE).read_text()
    today = datetime.date.today().isoformat()
    assert _words(svg) == f'LARRYD checks v{doctor.CHECKS_VERSION} PASS {today}'
    assert doctor.GOLD in svg and doctor.RED not in svg
    assert f'![LARRYD checks]({doctor.BADGE})' in capsys.readouterr().out


def test_a_failing_agent_gets_a_red_fail(agent):
    path = agent / 'agent' / 'agent.py'
    path.write_text(path.read_text() + '\nimport socket\n')
    assert cli.main(['doctor', str(agent), '--badge']) == 1
    svg = (agent / doctor.BADGE).read_text()
    assert re.search(r'>FAIL \d{4}-\d{2}-\d{2}<', svg) and 'PASS' not in svg
    assert doctor.RED in svg


def test_the_badge_is_not_part_of_the_agent(agent):
    cli.main(['doctor', str(agent), '--badge'])
    assert not (agent / 'agent' / doctor.BADGE).exists()
    assert doctor.check(agent) == []   # written beside agent/, the next doctor run still passes


def test_no_badge_unless_asked(agent):
    cli.main(['doctor', str(agent)])
    assert not (agent / doctor.BADGE).exists()


def test_the_json_names_the_checks_version(agent, capsys):
    cli.main(['doctor', str(agent), '--json'])
    import json
    assert json.loads(capsys.readouterr().out)['checks_version'] == doctor.CHECKS_VERSION
