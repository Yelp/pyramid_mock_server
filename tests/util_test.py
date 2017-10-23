# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import mock
import pytest

from pyramid_mock_server.util import check_file_is_valid
from pyramid_mock_server.util import extract_arg_pattern_from_query_args
from pyramid_mock_server.util import extract_arg_pattern_from_response_name
from pyramid_mock_server.util import extract_normalized_response_name
from pyramid_mock_server.util import extract_operation_and_response_code_from_filename
from pyramid_mock_server.util import make_operation_from_path
from pyramid_mock_server.util import norm_operation
from pyramid_mock_server.util import Operation


@pytest.mark.parametrize(
    'filename, result',
    [
        (
            'foo_{business_id#troll}_{mtb_id}',
            'foo_{business_id}_{mtb_id}',
        ),
        (
            'foo_baa_{business_id}_mtb_{mtb_id#33}',
            'foo_baa_{business_id}_mtb_{mtb_id}',
        )
    ],
)
def test_extract_normalized_response_name(filename, result):
    assert extract_normalized_response_name(filename) == result


@pytest.mark.parametrize(
    'filename, result',
    [
        (
            'foo_{business_id#troll}_{mtb_id}',
            {'business_id': 'troll', 'mtb_id': None},
        ),
        (
            'foo_baa_{business_id}_mtb_{mtb_id#33}',
            {'business_id': None, 'mtb_id': '33'},
        ),
    ],
)
def test_extract_arg_pattern_from_response_name(filename, result):
    assert extract_arg_pattern_from_response_name(filename) == result


def test_extract_arg_pattern_from_response_name_raise():
    with pytest.raises(ValueError):
        extract_arg_pattern_from_response_name('foo_{business_id#troll#trall}_{mtb_id}')


@pytest.mark.parametrize(
    'query_args, result',
    [
        (
            '{business_ids#troll,troll2}{gaga#32}',
            {'business_ids': 'troll,troll2', 'gaga': '32'},
        ),
        (
            '{business_ids#troll,troll2}',
            {'business_ids': 'troll,troll2'},
        ),
    ],
)
def test_extract_arg_pattern_from_query_args(query_args, result):
    assert extract_arg_pattern_from_query_args(query_args) == result


@pytest.mark.parametrize(
    'query_args',
    [
        ('{business_ids#troll,troll2}{gaga}',),
        ('{business_ids#troll,troll2}{gaga#2#3}',),
    ],
)
def test_extract_arg_pattern_from_query_args_raise(query_args):
    with pytest.raises(ValueError):
        extract_arg_pattern_from_query_args('foo_{business_id#troll#trall}_{mtb_id}')


@pytest.mark.parametrize(
    'filename, result',
    [
        (
            'foo_{business_id#troll}_{mtb_id}_response.POST',
            (Operation('foo_{business_id#troll}_{mtb_id}', 'POST'), 200)
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.POST',
            (Operation('foo_{business_id}_{mtb_id}', 'POST'), 404)
        ),
        (
            'foo_{business_id}_{mtb_id}.404.POST',
            (None, None)
        ),
        (
            'foo_{business_id}_{mtb_id}.POST.404',
            (None, None)
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.post',
            (None, None)
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.POST.lol',
            (None, None)
        ),
        # query arguments detection
        (
            'foo_{business_id}_{mtb_id}_query{business_id#2,3,4}{mtb_id#1,2,4}_response.404.POST',
            (
                Operation(
                    'foo_{business_id}_{mtb_id}',
                    'POST',
                    query_args='{business_id#2,3,4}{mtb_id#1,2,4}',
                ),
                404,
            )
        ),
        (
            'foo_query_query{business_id#32,33,34}{mtb_id#1,2,4}_response.404.POST',
            (
                Operation(
                    'foo_query',
                    'POST',
                    query_args='{business_id#32,33,34}{mtb_id#1,2,4}',
                ),
                404,
            )
        ),
        (
            'foo_{business_id}_{mtb_id}_query_response.404.POST',
            (Operation('foo_{business_id}_{mtb_id}_query', 'POST'), 404)
        ),
        (
            'foo_{business_id}_{mtb_id}_query{b}_response.404.POST',
            (Operation('foo_{business_id}_{mtb_id}_query{b}', 'POST'), 404)
        ),
    ]
)
def test_extract_operation_and_response_code_from_filename(filename, result):
    assert extract_operation_and_response_code_from_filename(filename) == result


@pytest.mark.parametrize(
    'filename, result',
    [
        (
            'foo_{business_id#troll}_{mtb_id}_response.POST',
            True,
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.POST',
            True,
        ),
        (
            'foo_{business_id}_{mtb_id}.404.POST',
            False,
        ),
        (
            'foo_{business_id}_{mtb_id}.POST.404',
            False,
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.post',
            False,
        ),
        (
            'foo_{business_id}_{mtb_id}_response.404.POST.lol',
            False,
        ),
        (
            'foo_{business_id}_{mtb_id}_query{business_id#2,3,4}{mtb_id#1,2,4}_response.404.POST',
            True,
        ),
        (
            'foo_query_query{business_id#32,33,34}{mtb_id#1,2,4}_response.404.POST',
            True,
        ),
        (
            'foo_{business_id}_{mtb_id}_query_response.404.POST',
            True,
        ),
        (
            'foo_{business_id}_{mtb_id}_query{b}_response.404.POST',
            True,
        ),
    ]
)
def test_check_file_is_valid(filename, result):
    assert check_file_is_valid(filename) is result


@pytest.mark.parametrize(
    'path, http_verb, result',
    [
        ('/foo/bar/', 'post', Operation('foo_bar', 'POST')),
        ('/foo/{foo_id}/bar', 'PUT', Operation('foo_{foo_id}_bar', 'PUT')),
        ('/foo/{foo_id#32}/bar', 'Get', Operation('foo_{foo_id#32}_bar', 'GET')),

    ],
)
def test_make_operation_from_path(path, http_verb, result):
    assert make_operation_from_path(path, http_verb) == result


@pytest.mark.parametrize(
    'operation, result',
    [
        (
            Operation('foo_{business_id#troll}_{mtb_id}', 'Post'),
            Operation('foo_{business_id}_{mtb_id}', 'POST'),
        ),
        (
            Operation('foo_{business_id}_{mtb_id}', 'PUT', '{business_ids#32,32,32}'),
            Operation('foo_{business_id}_{mtb_id}', 'PUT', None),
        ),
    ],
)
def test_norm_operation(operation, result):
    assert norm_operation(operation) == result


def test_norm_operation_use_extract_normalized_response_name():
    with mock.patch(
        'pyramid_mock_server.util.extract_normalized_response_name'
    ) as mocked_normalize:
        norm_operation(Operation('foo_{business_id#12}', 'POST', '{business_ids#32,32,32}'))

    mocked_normalize.assert_called_once_with('foo_{business_id#12}')
