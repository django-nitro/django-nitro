"""
Contact Form Example - Demonstrates Form Field Template Tags (v0.6.0)

This example shows how to use:
- {% nitro_input %} for text, email, and tel inputs
- {% nitro_select %} for dropdowns
- {% nitro_textarea %} for multi-line text
- {% nitro_checkbox %} for boolean fields
"""

from pydantic import BaseModel, EmailStr, Field
from nitro import NitroComponent, register_component


class ContactFormState(BaseModel):
    """State for contact form with validation."""

    # Form fields
    full_name: str = ""
    email: str = ""
    phone: str = ""
    subject: str = ""
    message: str = ""
    terms_accepted: bool = False

    # Subject choices for dropdown
    subject_choices: list[dict] = Field(default_factory=lambda: [
        {'value': 'general', 'label': 'General Inquiry'},
        {'value': 'support', 'label': 'Technical Support'},
        {'value': 'sales', 'label': 'Sales Question'},
        {'value': 'feedback', 'label': 'Feedback'},
    ])


@register_component
class ContactForm(NitroComponent[ContactFormState]):
    """Contact form component with validation and form field template tags."""

    template_name = "contact_form.html"

    def get_initial_state(self):
        """Initialize form with empty values and subject choices."""
        return ContactFormState()

    def submit_form(self):
        """
        Validate and submit the contact form.

        Demonstrates:
        - Pydantic validation
        - Error handling
        - Success messages
        """
        # Validate required fields
        if not self.state.full_name or len(self.state.full_name) < 2:
            self.error("Name must be at least 2 characters long")
            return

        if not self.state.email or '@' not in self.state.email:
            self.error("Please enter a valid email address")
            return

        if not self.state.phone:
            self.error("Phone number is required")
            return

        if not self.state.subject:
            self.error("Please select a subject")
            return

        if not self.state.message or len(self.state.message) < 10:
            self.error("Message must be at least 10 characters long")
            return

        if not self.state.terms_accepted:
            self.error("You must accept the terms and conditions")
            return

        # Simulate successful submission
        self.success(f"Thank you, {self.state.full_name}! Your message has been received.")

        # Reset form
        self.state.full_name = ""
        self.state.email = ""
        self.state.phone = ""
        self.state.subject = ""
        self.state.message = ""
        self.state.terms_accepted = False

    def clear_form(self):
        """Clear all form fields."""
        self.state.full_name = ""
        self.state.email = ""
        self.state.phone = ""
        self.state.subject = ""
        self.state.message = ""
        self.state.terms_accepted = False
        self.info("Form cleared")
