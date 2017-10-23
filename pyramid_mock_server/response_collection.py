# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from collections import Counter
from collections import defaultdict
from itertools import chain

import six

from pyramid_mock_server.util import extract_arg_pattern_from_query_args
from pyramid_mock_server.util import extract_arg_pattern_from_response_name
from pyramid_mock_server.util import norm_operation


class _ResponseVariations(object):
    """ Group the different possible response variations and actually performs
    the matching from the parameters
    """

    def __init__(self, mock_responses=None):
        """ Initialize the instance.
        The optional parameter is here to test this object.

        :param mock_responses: List of mock response names
        """
        self._arg_pattern_by_operation = {}
        self._mock_response_by_operation = {}

        if mock_responses:
            for mock_response in mock_responses:
                self.add_mock_response(mock_response)

    def add_mock_response(self, mock_response):
        arg_pattern = extract_arg_pattern_from_response_name(mock_response.operation.response_name)
        if mock_response.operation.query_args:
            arg_pattern.update(
                extract_arg_pattern_from_query_args(mock_response.operation.query_args)
            )
        self._arg_pattern_by_operation[mock_response.operation] = arg_pattern
        self._mock_response_by_operation[mock_response.operation] = mock_response

    def get_arg_list(self):
        """ Return the list of arguments that is defined by the list of
        filenames put in this object

        :return: list of arguments as an array of strings
        """
        arg_list = {}
        for pattern in six.itervalues(self._arg_pattern_by_operation):
            arg_list.update(pattern)

        return arg_list.keys()

    def generate_string_replacement_dict(self):
        """ Return all the variations as dictionaries that can be used to
        format path strings with the arguments that would lead to call this
        variation

        :return: list of string_replacement dict
        """
        arg_list = self.get_arg_list()
        arg_patterns = self._arg_pattern_by_operation.values()
        default_args_dict = {arg: arg for arg in arg_list}

        string_replacement_dicts = []
        for arg_pattern in arg_patterns:
            string_replacement_dict = default_args_dict.copy()
            string_replacement_dict.update({
                k: v
                for k, v in six.iteritems(arg_pattern) if v
            })
            string_replacement_dicts.append(string_replacement_dict)

        return string_replacement_dicts

    def match_arg_dict(self, arg_dict):
        """ Find the best matching variation for the given argument dictionary

        :param arg_dict: the requests arguments
        :return: best known matching MockResponse
        """

        # If their is only one alternative, return it directly
        if len(self._mock_response_by_operation) == 1:
            return next(six.itervalues(self._mock_response_by_operation))

        # Find the alternative that matches arguments best prioritizing
        # most specific value match over the generic.
        matchs = defaultdict(list)
        for key, value in six.iteritems(arg_dict):
            for operation, pattern in six.iteritems(self._arg_pattern_by_operation):
                if key in pattern and pattern[key] == value:
                    matchs[key].append(operation)

        for key in self.get_arg_list():
            # We only try to match the default pattern if no particular pattern
            # has been found.
            if not matchs[key]:
                for operation, pattern in six.iteritems(self._arg_pattern_by_operation):
                    if pattern.get(key) is None:
                        matchs[key].append(operation)

        # We use Counter to get the most matched name in the previous step
        all_matches = chain.from_iterable(six.itervalues(matchs))
        best_matched_operation = Counter(all_matches).most_common(1)[0][0]
        return self._mock_response_by_operation[best_matched_operation]


class ResponseCollection(object):
    """ Allow to group the different files for the same endpoint by analyzing
    the filename to guess the correct endpoint and the specific arguments for
    which this view should be used
    """

    def __init__(self, mock_responses):
        """
        :param mock_responses: array of read MockResponses
        """
        self._internal_storage = defaultdict(_ResponseVariations)
        for mock_response in mock_responses:
            self.add_mock_response(mock_response)

    def add_mock_response(self, mock_response):
        normed = norm_operation(mock_response.operation)
        self._internal_storage[normed].add_mock_response(mock_response)

    def get_variations(self, response_operation):
        normed_operation = norm_operation(response_operation)
        return self._internal_storage.get(normed_operation, None)
