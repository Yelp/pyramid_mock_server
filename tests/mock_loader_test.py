# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import json

from pyramid_mock_server.mock_loader import _make_json_template_loader
from pyramid_mock_server.mock_loader import load_responses
from pyramid_mock_server.mock_loader import MockResponse
from pyramid_mock_server.util import Operation


def test_load_responses():
    responses = load_responses(
        'tests/mock_loader_test_responses'
    )
    assert sorted(responses) == sorted([
        MockResponse(Operation('level0', 'GET'), '', 200),
        MockResponse(Operation('level1', 'GET'), '', 200),
        MockResponse(Operation('level2', 'GET'), '', 200),
    ])


def test_make_json_template_loader():
    loader = _make_json_template_loader(
        'tests/jinja_templating_test_files',
    )
    base = {
        'value': 0,
        'attr1': {
            'value': 1,
            'attr2': {
                'value': 2,
            }
        }
    }
    assert json.loads(
        loader('tests/jinja_templating_test_files/base.json')
    ) == base
    assert json.loads(
        loader('tests/jinja_templating_test_files/include.json')
    ) == {
        'base': base
    }
    assert json.loads(
        loader('tests/jinja_templating_test_files/override.json')
    ) == {
        'value': 0,
        'attr1': 'override'
    }
    assert json.loads(
        loader('tests/jinja_templating_test_files/patch.json')
    ) == {
        'extra': 'extra',
        'value': "patch",
        'attr1': {
            'value': 1,
            'attr2': {
                'value': 'patch',
            }
        }
    }
