# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import json

import six
from jinja2 import nodes
from jinja2.ext import Extension


def json_hard_update(base, update):
    result = json.loads(base)
    result.update(json.loads(update))
    return json.dumps(result, sort_keys=True, indent=4)


def _patch(base, patch):
    for key, value in six.iteritems(patch):
        if key in base and type(base[key]) == dict and type(value) == dict:
            _patch(base[key], value)
        else:
            base[key] = value


def json_soft_update(base, update):
    base_json = json.loads(base)
    update_json = json.loads(update)

    _patch(base_json, update_json)

    return json.dumps(base_json, sort_keys=True, indent=4)


class JSONOverrideExtension(Extension):
    """
    Adds an override keyword to the jinja syntax. This allow to update
    2 json dictionaries together.
    Syntax is as follow:

    {% override "template.json" %}
    {
      "attr1": "override"
    }
    {% endoverride %}

    with template.json being a valid template name.

    The override decorated dictionary will update the dictionary defined in the
    passed template
    """
    tags = set(['override'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        filename = parser.stream.expect('string').value

        body = parser.parse_statements(['name:endoverride'], drop_needle=True)

        return nodes.CallBlock(
            self.call_method('_override', [nodes.Const(filename)]),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _override(self, filename, caller=None):
        override_str = caller()
        base_str = self.environment.get_template(filename).render()

        return json_hard_update(base_str, override_str)


class JSONPatchExtension(Extension):
    """
    Adds an patch keyword to the jinja syntax. This allow to update
    2 json dictionaries together.
    Syntax is as follow:

    {% patch "template.json" %}
    {
      "attr1": {
      "value': "override"
      }
    }
    {% endpatch %}

    with template.json being a valid template name.

    All the values that the decorated dictionary defines will be updated in the
    passed template, with respect to hierarchy, and leaving most values as is
    """
    tags = set(['patch'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        filename = parser.stream.expect('string').value

        body = parser.parse_statements(['name:endpatch'], drop_needle=True)

        return nodes.CallBlock(
            self.call_method('_override', [nodes.Const(filename)]),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _override(self, filename, caller=None):
        override_str = caller()
        base_str = self.environment.get_template(filename).render()

        return json_soft_update(base_str, override_str)
