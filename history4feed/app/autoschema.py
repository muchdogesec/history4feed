from drf_spectacular.openapi import AutoSchema
from rest_framework.serializers import Serializer


class H4FSchema(AutoSchema):
    def _is_list_view(self, serializer: Serializer | type[Serializer] | None = None) -> bool:
        if self.path.endswith("/xml/"):
            return True
        return super()._is_list_view(serializer)