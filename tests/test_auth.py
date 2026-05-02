"""Tests for authentication system."""

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from lofi_gen.auth import check_quota
from lofi_gen.db.models import User, UserTier


def test_check_quota_within_limit():
    """Test quota check passes when within limit."""
    user = MagicMock()
    user.videos_generated = 5
    user.monthly_limit = 10
    user.max_duration = 14400
    
    # Should not raise
    check_quota(user, 3600)


def test_check_quota_exceeded():
    """Test quota check fails when limit exceeded."""
    user = MagicMock()
    user.tier = MagicMock()
    user.tier.value = "free"
    user.videos_generated = 10
    user.monthly_limit = 10
    
    with pytest.raises(HTTPException) as exc:
        check_quota(user, 3600)
    
    assert exc.value.status_code == 429
    assert "Monthly limit reached" in str(exc.value.detail)


def test_check_duration_exceeded():
    """Test duration limit check."""
    user = MagicMock()
    user.max_duration = 3600
    
    with pytest.raises(HTTPException) as exc:
        check_quota(user, 7200)
    
    assert exc.value.status_code == 400
    assert "Duration exceeds limit" in str(exc.value.detail)
