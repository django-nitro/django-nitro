"""
Nitro 0.8 - Multi-step form wizard.

Supports:
- Multiple steps with individual forms
- Session-based data storage
- Back/forward navigation
- Step validation
- Conditional steps
- Final submission

Usage:
    class PropertyWizard(CompanyMixin, NitroWizard):
        wizard_name = 'property_setup'
        steps = [
            WizardStep('type', PropertyTypeForm, 'wizard/type.html', 'Tipo'),
            WizardStep('details', PropertyDetailsForm, 'wizard/details.html', 'Detalles'),
            WizardStep('confirm', None, 'wizard/confirm.html', 'Confirmar'),
        ]

        def done(self, wizard_data):
            property = Property.objects.create(**wizard_data['details'])
            self.clear_wizard_data()
            return redirect('property_detail', pk=property.pk)
"""

from django.shortcuts import redirect
from .views import NitroView


class WizardStep:
    """
    Define a wizard step.

    Args:
        name: Unique step identifier (used in session key and URL)
        form_class: Django Form class for this step (None for confirmation steps)
        template: Template to render for this step
        title: Human-readable step title
        skip_allowed: Whether the user can skip this step
        condition: Callable(wizard_data) -> bool, step shows only if True
    """

    def __init__(self, name, form_class=None, template=None, title='',
                 skip_allowed=False, condition=None):
        self.name = name
        self.form_class = form_class
        self.template = template
        self.title = title
        self.skip_allowed = skip_allowed
        self.condition = condition


class NitroWizard(NitroView):
    """
    Multi-step form wizard with session-based data persistence.

    Subclasses must implement ``done(wizard_data)`` to handle final submission.
    """

    wizard_name = 'wizard'
    steps = []
    template_name = 'nitro/wizard/base.html'

    @property
    def session_key(self):
        return f'wizard_{self.wizard_name}'

    # -- Session data helpers -------------------------------------------------

    def get_wizard_data(self):
        """Get all wizard data from session."""
        return self.request.session.get(self.session_key, {})

    def save_wizard_data(self, data):
        """Save wizard data to session."""
        self.request.session[self.session_key] = data
        self.request.session.modified = True

    def clear_wizard_data(self):
        """Clear wizard data from session."""
        if self.session_key in self.request.session:
            del self.request.session[self.session_key]

    def get_step_data(self, step_name):
        """Get saved data for a specific step."""
        return self.get_wizard_data().get(step_name, {})

    def save_step_data(self, step_name, data):
        """Save data for a specific step."""
        wizard_data = self.get_wizard_data()
        wizard_data[step_name] = data
        self.save_wizard_data(wizard_data)

    # -- Step navigation ------------------------------------------------------

    def get_active_steps(self):
        """Get list of steps that should be shown (based on conditions)."""
        wizard_data = self.get_wizard_data()
        return [
            step for step in self.steps
            if step.condition is None or step.condition(wizard_data)
        ]

    def get_current_step_index(self):
        """Get current step index from ?step= param or default to 0."""
        step_name = self.request.GET.get('step') or self.request.POST.get('current_step')
        if step_name:
            for i, step in enumerate(self.get_active_steps()):
                if step.name == step_name:
                    return i
        return 0

    def get_current_step(self):
        """Get current WizardStep object."""
        steps = self.get_active_steps()
        index = self.get_current_step_index()
        if 0 <= index < len(steps):
            return steps[index]
        return steps[0] if steps else None

    def is_last_step(self):
        steps = self.get_active_steps()
        return self.get_current_step_index() >= len(steps) - 1

    # -- Form handling --------------------------------------------------------

    def get_form(self, step=None):
        """Get form for current or specified step."""
        if step is None:
            step = self.get_current_step()

        if not step or not step.form_class:
            return None

        return step.form_class(**self.get_form_kwargs(step))

    def get_form_kwargs(self, step):
        """Get form kwargs, pre-populated with saved data."""
        kwargs = {'initial': self.get_step_data(step.name)}

        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES

        return kwargs

    # -- Template rendering ---------------------------------------------------

    def get_template_names(self):
        """Return step-specific template or default."""
        step = self.get_current_step()
        if step and step.template:
            return [step.template]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        steps = self.get_active_steps()
        current_index = self.get_current_step_index()
        current_step = self.get_current_step()

        context.update({
            'wizard_name': self.wizard_name,
            'steps': steps,
            'current_step': current_step,
            'current_step_index': current_index,
            'total_steps': len(steps),
            'is_first_step': current_index == 0,
            'is_last_step': current_index == len(steps) - 1,
            'progress_percent': int((current_index / max(len(steps) - 1, 1)) * 100),
            'wizard_data': self.get_wizard_data(),
        })

        if 'form' not in kwargs:
            context['form'] = self.get_form()
        else:
            context['form'] = kwargs['form']

        return context

    # -- HTTP methods ---------------------------------------------------------

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        action = request.POST.get('wizard_action', 'next')

        if action == 'cancel':
            return self.cancel()

        if action == 'back':
            return self.go_back()

        if action == 'skip':
            return self.skip_step()

        # Validate current step
        form = self.get_form()
        if form:
            if not form.is_valid():
                return self.render_to_response(
                    self.get_context_data(form=form)
                )
            # Save validated data
            self.save_step_data(self.get_current_step().name, form.cleaned_data)

        # Go to next step or finish
        if action == 'finish' or self.is_last_step():
            return self.done(self.get_wizard_data())

        return self.go_next()

    # -- Navigation actions ---------------------------------------------------

    def go_next(self):
        """Navigate to next step."""
        steps = self.get_active_steps()
        next_index = self.get_current_step_index() + 1
        if next_index < len(steps):
            return redirect(self.get_step_url(steps[next_index].name))
        return self.done(self.get_wizard_data())

    def go_back(self):
        """Navigate to previous step."""
        steps = self.get_active_steps()
        prev_index = self.get_current_step_index() - 1
        if prev_index >= 0:
            return redirect(self.get_step_url(steps[prev_index].name))
        return redirect(self.get_step_url(steps[0].name))

    def skip_step(self):
        """Skip current step if allowed."""
        current = self.get_current_step()
        if current and current.skip_allowed:
            return self.go_next()
        return self.render_to_response(self.get_context_data())

    def cancel(self):
        """Cancel wizard and clear data."""
        self.clear_wizard_data()
        return redirect(self.get_cancel_url())

    # -- URL helpers (override as needed) -------------------------------------

    def get_step_url(self, step_name):
        """Get URL for a specific step."""
        return f'{self.request.path}?step={step_name}'

    def get_cancel_url(self):
        """URL to redirect on cancel."""
        return '/'

    # -- Abstract method ------------------------------------------------------

    def done(self, wizard_data):
        """
        Called when wizard is complete. Must return an HttpResponse.
        Override in subclasses to handle the final submission.
        """
        raise NotImplementedError("Subclasses must implement done()")
