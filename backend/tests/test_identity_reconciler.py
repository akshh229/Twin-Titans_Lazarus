"""Tests for identity reconciliation"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.identity_reconciler import reconcile_patient_identity


class TestIdentityReconciler:
    def test_dominant_even_parity(self):
        mock_db = MagicMock()
        mock_samples = []
        for i in range(8):
            s = MagicMock()
            s.parity_flag = "even"
            mock_samples.append(s)
        for i in range(2):
            s = MagicMock()
            s.parity_flag = "odd"
            mock_samples.append(s)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_samples
        mock_db.query.return_value = mock_query

        mock_alias = MagicMock()
        mock_alias.patient_id = "test-uuid"
        mock_query.first.return_value = mock_alias

        result = reconcile_patient_identity("P00001", mock_db)
        assert result == "test-uuid"

    def test_no_samples_defaults_even(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = MagicMock(patient_id="default-uuid")
        mock_db.query.return_value = mock_query

        result = reconcile_patient_identity("P00001", mock_db)
        assert result == "default-uuid"
