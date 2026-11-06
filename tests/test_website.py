"""larryd.ai (website/, served as is from /var/www/larryd), as it IS: website/index.html was made equal to the owner's live
larryd.ai page on 2026-10-21 (9b2905d), and these tests describe that page (CORE_CLEANUP_IV, frost-05: the tests follow the owner's
page, never the page the tests). The install lines are the published ones in the owner's order; npm and cargo stay off the page
until they are published past their 0.0.1 placeholder."""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / 'website'
PAGE = (SITE / 'index.html').read_text()

LINES = ['pipx install larryd', 'uv tool install --python 3.12 larryd', 'larryd']
UNPUBLISHED = ['npm install -g larryd', 'cargo install larryd']   # the registries hold only the name's 0.0.1 placeholder


def test_the_install_lines_in_the_owners_order():
    at = [PAGE.find(f'<code>{line}</code>') for line in LINES]
    assert all(i >= 0 for i in at), dict(zip(LINES, at))
    assert at == sorted(at)
    assert not any(line in PAGE for line in UNPUBLISHED)   # never a line that installs nothing yet


# ---------------------------------------------------------------- the page's one spine (the owner's review, 2026-09-30)
def _at(text, needle):
    i = PAGE.find(needle)
    assert i >= 0, needle
    return i


def test_the_sections_in_order():
    order = ['class="hero"', 'id="install"', 'id="ready"', 'id="what"', 'id="cannot"', 'id="walls"', 'id="observe"', 'id="faq"', 'id="server"']
    at = [_at(PAGE, n) for n in order]
    assert at == sorted(at), dict(zip(order, at))
    assert 'id="how"' not in PAGE and 'From an idea to a working agent' not in PAGE
    hero = PAGE[_at(PAGE, 'class="hero"'):_at(PAGE, 'id="install"')]
    assert 'class="terminal' not in hero   # the owner: install goes right under the hero, no terminal output there


def test_the_hero_keeps_its_words():
    for words in ('LARRYD keeps your agents from going rogue.', 'Your server has a daemon.<br>Your agents should have one too.',
                  'Free · for Mac and Linux · works with Claude Code', '>Install LARRYD</a>', '>See how it works</a>'):
        assert words in PAGE, words


def test_the_prompt_box_is_the_prompt_for_claude_code():
    """the live page's terminal box holds the prompt a developer gives Claude Code, whole (it replaced the doctor's printout)"""
    box = PAGE[_at(PAGE, 'class="terminal proof vsc vsc-prompt"'):]
    box = box[box.index('<pre'):box.index('</pre>')]
    assert 'I want to install LARRYD on this machine and start building AI agents with you.' in box
    assert 'WHAT LARRYD IS' in box and 'LARRYD Developer' in box and 'LARRYD Server' in box


def test_what_agents_cant_do():
    cant = PAGE[_at(PAGE, 'id="cannot"'):_at(PAGE, 'id="walls"')]
    assert 'What agents can’t do in LARRYD' in cant
    assert re.findall(r'<li[^>]*><strong>([^<]+)</strong>', cant) == [
        'REACH THE INTERNET.', 'OPEN YOUR FILES.', 'START OTHER PROGRAMS.', 'CARRY SECRETS.', 'GO PAST ITS JOB.']


def test_the_install_lines_show_in_one_terminal_never_folded():
    """The owner: the install is one terminal wall with every line showing, for developers; nothing folded away."""
    install = PAGE[_at(PAGE, 'id="install"'):_at(PAGE, 'id="what"')]
    assert '<details' not in install
    assert all(f'<code>{line}</code>' in install for line in LINES)


def test_no_heading_without_a_body():
    for page in (PAGE,):
        for m in re.finditer(r'<h2>(.*?)</h2>\s*(</div>\s*)?(<section|</main>|$)', page):
            raise AssertionError(f'a heading with nothing under it: {m.group(1)}')


# ---------------------------------------------------------------- THE LARRYD CHECKS
def test_the_checks_spec_names_the_doctors_checks():
    """THE LARRYD CHECKS live in CHECKS.md (the live page has no checks section): its version and its checks are the doctor's own"""
    from larryd import doctor
    spec = (REPO / 'CHECKS.md').read_text()
    assert f'# THE LARRYD CHECKS · version {doctor.CHECKS_VERSION}' in spec
    assert re.findall(r'^\| \d \| \*\*([^*]+)\*\*', spec, re.M) == list(doctor.CHECKS)


def test_the_platforms_own_page():
    """The owner: the official LARRYD page's chrome 1:1 (built inside the platform's page system: its header, footer,
    CRT animation and the brand's own stylesheets from /cdn-pf/, never a copy), our words in <main>, the standard server
    section (id="server") above the footer, no price section, no sudo."""
    for css in ('faf51f39/static/css/core.css', 'faf51f39/static/css/faf51f39.css', 'def9f8bf/static/css/def9f8bf.css'):
        assert f'<link rel="stylesheet" href="/cdn-pf/' in PAGE and css in PAGE, css
    assert 'data-brilliance-hierarchy="F13650BD0AC1"' in PAGE and 'class="pf-crt-warm pf-anim--crt"' in PAGE
    assert PAGE.count('<header class="layout--header">') == 1 and PAGE.count('<footer class="layout--footer">') == 1
    assert PAGE.index('<main class="lx-ours">') < PAGE.index('id="server"') < PAGE.index('<footer class="layout--footer">')   # the standard server section above the footer
    assert 'lx-chrome' not in PAGE
    assert 'band price' not in PAGE and 'sudo larryd' not in PAGE
