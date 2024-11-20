from drf_spectacular.openapi import AutoSchema
from rest_framework.serializers import Serializer
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.core import exceptions
from dogesec_commons.utils.autoschema import CustomAutoSchema

class H4FSchema(CustomAutoSchema):
    def _is_list_view(self, serializer: Serializer | type[Serializer] | None = None) -> bool:
        if self.path.endswith("/xml/"):
            return True
        return super()._is_list_view(serializer)