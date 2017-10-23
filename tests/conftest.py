# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import traceback

import mock
import pytest
from pyramid.config import Configurator
from pyramid.security import NO_PERMISSION_REQUIRED
from webtest import TestApp


# Let's turn off request validation for testing, so we can automagically
# generate tests for every added simple route
@pytest.yield_fixture(scope='session', autouse=True)
def mock_request_validation():
    with mock.patch('pyramid_swagger.tween.swaggerize_request'):
        yield


# Test App
##############################################################################

def _pyramid_and_unhandled_exception_parser(exception, request):
    status_int = getattr(exception, 'code', 500)
    request.response.status_int = status_int
    response = {
        'error': {
            'id': exception.__class__.__name__,
            'status_int': status_int,
            'exception': str(exception),
            'traceback': traceback.format_exc(),
        }
    }
    return response


def _create_application(
    schema_directory,
    responses_directory,
    packages,
    excluded_path
):
    config = Configurator(settings={
        # pyramid_swagger config
        'pyramid_swagger.schema_directory': schema_directory,
        'pyramid_swagger.swagger_versions': ['2.0'],
        'pyramid_swagger.enable_request_validation': True,
        'pyramid_swagger.enable_response_validation': True,

        # pyramid_mock_server config
        'pyramid_mock_server.custom_view_packages': packages,
        'pyramid_mock_server.mock_responses_path': responses_directory,
        'pyramid_mock_server.excluded_paths': excluded_path,
        'pyramid_mock_server.get_resources_from_pyramid_swagger_2_0_schema': True,
    })

    config.include('pyramid_swagger')

    # This should always be included after pyramid_swagger if
    # `read_resources_from_pyramid_swagger` is used
    config.include('pyramid_mock_server')

    config.add_view(
        _pyramid_and_unhandled_exception_parser,
        context=Exception,
        permission=NO_PERMISSION_REQUIRED,
        renderer='json',
    )

    return config.make_wsgi_app()


def create_test_app(
    schema_directory,
    responses_directory,
    packages=None,
    excluded_path=None,
):
    return TestApp(_create_application(
        schema_directory=schema_directory,
        responses_directory=responses_directory,
        packages=packages,
        excluded_path=excluded_path,
    ))
