"""larryd.ai: the page is the official site's own page (its header, CRT background, stylesheets and footer), only the
content is LARRYD's. The owner's words hold it."""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'website'
PAGE = (SITE / 'index.html').read_text()
LINES = ['npm install -g larryd', 'pip install larryd', 'pipx install larryd', 'cargo install larryd', 'sudo larryd &amp;']


def test_the_official_chrome_is_there():
    assert '<header class="layout--header">' in PAGE and '<footer class="layout--footer">' in PAGE
    assert 'pf-anim--crt' in PAGE and 'crtfx.js' in PAGE
    assert PAGE.count('class="hdr-icon-btn"') >= 4 and '>MENU</span>' in PAGE


def test_the_owners_words():
    assert 'LARRYD KEEPS YOUR AGENTS FROM GOING ROGUE.' in PAGE
    assert 'Your server has a daemon. Your agents should have one too.' in PAGE
    assert PAGE.count('class="main-button"') >= 2


def test_install_lines_in_order_right_after_the_top():
    at = [PAGE.index(f'<b>{l}</b>') for l in LINES]
    assert at == sorted(at)
    assert PAGE.index('id="install"') < PAGE.index('id="what"') < PAGE.index('id="cant"') < PAGE.index('id="checks"')


def test_no_internal_name_and_no_soon():
    assert 'HANZO' not in PAGE.upper() and 'soon' not in PAGE.lower()
