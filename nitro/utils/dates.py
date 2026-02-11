"""
Nitro 0.8 - Date utilities.

Usage:
    from nitro.utils.dates import today, relative_date, month_name

    relative_date(some_date)    # "Hoy", "Ayer", "Hace 3 días"
    month_name(1)               # "Enero"
    month_year(some_date)       # "Enero 2026"
"""

from datetime import date, datetime, timedelta
from typing import Tuple

from django.utils import timezone


def today() -> date:
    """Get today's date (timezone-aware)."""
    return timezone.now().date()


def now() -> datetime:
    """Get current datetime (timezone-aware)."""
    return timezone.now()


def relative_date(value: date) -> str:
    """
    Return relative date string in Spanish.

    Examples: "Hoy", "Ayer", "Mañana", "Hace 3 días", "En 5 días"
    Falls back to dd/mm/yyyy for dates > 30 days away.
    """
    if not value:
        return ''

    if isinstance(value, datetime):
        value = value.date()

    today_date = today()
    diff = (value - today_date).days

    if diff == 0:
        return 'Hoy'
    if diff == 1:
        return 'Mañana'
    if diff == -1:
        return 'Ayer'
    if 1 < diff <= 7:
        return f'En {diff} días'
    if -7 <= diff < -1:
        return f'Hace {abs(diff)} días'
    if 7 < diff <= 30:
        weeks = diff // 7
        return f'En {weeks} semana{"s" if weeks > 1 else ""}'
    if -30 <= diff < -7:
        weeks = abs(diff) // 7
        return f'Hace {weeks} semana{"s" if weeks > 1 else ""}'

    return value.strftime('%d/%m/%Y')


def date_range(start: date, end: date) -> str:
    """Format date range as string."""
    if start.year == end.year:
        if start.month == end.month:
            return f'{start.day}-{end.day} {start.strftime("%b %Y")}'
        return f'{start.strftime("%d %b")} - {end.strftime("%d %b %Y")}'
    return f'{start.strftime("%d %b %Y")} - {end.strftime("%d %b %Y")}'


def month_name(month: int) -> str:
    """Get Spanish month name (1-indexed)."""
    months = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ]
    return months[month] if 1 <= month <= 12 else ''


def month_year(d: date) -> str:
    """Format date as 'Enero 2026'."""
    return f'{month_name(d.month)} {d.year}'


def get_month_range(year: int, month: int) -> Tuple[date, date]:
    """Get first and last day of month."""
    first_day = date(year, month, 1)

    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return first_day, last_day


def get_quarter_range(year: int, quarter: int) -> Tuple[date, date]:
    """Get first and last day of quarter (1-4)."""
    quarters = {
        1: (1, 3),
        2: (4, 6),
        3: (7, 9),
        4: (10, 12),
    }
    start_month, end_month = quarters.get(quarter, (1, 3))
    first_day = date(year, start_month, 1)
    _, last_day = get_month_range(year, end_month)
    return first_day, last_day


def get_year_range(year: int) -> Tuple[date, date]:
    """Get first and last day of year."""
    return date(year, 1, 1), date(year, 12, 31)


def days_until(target_date: date) -> int:
    """Days until target date (negative if past)."""
    if isinstance(target_date, datetime):
        target_date = target_date.date()
    return (target_date - today()).days


def days_since(past_date: date) -> int:
    """Days since past date (negative if future)."""
    if isinstance(past_date, datetime):
        past_date = past_date.date()
    return (today() - past_date).days


def is_overdue(due_date: date) -> bool:
    """Check if date is past today."""
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    return due_date < today()


def add_months(d: date, months: int) -> date:
    """Add (or subtract) months to a date, clamping day to valid range."""
    month = d.month + months
    year = d.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(d.day, get_days_in_month(year, month))
    return date(year, month, day)


def get_days_in_month(year: int, month: int) -> int:
    """
    Get the number of days in a given month, handling leap years.

    Examples:
        get_days_in_month(2024, 2) → 29 (leap year)
        get_days_in_month(2025, 2) → 28 (non-leap year)
        get_days_in_month(2024, 4) → 30
        get_days_in_month(2024, 1) → 31
    """
    import calendar
    return calendar.monthrange(year, month)[1]


def get_safe_day_of_month(year: int, month: int, desired_day: int) -> int:
    """
    Get a valid day for the given month, capping at month's last day.

    This handles the case where payment_day might be 30 or 31 but the
    month has fewer days (e.g., February).

    Examples:
        get_safe_day_of_month(2024, 2, 30) → 29 (Feb 2024 has 29 days - leap year)
        get_safe_day_of_month(2025, 2, 30) → 28 (Feb 2025 has 28 days)
        get_safe_day_of_month(2024, 3, 30) → 30 (March has 31 days)
        get_safe_day_of_month(2024, 4, 31) → 30 (April has 30 days)
        get_safe_day_of_month(2024, 1, 31) → 31 (January has 31 days)
    """
    last_day = get_days_in_month(year, month)
    return min(desired_day, last_day)


def get_due_date(year: int, month: int, payment_day: int) -> date:
    """
    Get the due date for a payment, handling short months correctly.

    This is the primary function to use when calculating payment due dates.

    Examples:
        get_due_date(2024, 2, 30) → date(2024, 2, 29)
        get_due_date(2025, 2, 30) → date(2025, 2, 28)
        get_due_date(2024, 4, 31) → date(2024, 4, 30)
        get_due_date(2024, 3, 15) → date(2024, 3, 15)
    """
    safe_day = get_safe_day_of_month(year, month, payment_day)
    return date(year, month, safe_day)
