# tests/services/test_daily_summary_job.py
import pytest
from unittest.mock import patch, MagicMock
from app.services import daily_summary_job
from app.core.enums import CoexistenceStatus
from app.core.datetime_utils import get_yesterday

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_run_daily_summary_job_calls_generate_for_active_tenants():
    mock_db = MagicMock()
    mock_tenant1 = MagicMock(id="T001", coexistence_status=CoexistenceStatus.ACTIVE)
    mock_tenant2 = MagicMock(id="T002", coexistence_status=CoexistenceStatus.ACTIVE)
    
    # Patch get_db to return our mock DB session
    with patch("app.services.daily_summary_job.get_db", return_value=iter([mock_db])):
        # Patch the query chain to return our tenants
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_tenant1, mock_tenant2]
        
        # Patch generate_daily_summary so we can assert calls
        with patch("app.services.daily_summary_job.generate_daily_summary") as mock_generate:
            # Patch logger to avoid real logging
            with patch("app.services.daily_summary_job.logger") as mock_logger:
                # Patch get_yesterday to return a fixed date for predictability
                with patch("app.services.daily_summary_job.get_yesterday", return_value=get_yesterday()):
                    await daily_summary_job.run_daily_summary_job()
                
                # Assert generate_daily_summary called for each tenant
                yesterday = get_yesterday()
                mock_generate.assert_any_call(mock_db, "T001", yesterday)
                mock_generate.assert_any_call(mock_db, "T002", yesterday)
                
                # Assert commit called once
                mock_db.commit.assert_called_once()
                
                # Assert logger called at least twice (one per tenant)
                assert mock_logger.info.call_count >= 2

@pytest.mark.asyncio
async def test_run_daily_summary_job_handles_exceptions():
    mock_db = MagicMock()
    mock_tenant = MagicMock(id="T001", coexistence_status=CoexistenceStatus.ACTIVE)
    
    with patch("app.services.daily_summary_job.get_db", return_value=iter([mock_db])):
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_tenant]
        
        # Patch generate_daily_summary to raise an exception
        with patch("app.services.daily_summary_job.generate_daily_summary", side_effect=Exception("Boom")):
            with patch("app.services.daily_summary_job.logger") as mock_logger:
                # Patch get_yesterday to return a fixed date
                with patch("app.services.daily_summary_job.get_yesterday", return_value=get_yesterday()):
                    await daily_summary_job.run_daily_summary_job()
                
                # Ensure commit still called
                mock_db.commit.assert_called_once()
                
                # Ensure logger.error called for the exception
                mock_logger.error.assert_called()