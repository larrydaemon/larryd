"""THE TWO LISTS OF THE OUTSIDE HAND ARE ONE: the developer's larryd/shape.py MAKES (what the doctor accepts) names exactly the runtime's
server/runtime/app/core_engine/outside.py MODELS, each with the same choices (a model or a choice on one list only is a doctor that passes
what the runtime refuses, or the reverse: item 19's size was missing here until this test)."""
import importlib.util
import pathlib

from larryd import shape

OUTSIDE = pathlib.Path(__file__).resolve().parent.parent / 'server' / 'runtime' / 'app' / 'core_engine' / 'outside.py'


def _runtime_models():
    spec = importlib.util.spec_from_file_location('runtime_outside', OUTSIDE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # stdlib only: no runtime start, no network
    return module.MODELS


def test_the_same_models_with_the_same_choices():
    models = _runtime_models()
    assert sorted(shape.MAKES) == sorted(models)
    for name, (_what, provider, choices) in shape.MAKES.items():
        assert {k: tuple(v) for k, v in choices.items()} == {k: tuple(v) for k, v in models[name]['choices'].items()}, name
        assert provider == {'replicate': 'Replicate'}[models[name]['provider']], name
