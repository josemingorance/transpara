"""Tests for management commands."""
from io import StringIO
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.test import TestCase


@pytest.mark.django_db
class TestRunCrawlersCommand(TestCase):
    """Test run_crawlers management command."""

    def test_list_crawlers(self):
        """Test --list flag shows available crawlers."""
        out = StringIO()
        call_command("run_crawlers", "--list", stdout=out)
        output = out.getvalue()

        assert "Available crawlers:" in output
        assert "pcsp" in output.lower()

    @patch("apps.crawlers.implementations.pcsp.PCSPCrawler.run_crawler")
    def test_run_specific_crawler(self, mock_run):
        """Test running specific crawler."""
        mock_run_instance = Mock()
        mock_run_instance.status = "SUCCESS"
        mock_run_instance.records_created = 5
        mock_run_instance.records_updated = 2
        mock_run_instance.records_failed = 0
        mock_run_instance.duration_seconds = 10
        mock_run.return_value = mock_run_instance

        out = StringIO()
        call_command("run_crawlers", "--only", "pcsp", stdout=out)
        output = out.getvalue()

        assert "Running: pcsp" in output
        mock_run.assert_called_once()

    @patch("apps.crawlers.implementations.pcsp.PCSPCrawler.run_crawler")
    def test_run_multiple_crawlers(self, mock_run):
        """Test running multiple crawlers."""
        mock_run_instance = Mock()
        mock_run_instance.status = "SUCCESS"
        mock_run_instance.records_created = 5
        mock_run_instance.records_updated = 2
        mock_run_instance.records_failed = 0
        mock_run_instance.duration_seconds = 10
        mock_run.return_value = mock_run_instance

        out = StringIO()
        # Note: Would need multiple crawlers registered
        call_command("run_crawlers", "--only", "pcsp", stdout=out)

        assert "completed" in output.lower()

    def test_run_nonexistent_crawler(self):
        """Test running nonexistent crawler shows error."""
        out = StringIO()
        call_command("run_crawlers", "--only", "nonexistent", stdout=out)
        output = out.getvalue()

        assert "not found" in output.lower() or "✗" in output
