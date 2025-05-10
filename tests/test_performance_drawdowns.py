# tests/test_performance_drawdowns.py

import pandas as pd
import pytest
from utils.performance import calculate_drawdowns

def test_calculate_drawdowns_series_and_max():
    # Build a series with known peaks and troughs
    idx = pd.date_range("2020-01-01", periods=5)
    prices = pd.Series([100, 120, 110, 130,  90], index=idx)

    # Manually compute expected drawdowns
    # day1: peak=100 → (100-100)/100 = 0.0
    # day2: peak=120 → (120-120)/120 = 0.0
    # day3: peak still 120 → (110-120)/120 = -0.0833333...
    # day4: new peak=130 → (130-130)/130 = 0.0
    # day5: peak still 130 → (90 -130)/130  = -0.3076923...
    expected = pd.Series(
        [
            0.0,
            0.0,
            (110 - 120) / 120,
            -0.0833333,
            (90  - 130) / 130
        ],
        index=idx
    )

    # Run the function
    drawdowns, max_dd = calculate_drawdowns(prices)

    # Check that the full drawdowns series matches exactly
    pd.testing.assert_series_equal(
        drawdowns,
        expected,
        rtol=1e-6,
        atol=1e-8,
        check_names=False
    )

    # And that max_dd equals the lowest point in that series
    assert max_dd == pytest.approx(expected.min(), rel=1e-6)