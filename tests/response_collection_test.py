# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from pyramid_mock_server.mock_loader import MockResponse
from pyramid_mock_server.response_collection import _ResponseVariations
from pyramid_mock_server.response_collection import ResponseCollection
from pyramid_mock_server.util import Operation


def _make_mock_response(response_name, http_verb, query_args=None):
    return MockResponse(Operation(response_name, http_verb, query_args=query_args), "", 0)


response_variations_foo_bar = [
    _make_mock_response('foo_{foo_id}_bar_{bar_id}', 'GET'),
    _make_mock_response('foo_{foo_id}_bar_{bar_id#33}', 'GET'),
    _make_mock_response('foo_{foo_id#bar}_bar_{bar_id#33}', 'GET'),
    _make_mock_response('foo_{foo_id#bar}_bar_{bar_id#33}', 'GET'),
    _make_mock_response('foo_{foo_id#bar}_bar_{bar_id}', 'GET'),
    _make_mock_response('foo_{foo_id}_bar_{bar_id}', 'GET', query_args='{dar_id#dar}'),
    _make_mock_response(
        'foo_{foo_id#foo_dar}_bar_{bar_id#bar_dar}',
        'GET',
        query_args='{dar_id#dar}',
    ),
    _make_mock_response(
        'foo_{foo_id#foo_dar}_bar_{bar_id#bar_dar}',
        'GET',
        query_args='{dar_id#dar_2}',
    ),
]
response_collection_foo = [
    _make_mock_response('foo_{foo_id#32}', 'GET'),
    _make_mock_response('foo_{foo_id#33}', 'GET'),
    _make_mock_response('foo_{foo_id#32}', 'POST'),
    _make_mock_response('foo_{foo_id#33}', 'PUT'),
]


@pytest.mark.parametrize(
    'mock_responses, arg_list',
    [
        (
            response_variations_foo_bar,
            ['foo_id', 'bar_id', 'dar_id'],
        ),
        (
            [_make_mock_response('foo_{foo_id#32}', 'GET')],
            ['foo_id'],
        ),
    ],
)
def test_get_arg_list(mock_responses, arg_list):
    variations = _ResponseVariations(mock_responses=mock_responses)
    assert sorted(variations.get_arg_list()) == sorted(arg_list)


@pytest.mark.parametrize(
    'mock_responses, replacement_dict',
    [
        (
            response_variations_foo_bar,
            [
                {
                    'foo_id': 'foo_id',
                    'bar_id': 'bar_id',
                    'dar_id': 'dar_id',
                },
                {
                    'foo_id': 'foo_id',
                    'bar_id': '33',
                    'dar_id': 'dar_id',
                },
                {
                    'foo_id': 'bar',
                    'bar_id': '33',
                    'dar_id': 'dar_id',
                },
                {
                    'foo_id': 'bar',
                    'bar_id': 'bar_id',
                    'dar_id': 'dar_id',
                },
                {
                    'foo_id': 'foo_id',
                    'bar_id': 'bar_id',
                    'dar_id': 'dar',
                },
                {
                    'foo_id': 'foo_dar',
                    'bar_id': 'bar_dar',
                    'dar_id': 'dar',
                },
                {
                    'foo_id': 'foo_dar',
                    'bar_id': 'bar_dar',
                    'dar_id': 'dar_2',
                },
            ]

        ),
        (
            [_make_mock_response('foo_{foo_id#32}', 'GET')],
            [
                {
                    'foo_id': '32',
                },
            ],
        ),
    ],
)
def test_generate_string_replacement_dict(mock_responses, replacement_dict):
    def _sort(dict_list):
        return sorted(sorted(d.items()) for d in dict_list)

    variations = _ResponseVariations(mock_responses=mock_responses)
    assert _sort(variations.generate_string_replacement_dict()) == _sort(replacement_dict)


@pytest.mark.parametrize(
    'mock_responses, arg_dict, output',
    [
        (
            response_variations_foo_bar,
            {'foo_id': 'troll', 'bar_id': None},
            Operation('foo_{foo_id}_bar_{bar_id}', 'GET'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': None, 'bar_id': '33'},
            Operation('foo_{foo_id}_bar_{bar_id#33}', 'GET'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': None, 'bar_id': '34'},
            Operation('foo_{foo_id}_bar_{bar_id}', 'GET'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': 'bar', 'bar_id': '34'},
            Operation('foo_{foo_id#bar}_bar_{bar_id}', 'GET'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': 'bar', 'bar_id': '33'},
            Operation('foo_{foo_id#bar}_bar_{bar_id#33}', 'GET'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': 'x', 'bar_id': 'x', 'dar_id': 'dar'},
            Operation('foo_{foo_id}_bar_{bar_id}', 'GET', query_args='{dar_id#dar}'),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': 'foo_dar', 'bar_id': 'bar_dar', 'dar_id': 'dar'},
            Operation(
                'foo_{foo_id#foo_dar}_bar_{bar_id#bar_dar}',
                'GET',
                query_args='{dar_id#dar}',
            ),
        ),
        (
            response_variations_foo_bar,
            {'foo_id': 'foo_dar', 'bar_id': 'bar_dar', 'dar_id': 'dar_2'},
            Operation(
                'foo_{foo_id#foo_dar}_bar_{bar_id#bar_dar}',
                'GET',
                query_args='{dar_id#dar_2}',
            ),
        ),
        # Test the one variation case (with an exotic http verb)
        (
            [_make_mock_response('foo_{foo_id#32}', 'PUT')],
            {'foo_id': 12},
            Operation('foo_{foo_id#32}', 'PUT'),
        ),
    ],
)
def test_match_arg_dict(mock_responses, arg_dict, output):
    variations = _ResponseVariations(mock_responses=mock_responses)
    assert variations.match_arg_dict(arg_dict).operation == output


@pytest.mark.parametrize(
    'response_names, response_operation, has_variation',
    [
        (
            response_variations_foo_bar + response_collection_foo,
            Operation('bar_{bar_id}_foo_{foo_id}', 'GET'),
            False,
        ),
        (
            response_variations_foo_bar + response_collection_foo,
            Operation('foo_{foo_id}_bar_{bar_id#32}', 'GET'),
            True,
        ),
        (
            response_variations_foo_bar + response_collection_foo,
            Operation('foo_{foo_id}', 'PUT'),
            True,
        ),
    ]
)
def test_response_collection(response_names, response_operation, has_variation):
    collection = ResponseCollection(mock_responses=response_names)
    assert (collection.get_variations(response_operation) is None) != has_variation
