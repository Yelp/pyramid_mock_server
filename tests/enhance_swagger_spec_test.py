# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import json

import mock
import pytest

from pyramid_mock_server.enhance_swagger_spec import main


@pytest.fixture
def expected_enhances_specs():
    with open('tests/view_maker_test_files/enhanced_swagger.json') as f:
        return json.load(f)


def test_enhance_specs_without_custom_views(capsys, expected_enhances_specs):
    assert main([
        'tests/view_maker_test_files/swagger.json',
        'tests/view_maker_test_files/responses',
    ]) == 0

    stdout, _ = capsys.readouterr()
    expected_enhances_specs['paths']['/mock/via/custom/view']['get']['responses']['200'].pop(
        'examples', None,
    )
    assert expected_enhances_specs == json.loads(stdout)


def test_enhance_specs_with_custom_views(capsys, expected_enhances_specs):
    assert main([
        '-c',
        'tests/view_maker_test_files/custom_views',
        '--',
        'tests/view_maker_test_files/swagger.json',
        'tests/view_maker_test_files/responses',
    ]) == 0

    stdout, _ = capsys.readouterr()
    assert expected_enhances_specs == json.loads(stdout)


def test_enhance_specs_save_on_file(tmpdir, expected_enhances_specs):
    output_path = '{}/enhanced_swagger.json'.format(tmpdir.strpath)
    assert main([
        '-c',
        'tests/view_maker_test_files/custom_views',
        '-o',
        output_path,
        '--',
        'tests/view_maker_test_files/swagger.json',
        'tests/view_maker_test_files/responses',
    ]) == 0

    with open(output_path) as f:
        assert expected_enhances_specs == json.load(f)


@pytest.mark.parametrize('ignore_validation', [True, False])
@mock.patch('pyramid_mock_server.enhance_swagger_spec.Spec', autospec=True)
def test_enhance_specs_validation(mock_Spec, capsys, ignore_validation):
    assert main((['--ignore-validation'] if ignore_validation else []) + [
        'tests/view_maker_test_files/swagger.json',
        'tests/view_maker_test_files/responses',
    ]) == 0
    stdout, _ = capsys.readouterr()

    if ignore_validation:
        assert not mock_Spec.from_dict.called
    else:
        mock_Spec.from_dict.assert_called_once_with(json.loads(stdout))
