"""Tests for identity reconciliation"""

import pytest
from unittest.mock import MagicMock
from app.services.identity_reconciler import reconcile_patient_identity


class TestIdentityReconciler:
    def test_dominant_even_parity(self):
        mock_db = MagicMock()

        # Build mock samples: 8 even, 2 odd
        mock_samples = []
        for _ in range(8):
            s = MagicMock()
            s.parity_flag = "even"
            mock_samples.append(s)
        for _ in range(2):
            s = MagicMock()
            s.parity_flag = "odd"
            mock_samples.append(s)

        # First query: CleanTelemetry -> returns samples
        telemetry_query = MagicMock()
        telemetry_query.filter.return_value = telemetry_query
        telemetry_query.order_by.return_value = telemetry_query
        telemetry_query.limit.return_value = telemetry_query
        telemetry_query.all.return_value = mock_samples

        # Second query: PatientAlias -> returns existing alias
        alias_query = MagicMock()
        mock_alias = MagicMock()
        mock_alias.patient_id = "test-uuid"
        alias_query.filter_by.return_value = alias_query
        alias_query.first.return_value = mock_alias

        # db.query returns different mocks per model call
        mock_db.query.side_effect = [telemetry_query, alias_query]

        result = reconcile_patient_identity("P00001", mock_db)
        assert result == "test-uuid"

    def test_no_samples_defaults_even(self):
        mock_db = MagicMock()

        # First query: CleanTelemetry -> no samples
        telemetry_query = MagicMock()
        telemetry_query.filter.return_value = telemetry_query
        telemetry_query.order_by.return_value = telemetry_query
        telemetry_query.limit.return_value = telemetry_query
        telemetry_query.all.return_value = []

        # Second query: PatientAlias -> existing alias
        alias_query = MagicMock()
        mock_alias = MagicMock()
        mock_alias.patient_id = "default-uuid"
        alias_query.filter_by.return_value = alias_query
        alias_query.first.return_value = mock_alias

        mock_db.query.side_effect = [telemetry_query, alias_query]

        result = reconcile_patient_identity("P00001", mock_db)
        assert result == "default-uuid"
