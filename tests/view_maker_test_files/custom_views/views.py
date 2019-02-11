# -*- coding: utf-8 -*-
from json import JSONEncoder

from pyramid.response import Response

from pyramid_mock_server.view_maker import register_custom_view


@register_custom_view('/mock/via/custom/view', 'GET')
def mock_via_custom_view(request):
    return Response(
        body=JSONEncoder().encode({
            'message': 'Message from custom view',
        }),
        content_type='application/json',
        charset='UTF-8',
    )
