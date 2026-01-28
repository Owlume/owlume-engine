import pytest
from src.judgment_landing import (
    build_judgment_terminal_state,
    enforce_judgment_landing_on_termination,
    JudgmentLandingError,
)

def test_missing_jts_blocks_termination():
    with pytest.raises(JudgmentLandingError):
        enforce_judgment_landing_on_termination(None)

def test_build_valid_jts_passes():
    jts = build_judgment_terminal_state(
        jtype="position",
        statement="I now judge the real problem is incorrectly framed.",
        confidence=0.7,
        acknowledged=True,
    )
    enforce_judgment_landing_on_termination(jts)

def test_ack_required():
    with pytest.raises(JudgmentLandingError):
        build_judgment_terminal_state(
            jtype="boundary",
            statement="I cannot judge until I verify the underlying constraints.",
            confidence=0.5,
            acknowledged=False,
        )
