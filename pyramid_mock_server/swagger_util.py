# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import string
import warnings

import six
from six.moves.urllib.parse import urlencode

from pyramid_mock_server.util import make_operation_from_path


class QueryUrlFormatter(string.Formatter):
    """ Appends unused kwargs at the end as query_urls
    """

    def format(self, format_string, *args, **kwargs):
        formated_str = super(QueryUrlFormatter, self).format(format_string, *args, **kwargs)
        if self.unused_kwargs:
            return '?'.join((formated_str, urlencode(self.unused_kwargs)))

        return formated_str

    def check_unused_args(self, used_args, args, kwargs):
        self.unused_kwargs = collections.OrderedDict(sorted(kwargs.items()))
        for arg in used_args:
            self.unused_kwargs.pop(arg, None)


query_url_formatter = QueryUrlFormatter()


def get_all_mocks_operations(response_collection, resources):
    """ Return all the urls/http_operation pairs that the mocks are
    defining.
    This is useful for testing all the mocks against a spec for example.

    :param response_collection: ResponseCollection of all mocks
    :param resources: iterable of (path, method) pairs
    """

    operations = []

    for endpoint_path, endpoint_method in resources:
        operation = make_operation_from_path(endpoint_path, endpoint_method)
        variations = response_collection.get_variations(operation)
        replacement_dicts = variations.generate_string_replacement_dict()

        for replacement_dict in replacement_dicts:
            operations.append((
                query_url_formatter.format(
                    endpoint_path,
                    **replacement_dict
                ),
                endpoint_method,
            ))

    return operations


def get_swagger20_resources_iterator_from_pyramid_swagger(config):
    """ Extract the swagger2.0 defined path from a pyramid swagger configuration

    Only call this after `config.include('pyramid_swagger')`

    :param config: the pyramid config
    :return: an iterator over the swagger resources yielding (path, http_verb) tuples
    """
    swagger_schema = config.registry.settings.get('pyramid_swagger.schema20')
    if not swagger_schema:
        warnings.warn(
            'read_resources_from_pyramid_swagger is True but pyramid_swagger is not available'
        )
    else:
        base_path = swagger_schema.spec_dict.get('basePath', '').rstrip('/')
        for resource in six.itervalues(swagger_schema.resources):
            for op in six.itervalues(resource.operations):
                yield base_path + op.path_name, op.http_method
