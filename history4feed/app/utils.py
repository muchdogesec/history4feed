from rest_framework import pagination, response, renderers
from rest_framework.filters import OrderingFilter, BaseFilterBackend
from django.utils.encoding import force_str
from django.db.models import Q
from datetime import datetime, UTC
import typing
from dogesec_commons.utils import Pagination, Ordering
from dogesec_commons.utils.filters import MinMaxDateFilter, DatetimeFilter
from django.utils import timezone
from django.forms import DateTimeField
from django_filters.rest_framework import filters

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