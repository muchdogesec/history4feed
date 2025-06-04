import pytest
from unittest.mock import MagicMock
from datetime import datetime
from django.utils.timezone import make_aware
from history4feed.app.utils import MinMaxDateFilter



def test_filter_queryset_with_minmax_dates():
    filter_backend = MinMaxDateFilter()
    mock_view = MagicMock()
    mock_view.minmax_date_fields = ["created", "modified"]

    mock_request = MagicMock()
    mock_request.query_params = {
        "created_min": "2024-01-01T00:00:00Z",
        "created_max": "2024-01-05T00:00:00Z",
    }

    mock_qs = MagicMock()
    filtered_qs = MagicMock()
    mock_qs.filter.return_value = filtered_qs

    expected_gte = make_aware(datetime(2024, 1, 1, 0, 0))
    expected_lte = make_aware(datetime(2024, 1, 5, 0, 0))

    result = filter_backend.filter_queryset(mock_request, mock_qs, mock_view)

    assert result == filtered_qs

    mock_qs.filter.assert_called_once_with(
        created__gte=expected_gte,
        created__lte=expected_lte,
    )

    mock_request.query_params = {
        "created_max": "2024-01-05T00:00:00Z",
    }
    mock_qs.filter.reset_mock()
    result = filter_backend.filter_queryset(mock_request, mock_qs, mock_view)
    mock_qs.filter.assert_called_once_with(
        created__lte=expected_lte,
    )



    mock_request.query_params = {
        "created_min": "2024-01-01T00:00:00Z",
        "modified_max": "2024-01-05T00:00:00Z"
    }
    mock_qs.filter.reset_mock()
    result = filter_backend.filter_queryset(mock_request, mock_qs, mock_view)
    mock_qs.filter.assert_called_once_with(
        created__gte=expected_gte,
        modified__lte=expected_lte,
    )


    mock_request.query_params = {
        "bad_field_min": "2024-01-01T00:00:00Z",
        "modified_max": "2024-01-05T00:00:00Z"
    }
    mock_qs.filter.reset_mock()
    result = filter_backend.filter_queryset(mock_request, mock_qs, mock_view)
    mock_qs.filter.assert_called_once_with(
        modified__lte=expected_lte,
    )