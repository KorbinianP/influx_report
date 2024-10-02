import pytest
from unittest.mock import patch
from datetime import datetime
from main import main


@pytest.mark.parametrize("test_date, is_first_of_month, is_sunday, expected_period", [
    (datetime(year=2024, month=10, day=1), True, False, "month"),
    (datetime(year=2024, month=10, day=2), False, False, None),
    (datetime(year=2024, month=10, day=6), False, True, "week"),
    (datetime(year=2024, month=10, day=7), False, False, None),
])
def test_main(test_date, is_first_of_month, is_sunday, expected_period):
    with patch('main.process') as mock_process, \
         patch('main.is_first_of_month', return_value=is_first_of_month), \
         patch('main.is_sunday', return_value=is_sunday), \
         patch('main.datetime') as mock_datetime:

        mock_datetime.now.return_value = test_date
        main()

        if expected_period:
            mock_process.assert_any_call(date=test_date.replace(hour=23, minute=59, second=59), period=expected_period)
        else:
            mock_process.assert_not_called()
