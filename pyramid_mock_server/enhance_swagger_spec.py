# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import json
import os
import sys
from argparse import ArgumentParser
from copy import deepcopy

from bravado_core.spec import Spec
from pyramid.config import Configurator
from webtest import AppError
from webtest import TestApp


def _mock_server_app(swagger_spec_path, mock_responses_path, custom_view_packages):
    """Create the WSGI application, post-fork."""

    # Create a basic pyramid Configurator.
    config = Configurator(settings={
        'service_name': 'mobile_api_mock_server',

        'pyramid_swagger.dereference_served_schema': True,
        'pyramid_swagger.schema_directory': os.path.abspath(os.path.dirname(swagger_spec_path)),
        'pyramid_swagger.schema_file': os.path.basename(swagger_spec_path),
        'pyramid_swagger.swagger_versions': ['2.0'],
        'pyramid_swagger.enable_request_validation': False,
        'pyramid_swagger.enable_response_validation': True,

        # pyramid_mock_server config
        'pyramid_mock_server.mock_responses_path': mock_responses_path,
        'pyramid_mock_server.get_resources_from_pyramid_swagger_2_0_schema': True,
        'pyramid_mock_server.custom_view_packages': custom_view_packages or [],
    })

    config.include('pyramid_mock_server')

    return TestApp(config.make_wsgi_app())


def _bravado_core_spec(mock_server_app):
    # This is based on "internal" details of bravado_core
    # It could be replaced with
    #     Spec.from_dict(mock_app.request('/swagger.json', method='GET', status=200).json)
    return mock_server_app.app.registry.settings['pyramid_swagger.schema20']


def _insert_examples_in_flattened_specs(mock_server_app, bravado_core_spec):
    flattened_spec = deepcopy(bravado_core_spec.flattened_spec)

    for path, path_item_object in flattened_spec.get('paths', {}).items():
        for operation_key, operation_object in path_item_object.items():
            if (  # pragma: no branch
                operation_key not in {'get', 'put', 'post', 'delete', 'options', 'head'} or
                '200' not in operation_object['responses'] or
                'examples' in operation_object['responses']['200']
            ):
                continue  # pragma: no cover

            try:
                mock_response = mock_server_app.request(path, method=operation_key.upper())
                content_type = mock_response.headers.get('content-type')

                ok_response = operation_object['responses']['200']
                ok_response['examples'] = {
                    content_type: mock_response.json
                    if content_type == 'application/json'
                    else mock_response.body.decode('utf-8')
                }
            except (AppError, LookupError) as e:
                # Exception returned by a view or mock response not defined
                print(
                    'Exception while extracting example for {} {}: {}'.format(
                        operation_key.upper(), path, e),
                    file=sys.stderr,
                )
                pass

    return flattened_spec


def main(argv=None):
    parser = ArgumentParser(
        description='Tool to introduce HTTP/200 mock responses into response examples',
    )

    parser.add_argument('-c', '--custom-views', nargs='*', dest='custom_view')  # FIXME
    parser.add_argument('swagger_spec', help='Path of the swagger-specs')
    parser.add_argument('mock_responses', help='Path of the pyramid-mock-server mock responses')

    parser.add_argument('-o', '--output', help='Output file. If not set stdout will be used')
    parser.add_argument(
        '--ignore-validation',
        dest='ignore_validation',
        action='store_true',
        default=False,
        help='By default the generated specs are validated to ensure that they '
             'could be used in clientlibs',
    )
    args = parser.parse_args(argv)

    mock_server_app = _mock_server_app(
        args.swagger_spec,
        args.mock_responses,
        args.custom_view,
    )
    bravado_core_spec = _bravado_core_spec(mock_server_app)
    flattened_enhanced_specs = _insert_examples_in_flattened_specs(
        mock_server_app=mock_server_app, bravado_core_spec=bravado_core_spec,
    )

    if not args.ignore_validation:
        # If specs are invalid this is going to throw an exception
        # NOTE: Spec.from_dict alters the input specs, so we need to copy them
        Spec.from_dict(deepcopy(flattened_enhanced_specs))

    if not args.output:
        print(json.dumps(flattened_enhanced_specs, sort_keys=True, indent=2))
    else:
        with open(args.output, 'w') as f:
            json.dump(flattened_enhanced_specs, f, sort_keys=True, indent=2)

    return 0


if __name__ == '__main__':  # pragma: no cover
    exit(main())
