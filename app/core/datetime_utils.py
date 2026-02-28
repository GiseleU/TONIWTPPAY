# Date and time utilities

from datetime import date, datetime, timedelta, timezone


def get_yesterday() -> date:
    """Get yesterday's date."""
    return date.today() - timedelta(days=1)


def get_today() -> date:
    """Get today's date."""
    return date.today()


def date_to_datetime(d: date) -> datetime:
    """Convert date to datetime at midnight."""
    return datetime.combine(d, datetime.min.time())


def datetime_to_date(dt: datetime) -> date:
    """Convert datetime to date."""
    return dt.date()


def get_date_range(start_date: date, end_date: date) -> list[date]:
    """Get list of dates from start to end inclusive."""
    return [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]


def get_start_of_day(d: date) -> datetime:
    """Get the start of the day (midnight) as timezone-aware datetime."""
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)


def get_end_of_day(d: date) -> datetime:
    """Get the end of the day (23:59:59.999999) as timezone-aware datetime."""
    return datetime.combine(d, datetime.max.time(), tzinfo=timezone.utc)
