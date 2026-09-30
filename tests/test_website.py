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
    pages = PAGE
    wanted = set(re.findall(r'(?:src|href|srcset|poster)="/([^"#?]+)"', pages)) | set(re.findall(r'url\("/([^")]+)"\)', (SITE / 'site.css').read_text()))
    assert wanted
    missing = sorted(p for p in wanted if not (SITE / p).is_file())
    assert not missing, missing


# ---------------------------------------------------------------- the page's one spine (the owner's review, 2026-09-30)
def _at(text, needle):
    i = PAGE.find(needle)
    assert i >= 0, needle
    return i


def test_the_sections_in_order():
    order = ['class="hero"', 'id="install"', 'id="what"', 'id="cant"', 'id="checks"', 'class="band price"', 'id="faq"']
    at = [_at(PAGE, n) for n in order]
    assert at == sorted(at), dict(zip(order, at))
    assert 'id="how"' not in PAGE and 'From an idea to a working agent' not in PAGE
    hero = PAGE[_at(PAGE, 'class="hero"'):_at(PAGE, 'id="install"')]
    assert 'class="terminal' not in hero   # the owner: install goes right under the hero, no terminal output there


def test_the_hero_keeps_its_words():
    for words in ('LARRYD keeps your agents from going rogue.', 'Your server has a daemon.<br>Your agents should have one too.',
                  'Free · for Mac and Linux · works with Claude Code', '>Install LARRYD</a>', '>See how it works</a>'):
        assert words in PAGE, words


def test_the_proof_is_what_the_doctor_says(tmp_path):
    from larryd import doctor, new
    fresh = doctor.report(new.make('weather-report', tmp_path), []).splitlines()[1:]
    proof = PAGE[_at(PAGE, 'class="terminal proof"'):]
    proof = proof[proof.index('<pre>'):proof.index('</pre>')]
    assert '\n'.join(fresh) in proof


def test_what_your_agent_cant_do():
    cant = PAGE[_at(PAGE, 'id="cant"'):_at(PAGE, 'id="checks"')]
    assert 'What your agent can\'t do.' in cant
    assert len(re.findall(r'<li><strong>It ', cant)) == 5


def test_the_install_lines_show_in_one_terminal_never_folded():
    """The owner: the install is one terminal wall with every line showing, for developers; nothing folded away."""
    install = PAGE[_at(PAGE, 'id="install"'):_at(PAGE, 'id="what"')]
    assert '<details' not in install
    assert all(f'<code>{line}</code>' in install for line in LINES)


def test_share_is_a_card_marked_open():
    """The owner: "just say open"."""
    card = PAGE[_at(PAGE, 'class="card card-open"'):]
    card = card[:card.index('</article>')]
    assert '<h3>Share</h3>' in card and '<em class="soon">Open</em>' in card and 'soon</em>' not in card.replace('class="soon">Open</em>', '')


def test_the_nav_has_one_coloured_button():
    nav = PAGE[_at(PAGE, '<header class="nav">'):_at(PAGE, '</header>')]
    assert re.findall(r'class="button[^"]*"', nav) == ['class="button button-small"'] and 'Get LARRYD — free' in nav


def test_no_heading_without_a_body():
    for page in (PAGE,):
        for m in re.finditer(r'<h2>(.*?)</h2>\s*(</div>\s*)?(<section|</main>|$)', page):
            raise AssertionError(f'a heading with nothing under it: {m.group(1)}')


def test_every_image_speaks_or_is_silent():
    for alt in re.findall(r'<img [^>]*alt="([^"]*)"', PAGE):
        assert alt in ('', 'LARRYD', 'LARRYD checks v1: PASS'), alt


# ---------------------------------------------------------------- THE LARRYD CHECKS
def test_the_checks_page_and_spec_name_the_doctors_checks():
    from larryd import doctor
    page = PAGE[PAGE.index('id="checks"'):]
    spec = (REPO / 'CHECKS.md').read_text()
    assert f'# THE LARRYD CHECKS · version {doctor.CHECKS_VERSION}' in spec
    assert f'Version {doctor.CHECKS_VERSION}' in page
    assert re.findall(r'<h3>([^<]+)</h3>', page) == list(doctor.CHECKS)
    assert re.findall(r'^\| \d \| \*\*([^*]+)\*\*', spec, re.M) == list(doctor.CHECKS)
    assert 'Declared in the manifest, enforced when it runs.' in page


def test_one_long_page_and_the_logo_is_the_heartbeat_alone():
    """The owner: one single long page; the logo at the very top is the heartbeat line, no word."""
    assert not (SITE / 'checks.html').exists() and 'id="checks"' in PAGE
    header = PAGE[_at(PAGE, '<header class="nav">'):_at(PAGE, '</header>')]
    brand = header[:header.index('</a>')]
    assert 'brand-mark' in brand and 'brand-word' not in brand
