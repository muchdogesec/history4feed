from rest_framework import pagination, response, renderers
from rest_framework.filters import OrderingFilter, BaseFilterBackend
from django.utils.encoding import force_str
from django.db.models import Q
from datetime import datetime, UTC
import typing
from dogesec_commons.utils import Pagination, Ordering
from django.utils import timezone
from django.forms import DateTimeField
from django_filters.rest_framework import filters

class DatetimeFieldUTC(DateTimeField):
    def to_python(self, value):
        value = super().to_python(value) 
        return value and value.astimezone(UTC)
    
class DatetimeFilter(filters.Filter):
    field_class = DatetimeFieldUTC

class MinMaxDateFilter(BaseFilterBackend):
    min_val = datetime.min
    max_value = datetime.max
    def get_fields(self, view):
        out = {}
        fields = getattr(view, 'minmax_date_fields', [])
        if not isinstance(fields, list):
            return out
        for field in fields:
            out[f"{field}_max"] = field
            out[f"{field}_min"] = field
        return out
    
    def parse_date(self, value):
        return DatetimeFieldUTC().to_python(value)

    def filter_queryset(self, request, queryset, view):
        valid_fields = self.get_fields(view)
        valid_params = [(k, v) for k, v in request.query_params.items() if k in valid_fields]
        queries =  {}
        for param, value in valid_params:
            field_name = valid_fields[param]
            if param.endswith('_max'):
                queries[f"{field_name}__lte"] = self.parse_date(value)
            else:
                queries[f"{field_name}__gte"] = self.parse_date(value)
        return queryset.filter(**queries)

    def get_schema_operation_parameters(self, view):
        parameters = []
        valid_fields = self.get_fields(view)
        for query_name, field_name in valid_fields.items():
            _type = "Maximum"
            if query_name.endswith('min'):
                _type = "Minimum"
            parameter = {
                'name': query_name,
                'required': False,
                'in': 'query',
                'description': f"{_type} value of `{field_name}` to filter by in format `YYYY-MM-DD`.",
                'schema': {
                    'type': 'string', 'format': 'date',
                },
            }
            parameters.append(parameter)
        return parameters



# use pagination to modify how xml/rss renders
class XMLPostPagination(Pagination):
    def get_paginated_response_schema(self, schema):
        return {
            'type': 'string',
            'example': '<?xml version="1.0" ?>'
        }
    
    def get_paginated_response(self, data):
        return response.Response(data, headers={
            'rss_page_size': self.get_page_size(self.request),
            'rss_page_number': self.page.number,
            'rss_page_results_count': len(self.page),
            'rss_total_results_count': self.page.paginator.count,
        }, content_type="application/rss+xml; charset=UTF-8")
    
    def get_schema_operation_parameters(self, view):
        return super().get_schema_operation_parameters(view)

class RSSRenderer(renderers.BaseRenderer):
    media_type = "application/rss+xml"
    format = "xml"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data