# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import sys

import pytest
from .conftest import create_test_app
from pyramid.response import Response

from pyramid_mock_server.view_maker import register_custom_view


@pytest.fixture(
    scope='session',
    params=[True, False],
    ids=['custom_view_packages_as_string', 'custom_view_packages_as_python_module'],
)
def mock_app(request):
    custom_view_packages = __name__
    if not request.param:
        custom_view_packages = sys.modules[custom_view_packages]

    return create_test_app(
        'tests/view_maker_test_files',
        'tests/view_maker_test_files/responses',
        packages=[custom_view_packages],
    )


@pytest.fixture(scope='session')
def mock_app_exclude():
    return create_test_app(
        'tests/view_maker_test_files',
        'tests/view_maker_test_files/responses',
        packages=None,
        excluded_path=['/exclude_me'],
    )


@register_custom_view('/foo/bar', 'POST')
def custom_view(request):
    return Response(
        '{"message":"lloll"}',
        content_type=str('application/json'),
        charset='UTF-8',
    )


@pytest.mark.parametrize(
    'path, request_method, message, status',
    [
        (
            '/foo',
            'GET',
            'You got foo',
            200,
        ),
        (
            '/foo?offset=0&limit=1',
            'GET',
            'You got foo offset 0 limit 1',
            200,
        ),
        (
            '/foo?offset=1&limit=1',
            'GET',
            'You got foo offset 1 limit 1',
            200,
        ),
        (
            '/foo/bar',
            'POST',
            'lloll',
            200,
        ),
        (
            '/exclude_me',
            'GET',
            'I am not excluded yet',
            200,
        ),
        (
            '/exclude_me/am_i_excluded',
            'GET',
            'I am not excluded yet, am i?',
            200,
        ),
        (
            '/foo/something/v1',
            'GET',
            'default/get',
            200,
        ),
        (
            '/foo/404/v1',
            'GET',
            '404/get',
            404,
        ),
        (
            '/foo/something/v1',
            'POST',
            'default/post',
            200,
        ),
        (
            '/foo/42/v1',
            'POST',
            '42',
            200,
        ),
    ],
)
def test_setup_routes_views(mock_app, path, request_method, message, status):
    result = mock_app.request(path, method=request_method, status=status)
    assert result.json['message'] == message


@pytest.mark.parametrize(
    'path, request_method, exception',
    [
        (
            '/foo/bar',
            'POST',
            'No json response found for foo_bar POST',
        ),
    ],
)
def test_not_found(mock_app_exclude, path, request_method, exception):
    result = mock_app_exclude.request(path, method=request_method, status=500)
    assert result.json['error']['exception'] == exception


@pytest.mark.parametrize(
    'path, request_method',
    [
        (
            '/exclude_me',
            'GET',
        ),
        (
            '/exclude_me/am_i_excluded',
            'GET',
        ),
    ],
)
def test_excluded(mock_app_exclude, path, request_method):
    mock_app_exclude.request(path, method=request_method, status=404)
