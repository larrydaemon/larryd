"""THE LOOK RECORD: names only, from one fixed menu (kit/catalog.json), checked, cleaned and turned into the card's
custom properties that point at the LIVE theme variables; a designed sheet maps to the nearest names."""
import json
import pathlib
import re

from larryd import look, sheet

REPO = pathlib.Path(__file__).resolve().parent.parent


def test_the_menu_is_one_fixed_list_and_the_runtime_holds_the_same():
    cat = sheet.catalog()
    m = look.menu(cat)
    assert m['accent'][0] == 'active-color-01' and len(m['accent']) == 64
    assert m['radius'] == [f'step-{i}' for i in range(10)] and m['effect'] == ['none', 'crt', 'wellness', 'glitch']
    runtime = json.loads((REPO / 'server' / 'runtime' / 'app' / 'schemas' / 'look.json').read_text())
    assert runtime == look.menu(cat), 'regenerate: python -c "import json; from larryd import look; print(json.dumps(look.menu(), indent=1))" > server/runtime/app/schemas/look.json'


def test_properties_point_at_live_variables_never_a_resolved_value():
    props = look.properties({'accent': 'active-color-04', 'radius': 'step-2', 'space': 'step-3', 'effect': 'wellness'})
    assert props == {'--accent': 'var(--active-color-04)', '--radius': 'var(--step-2)', '--space': 'var(--step-3)', '--effect': 'wellness'}
    for v in props.values():
        assert '#' not in v and 'px' not in v


def test_anything_off_the_menu_is_dropped():
    hostile = {'accent': 'red; background: url(//x)', 'radius': '20px', 'space': 'step-3', 'effect': 'glitch</style>',
               'text': {'name': 'title', 'pitch': 'x;y', 'hack': 'body'}, 'extra': 'step-1'}
    assert look.clean(hostile) == {'space': 'step-3', 'text': {'name': 'title'}}
    assert look.properties(hostile) == {'--space': 'var(--step-3)'}
    assert look.clean('nope') == {} and look.clean({'text': 'x'}) == {}


def test_a_grey_and_twenty_px_map_to_the_nearest_names():
    record, said, _dropped = look.from_sheet('.mk-card { border: 1px solid #8a8a8a; border-radius: 20px }')
    assert record == {'accent': 'active-color-01', 'radius': 'step-6'}
    assert 'distance 0.04' in said[0]   # the closest one, said with its distance; no new colour


def test_a_colour_goes_to_the_nearest_the_eye_sees_not_the_nearest_number():
    record, _, _ = look.from_sheet('.mk-card { color: #ffcc99 }')   # by RGB numbers #D5C5AA; as the eye sees it #EFE5C6
    assert sheet.catalog()['colours']['--' + record['accent']] == '#EFE5C6'


def test_type_on_a_part_goes_to_the_nearest_role_and_elsewhere_is_said_dropped():
    record, said, dropped = look.from_sheet('.mk-price { font-size: 18px; font-weight: 500; text-transform: uppercase } .wrapper { font-size: 12px }')
    assert record == {'text': {'price': 'callout'}} and sheet.ROLE_RULE_CASED in said[0] and 'unwritten' not in said[0]
    assert dropped == ['.wrapper: font-size -> no name on the menu (no text part of the card here (the parts: number, class, name, info, pitch, developer, facts, price))']


def test_the_effect_is_never_read_from_a_sheet():
    """frost-92 on rc17 (Y1): the class picks the effect; a sheet's animation and layers are dropped, said why."""
    record, said, dropped = look.from_sheet('.mk-glow { filter: blur(8px); animation: breathe 6s }\n@keyframes breathe { to { opacity: 1 } }')
    assert 'effect' not in record and said == []
    assert '.mk-glow: filter, animation -> no name on the menu (the class picks the effect, which brings its own motion, light and shadow)' in dropped
    assert '@keyframes breathe -> no name on the menu (the class picks the effect, which brings its own animation)' in dropped


def test_the_runtime_card_template_uses_the_same_fixed_list():
    import re
    cat = sheet.catalog()
    web = REPO / 'server' / 'runtime' / 'app' / 'web'
    css = (web / 'agent_card.css').read_text()
    assert dict(re.findall(r'--(step-\d): (\d+)px', css)) == {k: str(v) for k, v in cat['steps'].items()}
    theme = (web / 'reference_theme.css').read_text()
    assert dict(re.findall(r'(--active-color-\d\d): (#[0-9A-Fa-f]{6})', theme)) == cat['colours']
    for effect in cat['effects'][1:]:
        assert f'[data-effect="{effect}"]' in css


# S1: every value of a designed sheet is said once, as a name or as dropped with why (frost-92's rc11 sheet, its kinds)
FROST92 = """@import url("fonts.css");
.mk-card { border: 2px solid #8a8a8a; border-radius: 20px; padding: 10px; gap: 12px; position: sticky; top: 0; transition: transform .2s ease }
.mk-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0, 0, 0, .4) }
.mk-frame { aspect-ratio: 4 / 3 }
.mk-name { color: #ffb000; font-size: 22px; font-weight: 800; font-style: italic }
.mk-foot { color: #8a8a8a; font-size: 0.85rem; letter-spacing: 0.08em }
@keyframes lift { from { opacity: 0 } to { opacity: 1 } }
"""


def test_every_value_is_named_or_dropped_with_why():
    record, said, dropped = look.from_sheet(FROST92)
    assert record == {'accent': 'active-color-01', 'radius': 'step-6', 'space': 'step-3', 'text': {'name': 'subtitle', 'facts': 'body'}}
    assert any('font-style: italic -> text name' in s for s in said)
    for line in ('@import url("fonts.css") -> no name on the menu (the template loads every file itself)',
                 '@keyframes lift -> no name on the menu (the class picks the effect, which brings its own animation)',
                 '.mk-card: gap -> no name on the menu ("space" is the card\'s padding; the template sets the gaps and margins from it)',
                 '.mk-card: position, top -> no name on the menu (the template places every part)',
                 '.mk-card: transition -> no name on the menu (the class picks the effect, which brings its own motion, light and shadow)',
                 '.mk-card:hover: transform, box-shadow -> no name on the menu (the template draws hover, focus and every other state)',
                 '.mk-frame: aspect-ratio -> no name on the menu (the template lays out the card)',
                 '.mk-name: color -> no name on the menu (colour is card-wide, the accent only: a text part takes a role, never a colour)',
                 '.mk-foot: color -> no name on the menu (colour is card-wide, the accent only: a text part takes a role, never a colour)'):
        assert line in dropped, (line, dropped)
    # nothing unsaid: every declaration of every rule is in a CONVERTED or a DROPPED line
    for selector, body in re.findall(r'^([^@{]+?)\s*\{([^}]*)\}', FROST92, re.M):
        for prop in re.findall(r'([a-z-]+)\s*:', body):
            assert any(s.startswith(selector) and prop in s for s in said + dropped), (selector, prop)


def test_a_layer_s_colour_says_the_effect_draws_it():
    _record, _said, dropped = look.from_sheet('.mk-glow { background: radial-gradient(circle, #D4C4A8 0%, transparent 60%) }')
    assert dropped == ['.mk-glow: background -> no name on the menu (colour is card-wide, the accent only; the class picks the effect, which draws its own layers)']
