# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import os
from collections import namedtuple

import jinja2

from pyramid_mock_server.jinja_utils import JSONOverrideExtension
from pyramid_mock_server.jinja_utils import JSONPatchExtension
from pyramid_mock_server.util import extract_operation_and_response_code_from_filename


MockResponse = namedtuple(
    'MockResponse',
    [
        'operation',
        'json_str',
        'http_response_code',
    ],
)


def _make_json_template_loader(mock_responses_directory):
    """ Generate a rendering function that uses jinja in the context of mock_responses_directory
        to render json files.

        :param: mock_responses_directory: path to root responses directory
        :return: loader function, that take a path of the json file one wants to load and returns
            a rendered json string
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(mock_responses_directory),
        extensions=[JSONOverrideExtension, JSONPatchExtension]
    )

    def _load_json_template(filepath):
        template_filepath = os.path.relpath(
            filepath,
            start=mock_responses_directory,
        )
        return env.get_template(template_filepath).render()

    return _load_json_template


def load_responses(mock_responses_directory):
    """ Load all sample json files in the given directory that match the naming pattern, ignoring
        all others.

        :param: mock_responses_directory: path to root responses directory
        :return: array of MockResponse
    """
    mock_responses = []
    load_json_template_fn = _make_json_template_loader(mock_responses_directory)

    for root, _, files in os.walk(mock_responses_directory):
        for filename in files:
            response_name, ext = os.path.splitext(filename)
            if ext != ".json":
                continue

            json_filepath = os.path.join(root, filename)
            json_str = load_json_template_fn(json_filepath)

            operation, response_code = extract_operation_and_response_code_from_filename(
                response_name
            )

            if operation is not None and response_code is not None:
                mock_responses.append(MockResponse(
                    operation=operation,
                    json_str=json_str,
                    http_response_code=response_code,
                ))

    return mock_responses
