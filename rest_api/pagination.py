from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from collections import OrderedDict


class CustomPagination(LimitOffsetPagination):

    min_limit = 1
    max_limit = 250
    # min_offset = 0
    # max_offset = 10000

    def get_paginated_response(self, data):
        ''' Customise the head of the pagination response '''
        return Response(OrderedDict([
            ('size', len(data)),
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


    def paginate_queryset(self, queryset, request, view=None):
        ''' Set a maximum value (limit) on the number of results returned per page '''
        limit = request.query_params.get('limit')
        if limit:
            limit = int(limit)
            error_msg = None
            error_dict = {}
            if limit > self.max_limit:
                error_msg = f'URL parameter \'limit\' should be less than or equal to {self.max_limit}'
            elif limit < self.min_limit:
                error_msg = f'URL parameter \'limit\' should be greater than or equal to {self.min_limit}'
            if error_msg:
                error_dict['limit'] = error_msg
                raise ValidationError(error_dict)

        #offset = request.query_params.get('offset')
        # if offset:
        #     offset = int(offset)
        #     if offset > self.max_offset:
        #         raise serializers.ValidationError({"offset" : ["URL parameter \'offset\' should be less than or equal to {0}".format(self.max_offset)]})
        #     elif offset < self.min_offset:
        #         raise serializers.ValidationError({"offset" : ["URL parameter \'offset\' should be greater than or equal to {0}".format(self.min_offset)]})

        return super(self.__class__, self).paginate_queryset(queryset, request, view)
