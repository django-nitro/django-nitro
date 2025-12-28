# Counter Example

A simple Django Nitro counter component to demonstrate basic concepts.

## Features

- Basic NitroComponent usage
- State management with Pydantic
- Action methods (increment, decrement, reset)
- Success messages
- No database required

## Setup

```bash
# Create virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# Install dependencies
pip install django django-ninja pydantic django-nitro

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

Visit: http://localhost:8000/

## Documentation

See the [full Counter example documentation](../../docs/examples/counter.md) for detailed explanations.
