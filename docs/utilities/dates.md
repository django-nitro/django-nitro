# Date Utilities

## Python Functions

```python
from nitro.utils import (
    today, relative_date, month_name, is_overdue,
    add_months, start_of_month, end_of_month
)
```

### today

Get current date.

```python
today()  # date(2024, 1, 15)
```

### relative_date

Human-readable relative date.

```python
relative_date(date.today())                    # "Hoy"
relative_date(date.today() - timedelta(1))     # "Ayer"
relative_date(date.today() - timedelta(2))     # "Hace 2 días"
relative_date(date.today() - timedelta(7))     # "Hace 1 semana"
relative_date(date.today() - timedelta(30))    # "Hace 1 mes"
relative_date(date.today() + timedelta(1))     # "Mañana"
relative_date(date.today() + timedelta(7))     # "En 1 semana"
```

### month_name

Get Spanish month name.

```python
month_name(1)   # "Enero"
month_name(12)  # "Diciembre"
```

### is_overdue

Check if date is past due.

```python
is_overdue(date(2024, 1, 1))  # True (if today is after)
is_overdue(date(2099, 1, 1))  # False
is_overdue(None)               # False
```

### add_months

Add months to a date.

```python
add_months(date(2024, 1, 31), 1)  # date(2024, 2, 29) - handles month ends
add_months(date(2024, 1, 15), 3)  # date(2024, 4, 15)
add_months(date(2024, 1, 15), -1) # date(2023, 12, 15)
```

### start_of_month / end_of_month

```python
start_of_month(date(2024, 1, 15))  # date(2024, 1, 1)
end_of_month(date(2024, 1, 15))    # date(2024, 1, 31)
end_of_month(date(2024, 2, 15))    # date(2024, 2, 29) - leap year
```

---

## Template Filters

```html
{% load nitro_tags %}

{{ payment.due_date|relative_date }}    {# Hoy, Ayer, Hace 3 días #}
{{ lease.start_date|date:"d/m/Y" }}     {# 15/01/2024 #}
```

---

## Date Range Helpers

```python
from nitro.utils import date_range, this_month, last_month, this_year

# Get date ranges
this_month()   # (date(2024, 1, 1), date(2024, 1, 31))
last_month()   # (date(2023, 12, 1), date(2023, 12, 31))
this_year()    # (date(2024, 1, 1), date(2024, 12, 31))

# Custom range
date_range('week')   # Last 7 days
date_range('month')  # Last 30 days
date_range('year')   # Last 365 days
```

---

## Common Patterns

### Overdue Indicator

```html
{% if payment.due_date|is_overdue %}
<span class="text-red-500">Vencido</span>
{% endif %}
```

### Relative Date Display

```html
<span title="{{ payment.due_date|date:'d/m/Y' }}">
    {{ payment.due_date|relative_date }}
</span>
```

### Month-Year Display

```python
# In view
context['month_name'] = month_name(date.today().month)
context['year'] = date.today().year
```

```html
{{ month_name }} {{ year }}  {# Enero 2024 #}
```

### Filter by Date Range

```python
class PaymentListView(NitroListView):
    model = Payment

    def get_queryset(self):
        qs = super().get_queryset()

        range_filter = self.request.GET.get('range', 'month')
        start, end = date_range(range_filter)

        return qs.filter(due_date__range=[start, end])
```

---

## Timezone Handling

Nitro date utilities work with naive dates by default. For timezone-aware applications:

```python
from django.utils import timezone

# Use timezone.now() instead of datetime.now()
now = timezone.now()

# Convert to local time for display
from django.utils.timezone import localtime
local_time = localtime(some_datetime)
```
