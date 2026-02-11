# Currency Utilities

## Python Functions

```python
from nitro.utils import format_currency, parse_currency
```

### format_currency

Format a number as currency.

```python
format_currency(1234.5)              # "RD$ 1,234.50"
format_currency(1234.5, 'USD')       # "US$ 1,234.50"
format_currency(1234.5, 'EUR')       # "€ 1,234.50"
format_currency(1234.5, 'DOP', True) # "RD$ 1,234.50 DOP"
```

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `amount` | required | Number to format |
| `currency` | 'DOP' | Currency code |
| `show_code` | False | Show currency code at end |

### parse_currency

Parse a formatted currency string.

```python
parse_currency('RD$ 1,234.50')      # Decimal('1234.50')
parse_currency('US$ 1,234.50')      # Decimal('1234.50')
parse_currency('1234.50')           # Decimal('1234.50')
parse_currency('1,234')             # Decimal('1234')
```

---

## Template Filter

```html
{% load nitro_tags %}

{{ amount|currency }}           {# RD$ 1,234.50 #}
{{ amount|currency:'USD' }}     {# US$ 1,234.50 #}
{{ amount|currency:'EUR' }}     {# € 1,234.50 #}
```

---

## Form Field

```python
from nitro.forms import CurrencyField

class PaymentForm(forms.Form):
    amount = CurrencyField(currency='DOP')
```

Validates and parses currency input.

---

## Alpine Component

```html
<input
    x-data="currencyInput({ currency: 'DOP' })"
    x-model="formatted"
    @input="format()"
    type="text"
    placeholder="RD$ 0.00"
>
<input type="hidden" name="amount" :value="raw">
```

Auto-formats as user types. Hidden input contains raw numeric value.

---

## Supported Currencies

| Code | Symbol | Name |
|------|--------|------|
| DOP | RD$ | Dominican Peso |
| USD | US$ | US Dollar |
| EUR | € | Euro |

To add more currencies, update `nitro/utils/currency.py`:

```python
CURRENCY_SYMBOLS = {
    'DOP': 'RD$',
    'USD': 'US$',
    'EUR': '€',
    'GBP': '£',
    # Add more...
}
```

---

## Best Practices

1. **Store as Decimal** in database, not float
2. **Format on display** only, store raw values
3. **Use hidden input** with Alpine for form submission
4. **Validate on server** - client formatting is for UX only

```python
# Model
class Payment(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='DOP')

# View
{{ payment.amount|currency:payment.currency }}
```
