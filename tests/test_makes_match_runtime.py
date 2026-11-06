"""THE TWO LISTS OF THE OUTSIDE HAND ARE ONE: the developer's larryd/shape.py MAKES (what the doctor accepts) names exactly the runtime's
server/runtime/app/core_engine/outside.py MODELS, each with the same choices (a model or a choice on one list only is a doctor that passes
what the runtime refuses, or the reverse: item 19's size was missing here until this test)."""
import importlib.machinery
import importlib.util
import pathlib
import sys

from larryd import shape

OUTSIDE = pathlib.Path(__file__).resolve().parent.parent / 'server' / 'runtime' / 'app' / 'core_engine' / 'outside.py'


def _runtime_models():
    # loaded as its package's module: outside.py builds the Exxact models from its neighbour exxact.py (from . import exxact)
    package = importlib.util.module_from_spec(importlib.machinery.ModuleSpec('runtime_core_engine', None, is_package=True))
    package.__path__ = [str(OUTSIDE.parent)]
    sys.modules.setdefault('runtime_core_engine', package)
    spec = importlib.util.spec_from_file_location('runtime_core_engine.outside', OUTSIDE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # stdlib only: no runtime start, no network
    return module.MODELS


def test_the_same_models_with_the_same_choices():
    models = _runtime_models()
    assert sorted(shape.MAKES) == sorted(models)
    for name, (_what, provider, choices) in shape.MAKES.items():
        assert {k: tuple(v) for k, v in choices.items()} == {k: tuple(v) for k, v in models[name]['choices'].items()}, name
        assert provider == {'replicate': 'Replicate', 'exxact': 'Exxact'}[models[name]['provider']], name


def test_the_same_number_fields_and_the_same_models_without_words():
    models = _runtime_models()
    assert {m: spec['numbers'] for m, spec in models.items() if spec['numbers']} == shape.MAKES_NUMBERS
    assert sorted(m for m, spec in models.items() if not spec['prompt']) == sorted(shape.MAKES_NO_WORDS)


def test_the_doctors_star_words_are_the_runtimes_reviews_aside():
    """THE "*" WORDS ARE ONE LIST too: the doctor's (shape.RECORD_EVERY) are the external runtime's member_records.EVERY_WORDS, "reviews"
    aside (an internal agent's, handed by LARRYD RUNTIME INTERNAL only): a word on one list only is a doctor that passes what the runtime
    hands nothing for (CORE_CLEANUP_IV row 142)."""
    spec = importlib.util.spec_from_file_location('runtime_member_records', OUTSIDE.parent / 'member_records.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # stdlib only
    assert set(shape.RECORD_EVERY[1]) - {'reviews'} == set(module.EVERY_WORDS)
