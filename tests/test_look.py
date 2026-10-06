"""THE LOOK RECORD: names only, from one fixed menu (kit/catalog.json), checked, cleaned and turned into the card's
custom properties that point at the LIVE theme variables; a designed sheet maps to the nearest names."""
import json
import pathlib

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
    record, said = look.from_sheet('.mk-card { border: 1px solid #8a8a8a; border-radius: 20px }')
    assert record == {'accent': 'active-color-01', 'radius': 'step-6'}
    assert 'distance 0.04' in said[0]   # the closest one, said with its distance; no new colour


def test_a_colour_goes_to_the_nearest_the_eye_sees_not_the_nearest_number():
    record, _ = look.from_sheet('.mk-card { color: #ffcc99 }')   # by RGB numbers #D5C5AA; as the eye sees it #EFE5C6
    assert sheet.catalog()['colours']['--' + record['accent']] == '#EFE5C6'


def test_type_on_a_part_goes_to_the_nearest_role_and_elsewhere_is_said_dropped():
    record, said = look.from_sheet('.mk-price { font-size: 18px; font-weight: 500; text-transform: uppercase } .wrapper { font-size: 12px }')
    assert record == {'text': {'price': 'callout'}}
    assert any('.wrapper' in s and 'dropped' in s for s in said)


def test_effects_from_the_sheet_s_words():
    assert look.from_sheet('.x { filter: blur(8px); animation: breathe 6s }')[0]['effect'] == 'wellness'
    assert look.from_sheet('.x { animation: jitter 1s steps(1) }')[0]['effect'] == 'glitch'
    assert 'effect' not in look.from_sheet('.mk-card { border-radius: 4px }')[0]


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
