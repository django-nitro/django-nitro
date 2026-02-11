# Forms & Wizards

## NitroModelForm

Enhanced ModelForm with Tailwind styling.

```python
from nitro.forms import NitroModelForm

class PropertyForm(NitroModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'rent_amount', 'status']

    # All widgets automatically get Tailwind classes
```

## NitroForm

For non-model forms.

```python
from nitro.forms import NitroForm, PhoneField, CurrencyField

class ContactForm(NitroForm):
    name = forms.CharField(max_length=100)
    phone = PhoneField()
    amount = CurrencyField()
```

## Custom Fields

### PhoneField

Phone number with formatting.

```python
from nitro.forms import PhoneField

class TenantForm(NitroModelForm):
    phone = PhoneField()  # Validates and formats phone numbers
```

### CurrencyField

Currency input with formatting.

```python
from nitro.forms import CurrencyField

class PaymentForm(NitroForm):
    amount = CurrencyField(currency='DOP')  # DOP, USD, EUR
```

### CedulaField

Dominican ID validation.

```python
from nitro.forms import CedulaField

class PersonForm(NitroForm):
    cedula = CedulaField()  # Validates Dominican cedula format
```

---

## NitroWizard

Multi-step form wizard with session-based data persistence.

### Define the Wizard

```python
from nitro.wizards import NitroWizard, WizardStep

class OnboardingWizard(NitroWizard):
    wizard_name = 'onboarding'
    steps = [
        WizardStep(
            name='company',
            form_class=CompanyForm,
            template='wizard/company.html',
            title='Datos de la Empresa'
        ),
        WizardStep(
            name='plan',
            form_class=PlanForm,
            template='wizard/plan.html',
            title='Seleccionar Plan'
        ),
        WizardStep(
            name='confirm',
            form_class=None,  # No form, just confirmation
            template='wizard/confirm.html',
            title='Confirmar'
        ),
    ]

    def done(self, wizard_data):
        """Called when wizard completes."""
        Company.objects.create(**wizard_data['company'])
        self.clear_wizard_data()
        return redirect('dashboard')
```

### URL Configuration

```python
# urls.py
from .views import OnboardingWizard

urlpatterns = [
    path('onboarding/', OnboardingWizard.as_view(), name='onboarding'),
    path('onboarding/<str:step>/', OnboardingWizard.as_view(), name='onboarding_step'),
]
```

### Step Templates

```html
<!-- wizard/company.html -->
{% extends "wizard/base.html" %}

{% block wizard_content %}
<form method="post">
    {% csrf_token %}
    {% nitro_field form.name %}
    {% nitro_field form.rnc %}
    {% nitro_field form.address %}

    <div class="flex justify-between mt-6">
        {% if prev_step %}
        <a href="{{ prev_step.url }}" class="btn btn-secondary">Anterior</a>
        {% endif %}
        <button type="submit" class="btn btn-primary">Siguiente</button>
    </div>
</form>
{% endblock %}
```

### Wizard Base Template

```html
<!-- wizard/base.html -->
{% extends "base.html" %}
{% load nitro_tags %}

{% block content %}
<div class="max-w-2xl mx-auto py-8">
    <!-- Progress bar -->
    <div class="mb-8">
        <div class="flex justify-between">
            {% for step in steps %}
            <div class="flex items-center {% if step.is_complete %}text-green-600{% elif step.is_current %}text-blue-600{% else %}text-gray-400{% endif %}">
                <span class="w-8 h-8 rounded-full border-2 flex items-center justify-center mr-2">
                    {{ forloop.counter }}
                </span>
                <span class="hidden sm:inline">{{ step.title }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Step content -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-bold mb-4">{{ current_step.title }}</h2>
        {% block wizard_content %}{% endblock %}
    </div>
</div>
{% endblock %}
```

### Accessing Wizard Data

```python
class OnboardingWizard(NitroWizard):
    # ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Access data from previous steps
        wizard_data = self.get_wizard_data()
        if 'company' in wizard_data:
            context['company_name'] = wizard_data['company']['name']

        return context
```

### Conditional Steps

```python
class OnboardingWizard(NitroWizard):
    # ...

    def should_skip_step(self, step_name):
        """Skip steps based on previous answers."""
        if step_name == 'payment':
            wizard_data = self.get_wizard_data()
            plan = wizard_data.get('plan', {}).get('plan_type')
            return plan == 'free'
        return False
```

### WizardStep Options

| Parameter | Description |
|-----------|-------------|
| `name` | Unique step identifier |
| `form_class` | Form class (None for display-only steps) |
| `template` | Template path |
| `title` | Display title |
| `description` | Optional description |
