"""unit test main.py"""
from datetime import datetime
from unittest.mock import patch

import pytest

from main import main


@pytest.mark.parametrize("test_date, is_first_of_month, is_sunday", [
    (datetime(year=2024, month=10, day=1), True, False),
    (datetime(year=2024, month=10, day=2), True, False),
    (datetime(year=2024, month=10, day=6), False, True),
    (datetime(year=2024, month=10, day=7), False, True),
])
def test_main(test_date, is_first_of_month, is_sunday):
    """test main function with different combinations"""
    with patch('main.process') as mock_process, \
         patch('main.is_first_of_month', return_value=is_first_of_month), \
         patch('main.is_sunday', return_value=is_sunday), \
         patch('main.datetime') as mock_datetime:

        mock_datetime.now.return_value = test_date
        main(today=test_date)

        mock_process.assert_any_call(date=test_date, is_month=is_first_of_month)
