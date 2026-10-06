"""THE CARD SHEET'S RULES (larryd/sheet.py, the one place): each rewrite and each removal, the agent's own layout and
looks kept, the same result every time."""
from larryd import sheet


def fixed(text):
    return sheet.rewrite(text)


def test_type_becomes_the_nearest_role():
    out, said = fixed('.x { font-size: 40px; font-weight: 900; font-family: Comic; text-transform: uppercase }')
    assert out == '.x { font-family: var(--font-heading); font-size: var(--font-heading-sz); font-weight: var(--font-heading-wt); text-transform: var(--font-heading-tt) }\n'
    assert any('-> the heading role' in s for s in said)


def test_a_typed_colour_becomes_the_nearest_slot():
    out, _said = fixed('.x { color: #fdfdfd; border: 1px solid rgb(18, 18, 18); background: white }')
    assert '#' not in out and 'rgb(' not in out and 'white' not in out
    assert out.count('var(--active-color-') == 3


def test_spacing_goes_to_the_scale_and_keeps_its_sign():
    out, said = fixed('.x { gap: 10px; padding: 14px 3px 1rem; margin: -7px 0; border-radius: 30px; width: 333px }')
    assert out == '.x { gap: 8px; padding: 12px 2px 16px; margin: -8px 0; border-radius: 32px; width: 333px }\n'   # a width is the agent's own
    assert 'gap 10px -> 8px (the spacing scale)' in said[0]


def test_the_agents_own_layout_and_looks_are_kept():
    text = ('.mk-card { position: absolute; transform: translate(4px, 0) scale(1.2); animation: x 2s infinite }\n'
            '.mk-frame::before { content: ""; inset: 0 }\n@keyframes x { from { opacity: 0 } to { opacity: 1 } }\n'
            '@media (prefers-reduced-motion: reduce) { .mk-card { animation: none } }\n')
    out, said = fixed(text)
    assert out == text.replace(' }\n@keyframes', ' }\n@keyframes') and said == []


def test_a_reach_is_removed():
    out, said = fixed('@import "x.css";\n@import url(//x.example/a.css);\n.x { background: url(https://x.example/a.png); opacity: 1 }\n'
                      '.y { background: url(data:image/png;base64,AA) } .z { background: url(art.png) }')
    assert 'import' not in out and 'x.example' not in out and 'data:' not in out
    assert '.x { opacity: 1 }' in out and '.z { background: url(art.png) }' in out   # an address on the page's own origin: the policy's to judge
    assert sum('removed' in s for s in said) == 4


def test_faces_and_other_at_rules_are_removed():
    out, _said = fixed('@font-face { font-family: X; src: local(X) }\n@charset "utf-8";\n@namespace svg url(x);\n@page { margin: 0 }\n.x { opacity: 1 }')
    assert out == '.x { opacity: 1 }\n'


def test_scripts_in_css_are_removed():
    out, _said = fixed('.x { width: expression(alert(1)); behavior: url(x.htc); -moz-binding: none; background: javascript:x; opacity: 1 }')
    assert out == '.x { opacity: 1 }\n'


def test_pinning_to_the_screen_is_removed():
    out, _said = fixed('.x { position: fixed; top: 0 } .y { position: sticky } .z { position: absolute }')
    assert out == '.x { top: 0 }\n.z { position: absolute }\n'


def test_styling_outside_the_card_is_removed():
    out, said = fixed('html, body, :root { display: none } :host-context(body) .x { opacity: 0 } .mk-card, body .x { opacity: 1 }')
    assert out == '.mk-card { opacity: 1 }\n'
    assert any('names the page outside the card' in s for s in said)


def test_markup_and_escapes_are_removed():
    out, _said = fixed('.x { content: "</style><script>" } .y { background: \\75 rl(x) } .\\31 x { opacity: 0 } /* <b> */ .z { opacity: 1 }')
    assert out == '.z { opacity: 1 }\n'


def test_habit_tags_become_the_roles():
    out, _said = fixed('h1 { opacity: 1 } .mk-card p { opacity: 0.9 }')
    assert out == '.heading { opacity: 1 }\n.mk-card .body { opacity: 0.9 }\n'


def test_a_broken_sheet_keeps_what_closed():
    out, said = fixed('.x { opacity: 1 } .y { opacity: 0')
    assert out == '.x { opacity: 1 }\n' and any('never closes' in s for s in said)


def test_over_the_cap_the_end_is_removed():
    out, said = fixed('.x { opacity: 1 }\n' * 2000)
    assert len(out) <= sheet.CAP and any('over 20000' in s for s in said)


def test_the_form_is_a_fixed_point():
    for text in ('.mk-card { gap: 10px; color: red; font-size: 12px } @media (max-width: 480px) { .x { padding: 5px } }', '.x{}', '', '}}{{', '/* a */ .x { opacity: 1 }'):
        once, _ = fixed(text)
        assert fixed(once) == (once, []), text
