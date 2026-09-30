"""larryd.ai (website/, served as is from /var/www/larryd): the install lines are the docs' lines in the owner's order,
the page never says the runtime's internal name, and every file it points at is in the tree."""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / 'website'
PAGE = (SITE / 'index.html').read_text()

LINES = ['npm install -g larryd', 'pip install larryd', 'pipx install larryd', 'cargo install larryd', 'sudo larryd &amp;']


def test_the_install_lines_in_the_owners_order():
    at = [PAGE.find(f'<code>{line}</code>') for line in LINES]
    assert all(i >= 0 for i in at), dict(zip(LINES, at))
    assert at == sorted(at)


def test_larryd_only():
    for path in SITE.rglob('*'):
        if path.suffix in ('.html', '.css', '.js'):
            assert 'hanzo' not in path.read_text().lower(), path


def test_every_local_file_it_points_at_is_there():
    wanted = set(re.findall(r'(?:src|href|srcset|poster)="/([^"#?]+)"', PAGE)) | set(re.findall(r'url\("/([^")]+)"\)', (SITE / 'site.css').read_text()))
    assert wanted
    missing = sorted(p for p in wanted if not (SITE / p).is_file())
    assert not missing, missing
