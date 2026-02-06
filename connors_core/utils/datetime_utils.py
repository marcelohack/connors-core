from datetime import datetime, timedelta
from typing import Optional


def add_utc_offset(utc_datetime: datetime, utc_offset: float) -> datetime:
    """Add UTC offset to a datetime object"""
    utc_offset_datetime = utc_datetime + timedelta(hours=utc_offset)
    return utc_offset_datetime


def is_valid_date(date_str: Optional[str]) -> bool:
    """Check if date string is valid YYYY-MM-DD format"""
    if date_str is None or date_str == "":
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
