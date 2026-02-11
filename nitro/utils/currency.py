"""
Nitro 0.8 - Currency utilities.

Usage:
    from nitro.utils.currency import format_currency, parse_currency

    format_currency(1234.5)          # Uses NITRO_DEFAULT_CURRENCY setting
    format_currency(1234.5, 'USD')   # "US$ 1,234.50"
    parse_currency('RD$ 1,234.50')   # Decimal('1234.50')

Configure default currency in Django settings:
    NITRO_DEFAULT_CURRENCY = 'USD'  # or 'DOP', 'EUR', etc.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def get_default_currency() -> str:
    """Get default currency from Django settings, fallback to 'USD'."""
    try:
        from django.conf import settings
        return getattr(settings, 'NITRO_DEFAULT_CURRENCY', 'USD')
    except Exception:
        return 'USD'


# Currency configurations
CURRENCIES = {
    'DOP': {
        'symbol': 'RD$',
        'name': 'Peso Dominicano',
        'decimal_places': 2,
        'thousand_sep': ',',
        'decimal_sep': '.',
    },
    'USD': {
        'symbol': 'US$',
        'name': 'Dólar Estadounidense',
        'decimal_places': 2,
        'thousand_sep': ',',
        'decimal_sep': '.',
    },
    'EUR': {
        'symbol': '€',
        'name': 'Euro',
        'decimal_places': 2,
        'thousand_sep': '.',
        'decimal_sep': ',',
    },
}


def get_currency_symbol(currency_code: str) -> str:
    """Get currency symbol for a given code."""
    return CURRENCIES.get(currency_code, {}).get('symbol', currency_code)


def format_currency(amount: Union[int, float, Decimal, str, None],
                    currency_code: str = None,
                    show_symbol: bool = True) -> str:
    """
    Format amount as currency string.

    Args:
        amount: The amount to format
        currency_code: Currency code (DOP, USD, EUR). Defaults to NITRO_DEFAULT_CURRENCY setting.
        show_symbol: Include currency symbol

    Returns:
        Formatted string like "US$ 1,234.56"
    """
    if amount is None:
        return ''

    if currency_code is None:
        currency_code = get_default_currency()

    try:
        if isinstance(amount, str):
            amount = Decimal(amount.replace(',', ''))
        elif isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
    except Exception:
        return str(amount)

    default_currency = get_default_currency()
    config = CURRENCIES.get(currency_code, CURRENCIES.get(default_currency, CURRENCIES['USD']))

    # Round to decimal places
    places = config['decimal_places']
    quantize_str = '0.' + '0' * places
    amount = amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    # Format number
    is_negative = amount < 0
    amount = abs(amount)
    parts = str(amount).split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else '00'

    # Add thousand separators
    reversed_int = integer_part[::-1]
    groups = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
    formatted_int = config['thousand_sep'].join(groups)[::-1]

    formatted = f"{formatted_int}{config['decimal_sep']}{decimal_part}"

    if is_negative:
        formatted = f"-{formatted}"

    if show_symbol:
        return f"{config['symbol']} {formatted}"
    return formatted


def parse_currency(value: str, currency_code: str = None) -> Decimal:
    """
    Parse currency string to Decimal.

    Args:
        value: String like "RD$ 1,234.56" or "1234.56"
        currency_code: Currency code for parsing rules. Defaults to NITRO_DEFAULT_CURRENCY.

    Returns:
        Decimal amount
    """
    if not value:
        return Decimal('0')

    if currency_code is None:
        currency_code = get_default_currency()

    default_currency = get_default_currency()
    config = CURRENCIES.get(currency_code, CURRENCIES.get(default_currency, CURRENCIES['USD']))

    # Remove currency symbol and whitespace
    cleaned = str(value)
    for curr in CURRENCIES.values():
        cleaned = cleaned.replace(curr['symbol'], '')
    cleaned = cleaned.strip()

    # Remove thousand separators
    cleaned = cleaned.replace(config['thousand_sep'], '')

    # Normalize decimal separator
    if config['decimal_sep'] != '.':
        cleaned = cleaned.replace(config['decimal_sep'], '.')

    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal('0')


def convert_currency(amount: Decimal, from_currency: str, to_currency: str,
                     rates: dict = None) -> Decimal:
    """
    Convert between currencies using provided rates.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        rates: Dict of rates relative to DOP, e.g. {'USD': 58.5, 'EUR': 63.0}

    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount

    if rates is None:
        # Default approximate rates to DOP
        rates = {
            'DOP': Decimal('1'),
            'USD': Decimal('58.5'),
            'EUR': Decimal('63.0'),
        }

    # Convert to DOP first, then to target
    if from_currency != 'DOP':
        amount_dop = amount * rates.get(from_currency, Decimal('1'))
    else:
        amount_dop = amount

    if to_currency != 'DOP':
        result = amount_dop / rates.get(to_currency, Decimal('1'))
    else:
        result = amount_dop

    return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
