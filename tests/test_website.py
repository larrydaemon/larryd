"""larryd.ai (website/, served as is from /var/www/larryd): the install lines are the docs' lines in the owner's order,
the page never says the runtime's internal name, and every file it points at is in the tree."""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / 'website'
PAGE = (SITE / 'index.html').read_text()

LINES = ['pipx install larryd', 'uv tool install larryd', 'npm install -g larryd', 'cargo install larryd', 'larryd']


def test_the_install_lines_in_the_owners_order():
    at = [PAGE.find(f'<code>{line}</code>') for line in LINES]
    assert all(i >= 0 for i in at), dict(zip(LINES, at))
    assert at == sorted(at)


def test_larryd_only():
    for path in SITE.rglob('*'):
        if path.suffix in ('.html', '.css', '.js'):
            assert 'hanzo' not in path.read_text().lower(), path


# ---------------------------------------------------------------- the page's one spine (the owner's review, 2026-09-30)
def _at(text, needle):
    i = PAGE.find(needle)
    assert i >= 0, needle
    return i


def test_the_sections_in_order():
    order = ['class="hero"', 'id="about"', 'id="install"', 'id="what"', 'id="cant"', 'id="observe"', 'id="stack"', 'id="it-leaders"',
             'id="checks"', 'id="faq"', 'id="how-we-build"']
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
    proof = PAGE[_at(PAGE, 'class="terminal proof vsc"'):]
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
    assert '>Share</h3>' in card and '<em class="soon">Open</em>' in card and 'soon</em>' not in card.replace('class="soon">Open</em>', '')


def test_no_heading_without_a_body():
    for page in (PAGE,):
        for m in re.finditer(r'<h2>(.*?)</h2>\s*(</div>\s*)?(<section|</main>|$)', page):
            raise AssertionError(f'a heading with nothing under it: {m.group(1)}')


# ---------------------------------------------------------------- THE LARRYD CHECKS
def test_the_checks_page_and_spec_name_the_doctors_checks():
    from larryd import doctor
    page = PAGE[PAGE.index('id="checks"'):]
    spec = (REPO / 'CHECKS.md').read_text()
    assert f'# THE LARRYD CHECKS · version {doctor.CHECKS_VERSION}' in spec
    assert f'Version {doctor.CHECKS_VERSION}' in page
    assert re.findall(r'<h3[^>]*>([^<]+)</h3>', page) == list(doctor.CHECKS)
    assert re.findall(r'^\| \d \| \*\*([^*]+)\*\*', spec, re.M) == list(doctor.CHECKS)
    assert 'Declared in the manifest, enforced when it runs.' in page




def test_the_platforms_own_page():
    """The owner: the official LARRYD page's chrome 1:1 (built inside the platform's page system: its header, footer,
    CRT animation and the brand's own stylesheets from /cdn-pf/, never a copy), our words in <main>, the standard server
    section above the footer, no price section, no sudo."""
    for css in ('faf51f39/static/css/core.css', 'faf51f39/static/css/faf51f39.css', 'def9f8bf/static/css/def9f8bf.css'):
        assert f'<link rel="stylesheet" href="/cdn-pf/' in PAGE and css in PAGE, css
    assert 'data-brilliance-hierarchy="F13650BD0AC1"' in PAGE and 'class="pf-crt-warm pf-anim--crt"' in PAGE
    assert PAGE.count('<header class="layout--header">') == 1 and PAGE.count('<footer class="layout--footer">') == 1
    assert PAGE.index('<main class="lx-ours">') < PAGE.index('Our Own Silicon') < PAGE.index('<footer class="layout--footer">')
    assert 'lx-chrome' not in PAGE
    assert 'band price' not in PAGE and 'sudo larryd' not in PAGE
