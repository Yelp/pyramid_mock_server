# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import mock
import pytest
from bravado_core.spec import Spec

from pyramid_mock_server import includeme
from pyramid_mock_server.mock_loader import load_responses
from pyramid_mock_server.response_collection import ResponseCollection
from pyramid_mock_server.swagger_util import get_all_mocks_operations
from pyramid_mock_server.swagger_util import get_swagger20_resources_iterator_from_pyramid_swagger
from pyramid_mock_server.swagger_util import query_url_formatter


def make_spec_from_dict(overrides=None):
    spec_dict = {
        "swagger": "2.0",
        "info": {
            "title": "test",
            "version": "1.0.0"
        },
        "paths": {
            '/pet': {
                'get': {
                    'responses': {
                        '200': {
                            'description': 'Returns a Pet',
                            'schema': {
                                'x-model': 'Pet',
                                'type': 'object',
                                'properties': {
                                    'name': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "definitions": {},
    }

    if overrides:
        spec_dict.update(overrides)

    return Spec.from_dict(spec_dict)


@pytest.mark.parametrize(
    'kwargs, result',
    [
        (dict(foo_id=1), '/foo/1'),
        (dict(foo_id=1, dar_id=32), '/foo/1?dar_id=32'),
    ]
)
def test_query_url_formatter(kwargs, result):
    assert query_url_formatter.format('/foo/{foo_id}', **kwargs) == result


def test_get_all_mocks_operations():
    responses = load_responses('tests/view_maker_test_files/responses')
    collection = ResponseCollection(responses)

    urls = get_all_mocks_operations(
        collection,
        [
            ('/foo', 'GET'),
            ('/foo/{foo_id}/v1', 'POST')
        ]
    )

    assert sorted(urls) == sorted([
        ('/foo/foo_id/v1', 'POST'),
        ('/foo/42/v1', 'POST'),
        ('/foo?limit=limit&offset=offset', 'GET'),
        ('/foo?limit=1&offset=0', 'GET'),
        ('/foo?limit=1&offset=1', 'GET'),
    ])


def test_get_swagger20_resources_iterator_from_pyramid_swagger_no_spec():
    config = mock.Mock(
        registry=mock.Mock(
            settings={},
        )
    )
    with pytest.warns(None) as record:
        list(get_swagger20_resources_iterator_from_pyramid_swagger(config))

    assert len(record) == 1
    assert str(record[0].message) == 'read_resources_from_pyramid_swagger is True but pyramid_swagger is not available'  # noqa


@pytest.mark.parametrize(
    'spec_dict_overrides, result',
    [
        (None, [('/pet', 'get')]),
        ({'basePath': '/base_path'}, [('/base_path/pet', 'get')]),
    ]
)
def test_get_swagger20_resources_iterator_from_pyramid_swagger(spec_dict_overrides, result):
    config = mock.Mock(
        registry=mock.Mock(
            settings={
                'pyramid_swagger.schema20': make_spec_from_dict(spec_dict_overrides),
            },
        )
    )

    with pytest.warns(None):
        resources = list(get_swagger20_resources_iterator_from_pyramid_swagger(config))

    assert resources == result


def test_includeme():
    config = mock.Mock(
        registry=mock.Mock(
            settings={},
        )
    )
    with mock.patch('pyramid_mock_server.setup_routes_views') as mock_setup_routes_views:
        includeme(config)

    mock_setup_routes_views.assert_called_once_with(
        config=config,
        responses_path=None,
        resources=[],
        excluded_paths=None,
        custom_view_packages=None,
    )
