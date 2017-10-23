# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import re


def extract_normalized_response_name(response_name):
    """ Remove custom parameters from a response file name.
        E.G.
        "bar_{business_id#foo}_{mtb_id}" -> "bar_{business_id}_{mtb_id}"

        :param response_name: a json mock response filename
        :return: cleaned-up response name
    """
    return re.sub(r'{(\w+)(?:#\w+)?}', r'{\1}', response_name)


def extract_arg_pattern_from_response_name(response_name):
    """ Extract the argument pattern from a filename.
        This will be used to perform view matching

        :param response_name: a json mock response filename
        :return: argument pattern, a dictionary containing the arguments
            defined by the file name and their value (or None)
    """
    arguments = re.findall(r'{(.+?)}', response_name)
    args_pattern = {}

    for argument in arguments:
        splits = re.split(r'#', argument)
        if len(splits) == 1:
            param = splits[0]
            value = None
        elif len(splits) == 2:
            param = splits[0]
            value = splits[1]
        else:
            raise ValueError(
                "{0} has too many arguments".format(response_name)
            )

        args_pattern[param] = value

    return args_pattern


def extract_arg_pattern_from_query_args(query_args):
    """ Extract the argument pattern from query_args

        :param query_args:
        :return: argument pattern, a dictionary containing the arguments
            defined by the file name and their valu
    """
    arguments = re.findall(r'{(.+?)}', query_args)
    args_pattern = {}

    for argument in arguments:
        splits = re.split(r'#', argument)
        if len(splits) == 2:
            param = splits[0]
            value = splits[1]
        else:
            raise ValueError(
                "Query is not correctly defined/extracted: {0}".format(query_args)
            )

        args_pattern[param] = value

    return args_pattern


class Operation(collections.namedtuple(
    'OperationBase', ['response_name', 'http_verb', 'query_args']
)):
    def __new__(cls, response_name, http_verb, query_args=None):
        return super(Operation, cls).__new__(
            cls,
            response_name=response_name,
            http_verb=http_verb,
            query_args=query_args,
        )


def make_operation_from_path(path, http_verb):
    """ Make an operation from a url path and the associated http_verb

    Sample result:
    '/foo/bar/', 'GET'
        -> Operation('foo_bar', 'GET')

    :param path: url path
    :param http_verb: POST, PUT, GET ...
    :return: (response_name, http_verb) tuple
    """
    name = path.strip('/').replace('/', '_')
    return Operation(name, http_verb.upper())


def _filename_regex_match(filename):
    """ Main function to match filename with the core regex to extract all the information from
     the file names

    :param filename: the name of the response file, without extension
    :return: re.MatchObject or None if the filename is not valid
    """
    return re.match(
        r'^(?P<response_name>.+?)(_query(?P<query_args>(?:{[^{}#]+#[^{}#]+})+))?_response\.(?:(?P<http_code>\d+)\.)?(?P<http_verb>[A-Z]+)$',  # noqa
        filename,
    )


def extract_operation_and_response_code_from_filename(filename):
    """ Extract from the filename, the operation (name + http verb) and eventual
    response http code defaulting to 200 if absent.

    Sample result:
    'foo_{foo_id#404}_v1_response.404.GET'
        -> Operation('foo_{foo_id#404}_v1', 'GET'), 404

    :param filename: the name of the response file, without extension
    :return: (response_name, http_verb) tuple and http_code int, or (None, None) if unvalid
    """
    match = _filename_regex_match(filename)
    if match:
        response_name = match.group('response_name')
        http_verb = match.group('http_verb')
        http_code = match.group('http_code') or 200
        http_code = int(http_code)
        query_args = match.group('query_args')

        return Operation(response_name, http_verb, query_args=query_args), http_code
    else:
        return None, None


def check_file_is_valid(filename):
    """

    :param filename: the name of the response file, without extension
    :return: True if filename is a valid mock file
    """
    return _filename_regex_match(filename) is not None


def norm_operation(operation):
    """ Return a normalized version of an operation, where the name is
    normalized, http_verb is standardized and query arguments are removed

    :param operation: Operation
    :return: normalized operation
    """
    normed_name = extract_normalized_response_name(operation.response_name)
    return Operation(normed_name, operation.http_verb.upper(), query_args=None)
