# -*- coding: utf-8 -*-
"""
Import this module to add the mocks views to your pyramid app.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from pyramid_mock_server.swagger_util import get_swagger20_resources_iterator_from_pyramid_swagger
from pyramid_mock_server.view_maker import setup_routes_views


def includeme(config):
    """
    :type config: :class:`pyramid.config.Configurator`
    """
    settings = config.registry.settings

    custom_view_packages = settings.get('pyramid_mock_server.custom_view_packages')
    responses_path = settings.get('pyramid_mock_server.mock_responses_path')
    excluded_paths = settings.get('pyramid_mock_server.excluded_paths')

    # Read resources:
    resources = settings.get('pyramid_mock_server.resources', [])

    # Read resources from pyramid_swagger
    if settings.get('pyramid_mock_server.get_resources_from_pyramid_swagger_2_0_schema', False):
        for resource in get_swagger20_resources_iterator_from_pyramid_swagger(config):
            resources.append(resource)

    setup_routes_views(
        config=config,
        responses_path=responses_path,
        resources=resources,
        excluded_paths=excluded_paths,
        custom_view_packages=custom_view_packages,
    )
