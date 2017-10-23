# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import venusian
from pyramid.response import Response

from pyramid_mock_server.mock_loader import load_responses
from pyramid_mock_server.response_collection import ResponseCollection
from pyramid_mock_server.util import make_operation_from_path


def make_response(mock_response):
    """Default endpoint response w/ its corresponding sample json data."""
    return Response(
        mock_response.json_str,
        status=mock_response.http_response_code,
        content_type=str('application/json'),
        charset='UTF-8',
    )


def make_servlet_view_fn(
    endpoint_operation,
    response_collection,
):
    """Create the given endpoint's servlet view function.

    :param endpoint_operation: Operation that will spawn the endpoint
    :param response_collection: ResponseCollection instance.
    :return: a pyramid view function.
    """
    variations = response_collection.get_variations(endpoint_operation)
    if not variations:
        def no_response_found(request):
            raise LookupError(
                u"No json response found for {0} {1}".format(
                    endpoint_operation.response_name,
                    endpoint_operation.http_verb
                )
            )
        return no_response_found

    def custom_view(request):
        arg_list = variations.get_arg_list()
        arg_dict = dict(
            (arg, request.matchdict[arg])
            for arg in arg_list
            if arg in request.matchdict
        )
        arg_dict.update(dict(
            (arg, request.GET[arg]) for arg in arg_list
            for arg in arg_list
            if arg in request.GET
        ))

        matched_mock_response = variations.match_arg_dict(arg_dict)
        return make_response(matched_mock_response)

    return custom_view


def setup_routes_views(
    config,
    responses_path,
    resources,
    custom_view_packages=None,
    excluded_paths=None,
):
    """ Creates the default views when needed, get the custom views, register
    them all in a pyramid config.

    :param config: pyramid config.
    :param responses_path: file path to the root json responses directory.
    :param resources: iterable of (path, method) string tuples.
    :param custom_view_packages: array of packages object that we should load custom view from.
    :param excluded_paths: array of path for which this function should not try to
        register views. Note ['foo'] would also exclude 'foo/whatever'.
    """

    routes_added = set()
    routes_operation_added = set()
    view_registry = {}
    if not excluded_paths:
        excluded_paths = []
    if not custom_view_packages:
        custom_view_packages = []

    responses = load_responses(responses_path)
    response_collections = ResponseCollection(responses)

    for package in custom_view_packages:
        _collect_custom_views(package, view_registry)

    for endpoint_path, http_verb in resources:
        endpoint_operation = make_operation_from_path(endpoint_path, http_verb)

        # Ignore excluded paths/names
        if any(map(endpoint_path.startswith, excluded_paths)):
            continue

        # Only add a route once
        if endpoint_operation.response_name not in routes_added:
            config.add_route(endpoint_operation.response_name, endpoint_path)
            routes_added.add(endpoint_operation.response_name)

        # Only add view once, for each resource
        if endpoint_operation not in routes_operation_added:
            if endpoint_operation not in view_registry:
                view_registry[endpoint_operation] = make_servlet_view_fn(
                    endpoint_operation,
                    response_collections,
                )
            config.add_view(
                view_registry[endpoint_operation],
                route_name=endpoint_operation.response_name,
                request_method=endpoint_operation.http_verb,
            )
            routes_operation_added.add(endpoint_operation)


def register_custom_view(path, http_verb):
    """ Associate the decorated function with the given path.
    This allows for custom views not automatically generated to be used.

        :param path: path as defined in swagger spec
        :param http_verb: http verb ('PUT', 'GET', ...)  for this view
        :return: decorator for the view
    """

    def wrapper(wrapped):
        def callback(scanner, _, ob):
            scanner.view_registry[make_operation_from_path(path, http_verb)] = wrapped
        venusian.attach(wrapped, callback, category='pyramid_mock_server')
        return wrapped

    return wrapper


def _collect_custom_views(package, view_registry):
    """ Collect all the custom views marked with the register_custom_view
    decorator and add them to the view_registry

    :param package: package to look for decorated views into
    :param view_registry: dictionary containing the path-view function pairs
    """
    scanner = venusian.Scanner(view_registry=view_registry)
    scanner.scan(package, categories=('pyramid_mock_server',))
