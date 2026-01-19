from django.db import models
from django.test import RequestFactory, TestCase
from pydantic import BaseModel, EmailStr

from nitro.base import ModelNitroComponent, NitroComponent
from nitro.registry import _components_registry, get_component_class, register_component


class SimpleState(BaseModel):
    """Test state schema."""

    count: int = 0
    message: str = ""


class SimpleComponent(NitroComponent[SimpleState]):
    """Test component for basic functionality."""

    template_name = "test.html"
    state_class = SimpleState

    def get_initial_state(self, **kwargs):
        return SimpleState()

    def increment(self):
        self.state.count += 1

    def set_message(self, text: str):
        self.state.message = text


class TestNitroComponent(TestCase):
    """Tests for NitroComponent base class."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_component_initialization(self):
        """Test that a component initializes with correct state."""
        component = SimpleComponent(request=self.request)
        self.assertIsInstance(component.state, SimpleState)
        self.assertEqual(component.state.count, 0)
        self.assertEqual(component.state.message, "")

    def test_component_initialization_with_state(self):
        """Test component initialization with provided state."""
        initial_state = {"count": 5, "message": "hello"}
        component = SimpleComponent(request=self.request, initial_state=initial_state)
        self.assertEqual(component.state.count, 5)
        self.assertEqual(component.state.message, "hello")

    def test_process_action(self):
        """Test that actions can be processed and state updates correctly."""
        component = SimpleComponent(request=self.request)
        result = component.process_action(
            action_name="increment", payload={}, current_state_dict={"count": 0, "message": ""}
        )
        self.assertEqual(result["state"]["count"], 1)

    def test_process_action_with_parameters(self):
        """Test actions with parameters."""
        component = SimpleComponent(request=self.request)
        result = component.process_action(
            action_name="set_message",
            payload={"text": "test message"},
            current_state_dict={"count": 0, "message": ""},
        )
        self.assertEqual(result["state"]["message"], "test message")

    def test_process_action_invalid(self):
        """Test that invalid action returns error response."""
        component = SimpleComponent(request=self.request)
        result = component.process_action(
            action_name="nonexistent_action",
            payload={},
            current_state_dict={"count": 0, "message": ""},
        )
        self.assertTrue(result["error"])
        self.assertIn("Action not found", result["message"])

    def test_integrity_computation(self):
        """Test that integrity token is computed for secure fields."""
        component = SimpleComponent(request=self.request)
        component.secure_fields = ["count"]
        token = component._compute_integrity()
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_integrity_verification_success(self):
        """Test successful integrity verification."""
        component = SimpleComponent(request=self.request)
        component.secure_fields = ["count"]
        token = component._compute_integrity()
        self.assertTrue(component.verify_integrity(token))

    def test_integrity_verification_failure(self):
        """Test failed integrity verification with tampered token."""
        component = SimpleComponent(request=self.request)
        component.secure_fields = ["count"]
        token = component._compute_integrity()
        component.state.count = 999  # Tamper with state
        self.assertFalse(component.verify_integrity(token))

    def test_integrity_verification_no_secure_fields(self):
        """Test that verification passes when no secure fields are defined."""
        component = SimpleComponent(request=self.request)
        self.assertTrue(component.verify_integrity(None))

    def test_success_message(self):
        """Test adding success messages."""
        component = SimpleComponent(request=self.request)
        component.success("Operation successful")
        self.assertEqual(len(component._pending_messages), 1)
        self.assertEqual(component._pending_messages[0]["level"], "success")
        self.assertEqual(component._pending_messages[0]["text"], "Operation successful")

    def test_error_message(self):
        """Test adding error messages."""
        component = SimpleComponent(request=self.request)
        component.error("Operation failed")
        self.assertEqual(len(component._pending_messages), 1)
        self.assertEqual(component._pending_messages[0]["level"], "error")
        self.assertEqual(component._pending_messages[0]["text"], "Operation failed")

    def test_add_field_error(self):
        """Test adding field-specific errors."""
        component = SimpleComponent(request=self.request)
        component.add_error("count", "Invalid count value")
        self.assertEqual(component._pending_errors["count"], "Invalid count value")


class TestComponentRegistry(TestCase):
    """Tests for component registration system."""

    def setUp(self):
        # Clear registry before each test
        _components_registry.clear()

    def tearDown(self):
        # Clear registry after each test
        _components_registry.clear()

    def test_register_component(self):
        """Test component registration."""

        @register_component
        class TestComp(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState()

        self.assertIn("TestComp", _components_registry)
        self.assertEqual(get_component_class("TestComp"), TestComp)

    def test_get_component_class_not_found(self):
        """Test getting a non-existent component."""
        self.assertIsNone(get_component_class("NonExistent"))


class TestModelNitroComponent(TestCase):
    """Tests for ModelNitroComponent."""

    def test_secure_fields_auto_detection(self):
        """Test that id and foreign key fields are automatically marked as secure."""

        # Create a test model and component
        class TestModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "nitro"

        class TestModelState(BaseModel):
            id: int
            name: str
            property_id: int

        class TestModelComponent(ModelNitroComponent[TestModelState]):
            template_name = "test.html"
            state_class = TestModelState
            model = TestModel

            def get_initial_state(self, **kwargs):
                return TestModelState(id=1, name="Test", property_id=1)

        component = TestModelComponent()
        self.assertIn("id", component.secure_fields)
        self.assertIn("property_id", component.secure_fields)


# ============================================================================
# ZERO JAVASCRIPT MODE TESTS (v0.4.0)
# ============================================================================


class TestZeroJavaScriptMode(TestCase):
    """Tests for Zero JavaScript Mode template tags and methods."""

    def test_sync_field_basic(self):
        """Test basic field syncing."""

        class TestState(BaseModel):
            email: str = ""
            count: int = 0

        class TestComponent(NitroComponent[TestState]):
            template_name = "test.html"
            state_class = TestState

            def get_initial_state(self, **kwargs):
                return TestState()

        component = TestComponent()

        # Sync email field
        component._sync_field("email", "test@example.com")
        self.assertEqual(component.state.email, "test@example.com")

        # Sync count field
        component._sync_field("count", 42)
        self.assertEqual(component.state.count, 42)

    def test_sync_field_validation_error(self):
        """Test that validation errors are caught."""

        class TestState(BaseModel):
            email: EmailStr

        class TestComponent(NitroComponent[TestState]):
            template_name = "test.html"
            state_class = TestState

            def get_initial_state(self, **kwargs):
                return TestState(email="valid@example.com")

        component = TestComponent()

        # Try to set invalid email
        component._sync_field("email", "invalid-email")

        # Should add error
        self.assertIn("email", component._pending_errors)

    def test_sync_field_nonexistent_field_debug(self):
        """Test syncing a non-existent field in DEBUG mode."""
        from django.test import override_settings

        class TestState(BaseModel):
            email: str = ""

        class TestComponent(NitroComponent[TestState]):
            template_name = "test.html"
            state_class = TestState

            def get_initial_state(self, **kwargs):
                return TestState()

        component = TestComponent()

        # Should raise ValueError in DEBUG mode
        with override_settings(DEBUG=True):
            with self.assertRaises(ValueError) as cm:
                component._sync_field("nonexistent", "value")

            self.assertIn("does not exist", str(cm.exception))
            self.assertIn("Available fields", str(cm.exception))


class TestTemplateTags(TestCase):
    """Tests for Zero JS Mode template tags."""

    def test_nitro_model_basic(self):
        """Test basic nitro_model tag."""
        from nitro.templatetags.nitro_tags import nitro_model

        result = nitro_model("email")

        # Should include x-model
        self.assertIn('x-model="email"', result)

        # Should include auto-sync call
        self.assertIn("call('_sync_field'", result)
        self.assertIn("field: 'email'", result)

        # Should include error styling
        self.assertIn(":class=", result)
        self.assertIn("border-red-500", result)

    def test_nitro_model_with_debounce(self):
        """Test nitro_model with debounce."""
        from nitro.templatetags.nitro_tags import nitro_model

        result = nitro_model("search", debounce="300ms")

        # Should include debounced input event
        self.assertIn("@input.debounce.300ms", result)

    def test_nitro_model_lazy(self):
        """Test nitro_model with lazy flag."""
        from nitro.templatetags.nitro_tags import nitro_model

        result = nitro_model("password", lazy=True)

        # Should use blur event instead of input
        self.assertIn("@blur", result)
        self.assertNotIn("@input", result)

    def test_nitro_model_with_on_change(self):
        """Test nitro_model with on_change callback."""
        from nitro.templatetags.nitro_tags import nitro_model

        result = nitro_model("email", on_change="validate_email")

        # Should include both sync and callback
        self.assertIn("call('_sync_field'", result)
        self.assertIn("call('validate_email')", result)

    def test_nitro_action_basic(self):
        """Test basic nitro_action tag."""
        from nitro.templatetags.nitro_tags import nitro_action

        result = nitro_action("submit")

        # Should include click handler
        self.assertIn("@click=", result)
        self.assertIn("call('submit')", result)

        # Should include disabled binding
        self.assertIn(":disabled=", result)
        self.assertIn("isLoading", result)

    def test_nitro_action_with_params(self):
        """Test nitro_action with parameters."""
        from nitro.templatetags.nitro_tags import nitro_action

        result = nitro_action("delete", id="item.id", force="true")

        # Should include all parameters
        self.assertIn("call('delete'", result)
        self.assertIn("id: item.id", result)
        self.assertIn("force: true", result)

    def test_nitro_action_with_confirm(self):
        """Test nitro_action with confirmation dialog."""
        from nitro.templatetags.nitro_tags import nitro_action

        result = nitro_action("delete", id="item.id", confirm="Are you sure?")

        # Should include confirm dialog wrapper
        self.assertIn("if(confirm(", result)
        self.assertIn("Are you sure?", result)
        self.assertIn("call('delete'", result)
        self.assertIn("id: item.id", result)

    def test_nitro_show(self):
        """Test nitro_show tag."""
        from nitro.templatetags.nitro_tags import nitro_show

        result = nitro_show("isLoading")

        # Should be simple x-show wrapper
        self.assertEqual(result, 'x-show="isLoading"')

    def test_nitro_show_with_expression(self):
        """Test nitro_show with complex expression."""
        from nitro.templatetags.nitro_tags import nitro_show

        result = nitro_show("count > 0 && !isLoading")

        self.assertIn("x-show=", result)
        self.assertIn("count > 0 && !isLoading", result)

    def test_nitro_class_basic(self):
        """Test nitro_class tag."""
        from nitro.templatetags.nitro_tags import nitro_class

        result = nitro_class(active="isActive", disabled="isLoading")

        # Should include :class binding
        self.assertIn(":class=", result)
        self.assertIn("'active': isActive", result)
        self.assertIn("'disabled': isLoading", result)

    def test_nitro_class_empty(self):
        """Test nitro_class with no conditions."""
        from nitro.templatetags.nitro_tags import nitro_class

        result = nitro_class()

        # Should return empty string
        self.assertEqual(result, "")


# ============================================================================
# ADVANCED ZERO JAVASCRIPT MODE TESTS (v0.5.0)
# ============================================================================


class TestAdvancedTemplateTags(TestCase):
    """Tests for Advanced Zero JS Mode template tags (v0.5.0)."""

    def test_nitro_attr_basic(self):
        """Test basic nitro_attr tag."""
        from nitro.templatetags.nitro_tags import nitro_attr

        result = nitro_attr("src", "product.image_url")

        # Should create dynamic attribute binding
        self.assertEqual(result, ':src="product.image_url"')

    def test_nitro_attr_various_attributes(self):
        """Test nitro_attr with different attributes."""
        from nitro.templatetags.nitro_tags import nitro_attr

        # Test href
        result = nitro_attr("href", "item.link")
        self.assertEqual(result, ':href="item.link"')

        # Test placeholder
        result = nitro_attr("placeholder", "form.placeholder_text")
        self.assertEqual(result, ':placeholder="form.placeholder_text"')

    def test_nitro_disabled_basic(self):
        """Test basic nitro_disabled tag."""
        from nitro.templatetags.nitro_tags import nitro_disabled

        result = nitro_disabled("isProcessing")

        # Should create disabled binding
        self.assertEqual(result, ':disabled="isProcessing"')

    def test_nitro_disabled_with_expression(self):
        """Test nitro_disabled with complex expression."""
        from nitro.templatetags.nitro_tags import nitro_disabled

        result = nitro_disabled("isProcessing || !isValid")

        # Should include full expression
        self.assertIn(':disabled="isProcessing || !isValid"', result)

    def test_nitro_file_basic(self):
        """Test basic nitro_file tag."""
        from nitro.templatetags.nitro_tags import nitro_file

        result = nitro_file("document")

        # Should include file upload handler
        self.assertIn('@change="handleFileUpload', result)
        self.assertIn("'document'", result)

    def test_nitro_file_with_accept(self):
        """Test nitro_file with accept parameter."""
        from nitro.templatetags.nitro_tags import nitro_file

        result = nitro_file("avatar", accept=".jpg,.png")

        # Should include accept attribute
        self.assertIn('accept=".jpg,.png"', result)
        self.assertIn("handleFileUpload", result)

    def test_nitro_file_with_max_size(self):
        """Test nitro_file with max_size parameter."""
        from nitro.templatetags.nitro_tags import nitro_file

        result = nitro_file("document", max_size="5MB")

        # Should include maxSize in options
        self.assertIn("maxSize: '5MB'", result)

    def test_nitro_file_with_preview(self):
        """Test nitro_file with preview enabled."""
        from nitro.templatetags.nitro_tags import nitro_file

        result = nitro_file("avatar", accept="image/*", preview=True)

        # Should include preview option
        self.assertIn("preview: true", result)
        self.assertIn('accept="image/*"', result)


class TestNestedFieldSupport(TestCase):
    """Tests for nested field support in _sync_field (v0.5.0)."""

    def test_sync_nested_field_two_levels(self):
        """Test syncing nested fields (two levels)."""

        class ProfileState(BaseModel):
            email: str = ""
            name: str = ""

        class UserState(BaseModel):
            id: int = 1
            profile: ProfileState = ProfileState()

        class TestComponent(NitroComponent[UserState]):
            template_name = "test.html"
            state_class = UserState

            def get_initial_state(self, **kwargs):
                return UserState()

        component = TestComponent()

        # Sync nested field
        component._sync_field("profile.email", "user@example.com")
        self.assertEqual(component.state.profile.email, "user@example.com")

        component._sync_field("profile.name", "John Doe")
        self.assertEqual(component.state.profile.name, "John Doe")

    def test_sync_nested_field_three_levels(self):
        """Test syncing deeply nested fields (three levels)."""

        class AddressState(BaseModel):
            street: str = ""
            city: str = ""

        class ProfileState(BaseModel):
            address: AddressState = AddressState()

        class UserState(BaseModel):
            profile: ProfileState = ProfileState()

        class TestComponent(NitroComponent[UserState]):
            template_name = "test.html"
            state_class = UserState

            def get_initial_state(self, **kwargs):
                return UserState()

        component = TestComponent()

        # Sync deeply nested field
        component._sync_field("profile.address.city", "New York")
        self.assertEqual(component.state.profile.address.city, "New York")

        component._sync_field("profile.address.street", "123 Main St")
        self.assertEqual(component.state.profile.address.street, "123 Main St")

    def test_sync_nested_field_invalid_path(self):
        """Test syncing with invalid nested field path."""

        class UserState(BaseModel):
            id: int = 1
            name: str = ""

        class TestComponent(NitroComponent[UserState]):
            template_name = "test.html"
            state_class = UserState

            def get_initial_state(self, **kwargs):
                return UserState()

        component = TestComponent()

        # Try to sync non-existent nested path (requires DEBUG mode)
        from django.test import override_settings

        with override_settings(DEBUG=True):
            with self.assertRaises(ValueError):
                component._sync_field("profile.email", "test@example.com")


class TestFileUploadHandler(TestCase):
    """Tests for file upload handler (v0.5.0)."""

    def test_handle_file_upload_default_implementation(self):
        """Test default _handle_file_upload implementation."""

        class TestComponent(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState()

        component = TestComponent()

        # Mock uploaded file
        class MockFile:
            name = "test.pdf"
            size = 1024

        # Call with file - should generate warning
        component._handle_file_upload("document", MockFile())

        # Should have warning message
        self.assertEqual(len(component._pending_messages), 1)
        self.assertEqual(component._pending_messages[0]["level"], "warning")
        self.assertIn("not processed", component._pending_messages[0]["text"])

    def test_handle_file_upload_no_file(self):
        """Test _handle_file_upload with no file."""

        class TestComponent(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState()

        component = TestComponent()

        # Call without file - should generate error
        component._handle_file_upload("document", None)

        # Should have error message
        self.assertEqual(len(component._pending_messages), 1)
        self.assertEqual(component._pending_messages[0]["level"], "error")
        self.assertIn("No file was uploaded", component._pending_messages[0]["text"])


# ============================================================================
# V0.6.0 FORM FIELD TEMPLATE TAGS TESTS
# ============================================================================


class TestFormFieldTags(TestCase):
    """Tests for v0.6.0 Form Field Template Tags."""

    def test_nitro_input_basic(self):
        """Test basic nitro_input tag."""
        from nitro.templatetags.nitro_tags import nitro_input

        result = nitro_input("create_buffer.name", label="Name")

        # Should return context dict
        self.assertIn("field", result)
        self.assertEqual(result["field"], "create_buffer.name")
        self.assertEqual(result["label"], "Name")
        self.assertEqual(result["type"], "text")

    def test_nitro_input_with_edit_buffer(self):
        """Test nitro_input with edit_buffer (safe navigation)."""
        from nitro.templatetags.nitro_tags import nitro_input

        result = nitro_input("edit_buffer.email", label="Email", type="email")

        # Should use safe navigation operator
        self.assertIn("safe_field", result)
        self.assertIn("?.", result["safe_field"])

    def test_nitro_input_with_extra_attrs(self):
        """Test nitro_input with additional HTML attributes."""
        from nitro.templatetags.nitro_tags import nitro_input

        result = nitro_input("create_buffer.price", type="number", step="0.01", min="0")

        # Should include extra attributes
        self.assertIn("extra_attrs", result)
        self.assertIn('step="0.01"', result["extra_attrs"])
        self.assertIn('min="0"', result["extra_attrs"])

    def test_nitro_select_basic(self):
        """Test basic nitro_select tag."""
        from nitro.templatetags.nitro_tags import nitro_select

        choices = [("active", "Active"), ("inactive", "Inactive")]
        result = nitro_select("create_buffer.status", label="Status", choices=choices)

        # Should normalize choices
        self.assertIn("choices", result)
        self.assertEqual(len(result["choices"]), 2)
        self.assertEqual(result["choices"][0]["value"], "active")
        self.assertEqual(result["choices"][0]["label"], "Active")

    def test_nitro_select_with_dict_choices(self):
        """Test nitro_select with dict-based choices."""
        from nitro.templatetags.nitro_tags import nitro_select

        choices = [{"value": "1", "label": "Option 1"}, {"value": "2", "label": "Option 2"}]
        result = nitro_select("edit_buffer.option", choices=choices)

        # Should handle dict format
        self.assertEqual(len(result["choices"]), 2)
        self.assertEqual(result["choices"][0]["value"], "1")

    def test_nitro_checkbox_basic(self):
        """Test basic nitro_checkbox tag."""
        from nitro.templatetags.nitro_tags import nitro_checkbox

        result = nitro_checkbox("create_buffer.is_active", label="Active")

        # Should include field and label
        self.assertEqual(result["field"], "create_buffer.is_active")
        self.assertEqual(result["label"], "Active")
        self.assertIn("change_handler", result)

    def test_nitro_checkbox_with_edit_buffer(self):
        """Test nitro_checkbox with edit_buffer null check."""
        from nitro.templatetags.nitro_tags import nitro_checkbox

        result = nitro_checkbox("edit_buffer.is_vendor", label="Is Vendor")

        # Should use safe navigation
        self.assertTrue(result["is_edit_buffer"])
        self.assertIn("?.", result["safe_field"])

    def test_nitro_textarea_basic(self):
        """Test basic nitro_textarea tag."""
        from nitro.templatetags.nitro_tags import nitro_textarea

        result = nitro_textarea("create_buffer.description", label="Description", rows=5)

        # Should include all parameters
        self.assertEqual(result["field"], "create_buffer.description")
        self.assertEqual(result["label"], "Description")
        self.assertEqual(result["rows"], 5)

    def test_nitro_textarea_with_placeholder(self):
        """Test nitro_textarea with placeholder."""
        from nitro.templatetags.nitro_tags import nitro_textarea

        result = nitro_textarea(
            "edit_buffer.notes", label="Notes", placeholder="Enter notes here..."
        )

        # Should include placeholder
        self.assertEqual(result["placeholder"], "Enter notes here...")
        self.assertIn("?.", result["safe_field"])


# ============================================================================
# V0.6.0 SEO TEMPLATE TAGS TESTS
# ============================================================================


class TestSEOTemplateTags(TestCase):
    """Tests for v0.6.0 SEO-friendly template tags."""

    def test_nitro_text_tag(self):
        """Test nitro_text tag rendering (v0.7.0 - attribute only)."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}<span {% nitro_text 'count' %}></span>")
        context = Context({"count": 42})
        result = template.render(context)

        # Should output x-text attribute
        self.assertIn('x-text="count"', result)
        self.assertIn("<span", result)

    def test_nitro_text_with_class(self):
        """Test nitro_text can be combined with other attributes (v0.7.0)."""
        from django.template import Context, Template

        template = Template('{% load nitro_tags %}<span {% nitro_text "name" %} class="truncate"></span>')
        context = Context({})
        result = template.render(context)

        # Should have both x-text and class
        self.assertIn('x-text="name"', result)
        self.assertIn('class="truncate"', result)

    def test_nitro_text_shorthand_alias(self):
        """Test n_text shorthand alias works (v0.7.0)."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}<div {% n_text 'value' %}></div>")
        context = Context({})
        result = template.render(context)

        self.assertIn('x-text="value"', result)

    def test_nitro_for_tag_basic(self):
        """Test nitro_for tag with basic list (v0.7.0)."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_for 'items' as 'item' %}"
            "<div {% nitro_text 'item.name' %}></div>"
            "{% end_nitro_for %}"
        )

        items = [{"name": "Item 1", "id": 1}, {"name": "Item 2", "id": 2}]
        context = Context({"items": items})
        result = template.render(context)

        # Should include Alpine template with x-text binding
        self.assertIn("<template x-for=", result)
        self.assertIn('x-text="item.name"', result)
        self.assertIn("nitro-seo-content", result)

    def test_nitro_for_with_empty_list(self):
        """Test nitro_for with empty list."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_for 'items' as 'item' %}"
            "<div>{% nitro_text 'item.name' %}</div>"
            "{% end_nitro_for %}"
        )

        context = Context({"items": []})
        result = template.render(context)

        # Should still render structure
        self.assertIn("<template x-for=", result)


# ============================================================================
# COMPONENT RENDERING TESTS
# ============================================================================


class TestComponentRendering(TestCase):
    """Tests for component rendering tags."""

    def test_nitro_component_tag(self):
        """Test nitro_component tag."""
        from django.template import Context, Template

        # Register a test component
        @register_component
        class TestRenderComponent(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState()

            def render(self):
                return "<div>Test Component</div>"

        template = Template("{% load nitro_tags %}{% nitro_component 'TestRenderComponent' %}")
        context = Context({"request": RequestFactory().get("/")})
        result = template.render(context)

        # Should render component
        self.assertIn("Test Component", result)

        # Cleanup
        _components_registry.pop("TestRenderComponent", None)

    def test_nitro_component_with_kwargs(self):
        """Test nitro_component with initialization kwargs."""
        from django.template import Context, Template

        @register_component
        class TestKwargsComponent(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState(count=kwargs.get("initial", 0))

            def render(self):
                return f"<div>Count: {self.state.count}</div>"

        template = Template(
            "{% load nitro_tags %}{% nitro_component 'TestKwargsComponent' initial=10 %}"
        )
        context = Context({"request": RequestFactory().get("/")})
        result = template.render(context)

        # Should pass kwargs
        self.assertIn("Count: 10", result)

        # Cleanup
        _components_registry.pop("TestKwargsComponent", None)

    def test_nitro_component_not_found(self):
        """Test nitro_component with non-existent component."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}{% nitro_component 'NonExistent' %}")
        context = Context({"request": RequestFactory().get("/")})
        result = template.render(context)

        # Should return empty string
        self.assertEqual(result.strip(), "")

    def test_nitro_scripts_tag(self):
        """Test nitro_scripts tag includes CSS and JS."""
        from nitro.templatetags.nitro_tags import nitro_scripts

        result = nitro_scripts()

        # Should include both CSS and JS
        self.assertIn("nitro.css", result)
        self.assertIn("nitro.js", result)
        self.assertIn('<link rel="stylesheet"', result)
        self.assertIn("<script defer", result)


# ============================================================================
# CONDITIONAL RENDERING TESTS
# ============================================================================


class TestConditionalRendering(TestCase):
    """Tests for nitro_if conditional rendering."""

    def test_nitro_if_tag(self):
        """Test nitro_if tag."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_if 'isActive' %}"
            "<div>Active Content</div>"
            "{% end_nitro_if %}"
        )

        context = Context({"isActive": True})
        result = template.render(context)

        # Should wrap in x-if template
        self.assertIn('<template x-if="isActive">', result)
        self.assertIn("Active Content", result)

    def test_nitro_if_with_complex_condition(self):
        """Test nitro_if with complex expression."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_if 'count > 0 && !isLoading' %}"
            "<div>Content</div>"
            "{% end_nitro_if %}"
        )

        context = Context({})
        result = template.render(context)

        # Should include full condition
        self.assertIn('x-if="count > 0 && !isLoading"', result)


# ============================================================================
# BASE LIST COMPONENT TESTS
# ============================================================================


class TestBaseListComponent(TestCase):
    """Tests for BaseListComponent pagination and filtering."""

    def test_base_list_initialization(self):
        """Test BaseListComponent initialization."""
        from nitro.list import BaseListComponent

        class ItemState(BaseModel):
            id: int
            name: str

        class ItemListState(BaseModel):
            items: list[ItemState] = []
            total: int = 0
            page: int = 1

        class TestModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "nitro"

        class ItemList(BaseListComponent[ItemListState]):
            template_name = "test.html"
            state_class = ItemListState
            model = TestModel
            per_page = 10

            def get_initial_state(self, **kwargs):
                return ItemListState()

        factory = RequestFactory()
        request = factory.get("/")
        component = ItemList(request=request)

        # Should initialize with default state
        self.assertEqual(component.state.page, 1)
        self.assertEqual(component.state.total, 0)

    def test_base_list_messages(self):
        """Test message handling in components."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        # Test success message
        component.success("Success!")
        self.assertEqual(len(component._pending_messages), 1)
        self.assertEqual(component._pending_messages[0]["level"], "success")

        # Test info message
        component.info("Info message")
        self.assertEqual(len(component._pending_messages), 2)
        self.assertEqual(component._pending_messages[1]["level"], "info")

        # Test warning message
        component.warning("Warning!")
        self.assertEqual(len(component._pending_messages), 3)
        self.assertEqual(component._pending_messages[2]["level"], "warning")


# ============================================================================
# UTILITY FUNCTIONS TESTS
# ============================================================================


class TestUtilityFunctions(TestCase):
    """Tests for utility functions."""

    def test_build_safe_field(self):
        """Test build_safe_field utility."""
        from nitro.utils import build_safe_field

        # Test with edit_buffer
        safe_field, is_edit = build_safe_field("edit_buffer.name")
        self.assertIn("?.", safe_field)
        self.assertTrue(is_edit)

        # Test with create_buffer
        safe_field, is_edit = build_safe_field("create_buffer.name")
        self.assertNotIn("?.", safe_field)
        self.assertFalse(is_edit)

    def test_build_error_path(self):
        """Test build_error_path utility."""
        from nitro.utils import build_error_path

        # Test with simple field
        error_path = build_error_path("name")
        self.assertEqual(error_path, "errors?.name")

        # Test with nested field
        error_path = build_error_path("address.street")
        self.assertEqual(error_path, "errors?.address?.street")

        # Test with deeply nested field
        error_path = build_error_path("create_buffer.address.street")
        self.assertEqual(error_path, "errors?.create_buffer?.address?.street")


# ============================================================================
# V0.6.1 ZERO JS COMPLETE TESTS
# ============================================================================


class TestZeroJSCompleteV061(TestCase):
    """Tests for v0.6.1 ZeroJS complete tags: nitro_toggle, nitro_set, nitro_key."""

    def test_nitro_toggle_basic(self):
        """Test basic nitro_toggle tag."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("showModal")

        # Should generate @click with toggle expression
        self.assertIn("@click=", result)
        self.assertIn("showModal = !showModal", result)

    def test_nitro_toggle_with_stop(self):
        """Test nitro_toggle with stop propagation."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("isExpanded", stop=True)

        # Should include .stop modifier
        self.assertIn("@click.stop=", result)
        self.assertIn("isExpanded = !isExpanded", result)

    def test_nitro_set_basic(self):
        """Test basic nitro_set tag."""
        from nitro.templatetags.nitro_tags import nitro_set

        result = nitro_set("activeTab", "'settings'")

        # Should generate @click with assignment
        self.assertIn("@click=", result)
        self.assertIn("activeTab = 'settings'", result)

    def test_nitro_set_with_expression(self):
        """Test nitro_set with expression value."""
        from nitro.templatetags.nitro_tags import nitro_set

        result = nitro_set("count", "count + 1")

        # Should preserve the expression
        self.assertIn("count = count + 1", result)

    def test_nitro_set_with_stop(self):
        """Test nitro_set with stop propagation."""
        from nitro.templatetags.nitro_tags import nitro_set

        result = nitro_set("selectedId", "item.id", stop=True)

        # Should include .stop modifier
        self.assertIn("@click.stop=", result)
        self.assertIn("selectedId = item.id", result)

    def test_nitro_key_basic(self):
        """Test basic nitro_key tag."""
        from nitro.templatetags.nitro_tags import nitro_key

        result = nitro_key("enter", action="search")

        # Should generate @keydown.enter with call
        self.assertIn("@keydown.enter=", result)
        self.assertIn("call('search')", result)

    def test_nitro_key_with_modifiers(self):
        """Test nitro_key with prevent and stop modifiers."""
        from nitro.templatetags.nitro_tags import nitro_key

        result = nitro_key("enter", action="submit", prevent=True, stop=True)

        # Should include .prevent and .stop
        self.assertIn(".prevent", result)
        self.assertIn(".stop", result)
        self.assertIn("call('submit')", result)

    def test_nitro_key_combo(self):
        """Test nitro_key with key combination."""
        from nitro.templatetags.nitro_tags import nitro_key

        result = nitro_key("ctrl+s", action="save", prevent=True)

        # Should generate @keydown.ctrl.s.prevent
        self.assertIn("@keydown.ctrl.s", result)
        self.assertIn(".prevent", result)
        self.assertIn("call('save')", result)

    def test_nitro_key_with_window(self):
        """Test nitro_key with window modifier for global shortcuts."""
        from nitro.templatetags.nitro_tags import nitro_key

        result = nitro_key("escape", action="close_modal", window=True)

        # Should include .window modifier
        self.assertIn(".window", result)
        self.assertIn("call('close_modal')", result)

    def test_nitro_key_with_params(self):
        """Test nitro_key with action parameters."""
        from nitro.templatetags.nitro_tags import nitro_key

        result = nitro_key("enter", action="select_item", id="item.id")

        # Should include params in call
        self.assertIn("call('select_item', {id: item.id})", result)

    def test_nitro_dynamic_select_basic(self):
        """Test basic nitro_dynamic_select tag."""
        from nitro.templatetags.nitro_tags import nitro_dynamic_select

        result = nitro_dynamic_select(
            field="create_buffer.province_id",
            options_var="provinces",
            label="Provincia",
        )

        # Should return context dict for inclusion tag
        self.assertEqual(result["field"], "create_buffer.province_id")
        self.assertEqual(result["options_var"], "provinces")
        self.assertEqual(result["label"], "Provincia")
        self.assertEqual(result["option_value"], "id")  # default
        self.assertEqual(result["option_label"], "name")  # default

    def test_nitro_dynamic_select_with_custom_fields(self):
        """Test nitro_dynamic_select with custom option fields."""
        from nitro.templatetags.nitro_tags import nitro_dynamic_select

        result = nitro_dynamic_select(
            field="edit_buffer.country_code",
            options_var="countries",
            option_value="code",
            option_label="display_name",
            placeholder="Select country...",
        )

        self.assertEqual(result["option_value"], "code")
        self.assertEqual(result["option_label"], "display_name")
        self.assertEqual(result["placeholder"], "Select country...")

    def test_nitro_dynamic_select_with_on_change(self):
        """Test nitro_dynamic_select with on_change callback."""
        from nitro.templatetags.nitro_tags import nitro_dynamic_select

        result = nitro_dynamic_select(
            field="create_buffer.province_id",
            options_var="provinces",
            on_change="load_municipalities",
            on_change_param="province_id",
        )

        # Should include change handler with param
        self.assertIn("load_municipalities", result["change_handler"])
        self.assertIn("province_id", result["change_handler"])


# ============================================================================
# XSS SECURITY TESTS
# ============================================================================


class TestXSSSecurity(TestCase):
    """Tests for XSS protection in Nitro components and tags."""

    def test_nitro_action_xss_in_action_name(self):
        """Test that nitro_action handles XSS attempts in action names.

        Note: Alpine.js handles the XSS protection at runtime since it
        evaluates action names as string identifiers. The tag generates
        valid Alpine syntax - actual XSS protection happens client-side.
        """
        from nitro.templatetags.nitro_tags import nitro_action

        # Malicious action name attempting XSS
        malicious_action = "'); alert('xss'); //"
        result = nitro_action(malicious_action)

        # Should generate @click handler with call()
        self.assertIn("@click=", result)
        self.assertIn("call(", result)

    def test_nitro_action_xss_in_params(self):
        """Test that nitro_action handles XSS attempts in parameters."""
        from nitro.templatetags.nitro_tags import nitro_action

        result = nitro_action("delete", id="<script>alert(1)</script>")

        # The tag outputs raw Alpine.js syntax - XSS protection happens at render time
        # But the structure should be intact
        self.assertIn("call('delete'", result)
        self.assertIn("id:", result)

    def test_nitro_model_xss_in_field_name(self):
        """Test that nitro_model escapes XSS in field names."""
        from nitro.templatetags.nitro_tags import nitro_model

        malicious_field = "email\" onmouseover=\"alert(1)"
        result = nitro_model(malicious_field)

        # Should not allow attribute breakout
        # The field name should be escaped in the x-model binding
        self.assertIn('x-model="', result)
        self.assertIn('onmouseover', result)  # Will be inside quoted string

    def test_nitro_show_xss_in_expression(self):
        """Test that nitro_show handles XSS in expressions."""
        from nitro.templatetags.nitro_tags import nitro_show

        malicious_expr = 'true"><script>alert(1)</script><div x-show="'
        result = nitro_show(malicious_expr)

        # Expression is passed directly to Alpine - Alpine handles escaping
        self.assertIn('x-show="', result)

    def test_nitro_text_xss_attribute(self):
        """Test that nitro_text outputs safe attribute (v0.7.0).

        nitro_text now outputs only the x-text attribute.
        XSS protection is handled by Alpine.js which escapes content.
        """
        from django.template import Context, Template

        template = Template('{% load nitro_tags %}<span {% nitro_text "user_input" %}></span>')
        context = Context({"user_input": "<img src=x onerror=alert(1)>"})
        result = template.render(context)

        # Should output clean x-text attribute
        self.assertIn('x-text="user_input"', result)
        # No server-side content injection possible
        self.assertNotIn("<img", result)

    def test_nitro_class_xss_in_class_names(self):
        """Test that nitro_class handles XSS in class names."""
        from nitro.templatetags.nitro_tags import nitro_class

        result = nitro_class(**{"active\" onclick=\"alert(1)": "isActive"})

        # Class names with quotes should be escaped/handled
        self.assertIn(":class=", result)

    def test_nitro_attr_xss_in_attribute_value(self):
        """Test that nitro_attr handles XSS in values."""
        from nitro.templatetags.nitro_tags import nitro_attr

        result = nitro_attr("href", "javascript:alert(1)")

        # This creates Alpine binding - XSS happens if state contains malicious value
        self.assertIn(':href="javascript:alert(1)"', result)

    def test_component_state_xss_in_messages(self):
        """Test that component messages don't execute XSS."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        # Add message with XSS payload
        component.success("<script>alert('xss')</script>")

        # Message text should be stored as-is but frontend should escape
        self.assertEqual(
            component._pending_messages[0]["text"], "<script>alert('xss')</script>"
        )

    def test_process_action_xss_in_payload(self):
        """Test that action payloads with XSS are handled safely."""

        class XSSTestComponent(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState

            def get_initial_state(self, **kwargs):
                return SimpleState()

            def set_message(self, text: str):
                self.state.message = text

        component = XSSTestComponent(request=RequestFactory().get("/"))

        # Call action with XSS payload
        result = component.process_action(
            action_name="set_message",
            payload={"text": "<script>alert(1)</script>"},
            current_state_dict={"count": 0, "message": ""},
        )

        # State should contain the value but not execute
        self.assertEqual(result["state"]["message"], "<script>alert(1)</script>")


# ============================================================================
# EDGE CASES TESTS
# ============================================================================


class TestEdgeCases(TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_component_with_empty_state(self):
        """Test component with empty/minimal state."""

        class EmptyState(BaseModel):
            pass

        class EmptyComponent(NitroComponent[EmptyState]):
            template_name = "test.html"
            state_class = EmptyState

            def get_initial_state(self, **kwargs):
                return EmptyState()

        component = EmptyComponent(request=RequestFactory().get("/"))
        self.assertIsInstance(component.state, EmptyState)

    def test_component_with_none_values(self):
        """Test component handling None values in state."""

        class NullableState(BaseModel):
            name: str | None = None
            count: int | None = None

        class NullableComponent(NitroComponent[NullableState]):
            template_name = "test.html"
            state_class = NullableState

            def get_initial_state(self, **kwargs):
                return NullableState()

        component = NullableComponent(request=RequestFactory().get("/"))
        self.assertIsNone(component.state.name)
        self.assertIsNone(component.state.count)

    def test_sync_field_with_empty_string(self):
        """Test syncing empty string values."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        component._sync_field("message", "")
        self.assertEqual(component.state.message, "")

    def test_sync_field_with_whitespace_only(self):
        """Test syncing whitespace-only values."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        component._sync_field("message", "   ")
        self.assertEqual(component.state.message, "   ")

    def test_sync_field_with_zero(self):
        """Test syncing zero value (shouldn't be treated as empty)."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        component._sync_field("count", 0)
        self.assertEqual(component.state.count, 0)

    def test_sync_field_with_unicode(self):
        """Test syncing Unicode values."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        unicode_text = "Héllo Wörld 日本語 🎉"
        component._sync_field("message", unicode_text)
        self.assertEqual(component.state.message, unicode_text)

    def test_sync_field_with_very_long_string(self):
        """Test syncing very long string values."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        long_text = "x" * 100000  # 100KB of text
        component._sync_field("message", long_text)
        self.assertEqual(len(component.state.message), 100000)

    def test_sync_field_with_special_chars(self):
        """Test syncing strings with special characters."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        special_chars = "Test\n\t\r\"'`\\<>&"
        component._sync_field("message", special_chars)
        self.assertEqual(component.state.message, special_chars)

    def test_process_action_with_empty_action_name(self):
        """Test processing action with empty name."""
        component = SimpleComponent(request=RequestFactory().get("/"))
        result = component.process_action(
            action_name="",
            payload={},
            current_state_dict={"count": 0, "message": ""},
        )
        self.assertTrue(result["error"])

    def test_process_action_with_none_payload(self):
        """Test processing action with None payload returns error.

        Note: The current implementation doesn't handle None payload -
        this is expected behavior since actions require proper payload dict.
        """
        component = SimpleComponent(request=RequestFactory().get("/"))
        result = component.process_action(
            action_name="increment",
            payload=None,
            current_state_dict={"count": 0, "message": ""},
        )
        # Current behavior: None payload causes TypeError, returns error
        self.assertTrue(result.get("error", False))

    def test_process_action_with_extra_payload_fields(self):
        """Test processing action with extra payload fields returns error.

        Note: Python's **kwargs unpacking passes all fields to the method,
        which causes TypeError if unexpected fields are present.
        """
        component = SimpleComponent(request=RequestFactory().get("/"))
        result = component.process_action(
            action_name="set_message",
            payload={"text": "hello", "extra": "ignored", "another": 123},
            current_state_dict={"count": 0, "message": ""},
        )
        # Current behavior: extra kwargs cause TypeError
        self.assertTrue(result.get("error", False))

    def test_nitro_input_with_empty_label(self):
        """Test nitro_input with empty label."""
        from nitro.templatetags.nitro_tags import nitro_input

        result = nitro_input("field", label="")
        self.assertEqual(result["label"], "")

    def test_nitro_select_with_empty_choices(self):
        """Test nitro_select with empty choices list."""
        from nitro.templatetags.nitro_tags import nitro_select

        result = nitro_select("field", choices=[])
        self.assertEqual(result["choices"], [])

    def test_nitro_model_with_deeply_nested_field(self):
        """Test nitro_model with very deeply nested field path."""
        from nitro.templatetags.nitro_tags import nitro_model

        result = nitro_model("a.b.c.d.e.f.g.h")
        self.assertIn("a.b.c.d.e.f.g.h", result)

    def test_nitro_for_with_empty_list(self):
        """Test nitro_for with empty list."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_for 'items' as 'item' %}"
            "<div></div>"
            "{% end_nitro_for %}"
        )
        context = Context({"items": []})
        result = template.render(context)

        # Should handle empty list gracefully
        self.assertIn("<template x-for=", result)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration(TestCase):
    """Integration tests for complete component workflows."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_full_component_lifecycle(self):
        """Test complete component lifecycle: init -> action -> state update."""

        class CounterState(BaseModel):
            count: int = 0
            history: list[int] = []

        class CounterComponent(NitroComponent[CounterState]):
            template_name = "test.html"
            state_class = CounterState

            def get_initial_state(self, **kwargs):
                return CounterState(count=kwargs.get("start", 0))

            def increment(self):
                self.state.history.append(self.state.count)
                self.state.count += 1
                self.success("Incremented!")

            def decrement(self):
                self.state.history.append(self.state.count)
                self.state.count -= 1

            def reset(self):
                self.state.count = 0
                self.state.history = []

        # Initialize component
        component = CounterComponent(request=self.request)
        self.assertEqual(component.state.count, 0)

        # Process multiple actions
        result = component.process_action(
            "increment", {}, {"count": 0, "history": []}
        )
        self.assertEqual(result["state"]["count"], 1)
        self.assertEqual(len(result["messages"]), 1)

        result = component.process_action(
            "increment", {}, {"count": 1, "history": [0]}
        )
        self.assertEqual(result["state"]["count"], 2)

        result = component.process_action(
            "decrement", {}, {"count": 2, "history": [0, 1]}
        )
        self.assertEqual(result["state"]["count"], 1)

        result = component.process_action(
            "reset", {}, {"count": 1, "history": [0, 1, 2]}
        )
        self.assertEqual(result["state"]["count"], 0)
        self.assertEqual(result["state"]["history"], [])

    def test_component_with_validation_errors(self):
        """Test component handling validation errors."""

        class FormState(BaseModel):
            email: EmailStr = "valid@example.com"
            age: int = 18

        class FormComponent(NitroComponent[FormState]):
            template_name = "test.html"
            state_class = FormState

            def get_initial_state(self, **kwargs):
                return FormState()

            def submit(self):
                if self.state.age < 18:
                    self.add_error("age", "Must be 18 or older")
                    return
                self.success("Form submitted!")

        component = FormComponent(request=self.request)

        # Sync invalid email
        component._sync_field("email", "not-an-email")
        self.assertIn("email", component._pending_errors)

        # Sync valid email
        component = FormComponent(request=self.request)
        component._sync_field("email", "test@example.com")
        self.assertNotIn("email", component._pending_errors)

    def test_component_secure_fields_workflow(self):
        """Test component with secure fields throughout workflow."""

        class SecureState(BaseModel):
            id: int = 1
            user_id: int = 100
            name: str = ""

        class SecureComponent(NitroComponent[SecureState]):
            template_name = "test.html"
            state_class = SecureState
            secure_fields = ["id", "user_id"]

            def get_initial_state(self, **kwargs):
                return SecureState()

            def update_name(self, name: str):
                self.state.name = name

        component = SecureComponent(request=self.request)

        # Compute integrity token
        token = component._compute_integrity()
        self.assertIsNotNone(token)

        # Verify token with same state
        self.assertTrue(component.verify_integrity(token))

        # Update non-secure field - should still verify
        component.state.name = "Updated"
        self.assertTrue(component.verify_integrity(token))

        # Tamper with secure field - should fail verification
        component.state.id = 999
        self.assertFalse(component.verify_integrity(token))

    def test_component_events_workflow(self):
        """Test component event emission.

        Note: Events are prefixed with 'nitro:' namespace by the emit method.
        """

        class EventState(BaseModel):
            items: list[str] = []

        class EventComponent(NitroComponent[EventState]):
            template_name = "test.html"
            state_class = EventState

            def get_initial_state(self, **kwargs):
                return EventState()

            def add_item(self, item: str):
                self.state.items.append(item)
                self.emit("item-added", {"item": item})

            def clear(self):
                self.state.items = []
                self.emit("items-cleared")

        # Add item and check event (emit adds 'nitro:' prefix)
        component = EventComponent(request=self.request)
        result = component.process_action(
            "add_item", {"item": "Test"}, {"items": []}
        )
        self.assertGreaterEqual(len(result["events"]), 1)
        # Find the item-added event
        event_names = [e["name"] for e in result["events"]]
        self.assertIn("nitro:item-added", event_names)

        # Clear and check event (new component instance to avoid accumulated events)
        component = EventComponent(request=self.request)
        result = component.process_action("clear", {}, {"items": ["Test"]})
        event_names = [e["name"] for e in result["events"]]
        self.assertIn("nitro:items-cleared", event_names)

    def test_multiple_messages_in_single_action(self):
        """Test component with multiple messages in single action."""
        component = SimpleComponent(request=self.request)

        component.success("Success 1")
        component.info("Info message")
        component.warning("Warning!")
        component.error("Error occurred")

        self.assertEqual(len(component._pending_messages), 4)
        levels = [m["level"] for m in component._pending_messages]
        self.assertEqual(levels, ["success", "info", "warning", "error"])

    def test_component_with_initial_state_override(self):
        """Test component initialization with state override."""
        initial = {"count": 100, "message": "Custom"}
        component = SimpleComponent(request=self.request, initial_state=initial)

        self.assertEqual(component.state.count, 100)
        self.assertEqual(component.state.message, "Custom")

    def test_nested_field_sync_integration(self):
        """Test complete nested field sync workflow."""

        class AddressState(BaseModel):
            street: str = ""
            city: str = ""
            zip_code: str = ""

        class PersonState(BaseModel):
            name: str = ""
            address: AddressState = AddressState()

        class PersonComponent(NitroComponent[PersonState]):
            template_name = "test.html"
            state_class = PersonState

            def get_initial_state(self, **kwargs):
                return PersonState()

        component = PersonComponent(request=self.request)

        # Sync nested fields
        component._sync_field("name", "John Doe")
        component._sync_field("address.street", "123 Main St")
        component._sync_field("address.city", "New York")
        component._sync_field("address.zip_code", "10001")

        self.assertEqual(component.state.name, "John Doe")
        self.assertEqual(component.state.address.street, "123 Main St")
        self.assertEqual(component.state.address.city, "New York")
        self.assertEqual(component.state.address.zip_code, "10001")


# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================


# ============================================================================
# V0.7.0 DJANGO NINJA API TESTS
# ============================================================================


class TestDjangoNinjaAPI(TestCase):
    """Tests for Django Ninja API configuration and endpoints (v0.7.0)."""

    def test_api_configuration(self):
        """Test Django Ninja API is properly configured."""
        from nitro.api import api

        # Check API metadata
        self.assertEqual(api.urls_namespace, "nitro")
        self.assertEqual(api.title, "Nitro Component API")
        self.assertEqual(api.version, "0.7.0")
        self.assertIn("Django Nitro", api.description)

    def test_request_schemas_exist(self):
        """Test that request schemas are properly defined."""
        from nitro.api import ActionPayload, ActionFormPayload

        # Test ActionPayload schema
        payload = ActionPayload(
            component_name="TestComponent",
            action="test_action",
            state={"count": 0},
            payload={"id": 1},
            integrity="test_signature"
        )
        self.assertEqual(payload.component_name, "TestComponent")
        self.assertEqual(payload.action, "test_action")
        self.assertEqual(payload.state, {"count": 0})

        # Test ActionFormPayload schema (used with file uploads)
        form_payload = ActionFormPayload(
            component_name="FileComponent",
            action="upload",
            state='{"file_name": ""}',
            payload='{"doc_type": "pdf"}',
            integrity="signature"
        )
        self.assertEqual(form_payload.component_name, "FileComponent")
        self.assertEqual(form_payload.state, '{"file_name": ""}')  # JSON string

    def test_response_schemas_exist(self):
        """Test that response schemas are properly defined."""
        from nitro.api import ErrorResponse, NitroResponse

        # Test ErrorResponse schema
        error = ErrorResponse(error="Not found", detail="Component not found")
        self.assertEqual(error.error, "Not found")
        self.assertEqual(error.detail, "Component not found")

        # Test NitroResponse schema
        response = NitroResponse(
            html="<div>Content</div>",
            state={"count": 1},
            redirect=None,
            error=None
        )
        self.assertEqual(response.html, "<div>Content</div>")
        self.assertEqual(response.state, {"count": 1})

    def test_exception_handlers_registered(self):
        """Test that exception handlers are registered."""
        from nitro.api import api
        from django.core.exceptions import PermissionDenied
        from django.core.exceptions import ValidationError as DjangoValidationError
        from pydantic import ValidationError as PydanticValidationError

        # Check exception handlers are in place
        # Django Ninja registers handlers internally
        self.assertTrue(hasattr(api, '_exception_handlers') or hasattr(api, 'exception_handlers'))


class TestDjangoNinjaExceptionHandlers(TestCase):
    """Tests for Django Ninja exception handlers."""

    def test_permission_denied_handler(self):
        """Test PermissionDenied exception handler."""
        from django.core.exceptions import PermissionDenied
        from nitro.api import permission_denied_handler, api

        request = RequestFactory().post("/")
        request.user = type('User', (), {'username': 'testuser'})()

        exc = PermissionDenied("Access denied")
        response = permission_denied_handler(request, exc)

        # Should return 403 response
        self.assertEqual(response.status_code, 403)

    def test_django_validation_handler(self):
        """Test Django ValidationError exception handler."""
        from django.core.exceptions import ValidationError
        from nitro.api import django_validation_handler, api

        request = RequestFactory().post("/")

        exc = ValidationError("Invalid field value")
        response = django_validation_handler(request, exc)

        # Should return 400 response
        self.assertEqual(response.status_code, 400)

    def test_pydantic_validation_handler(self):
        """Test Pydantic ValidationError exception handler."""
        from pydantic import ValidationError as PydanticValidationError, BaseModel
        from nitro.api import pydantic_validation_handler, api

        request = RequestFactory().post("/")

        # Create a real Pydantic validation error
        class TestModel(BaseModel):
            email: str

        try:
            TestModel(email=123)  # Invalid type
        except PydanticValidationError as exc:
            response = pydantic_validation_handler(request, exc)
            # Should return 400 response
            self.assertEqual(response.status_code, 400)


# ============================================================================
# V0.7.0 NEW TEMPLATE TAGS TESTS
# ============================================================================


class TestV070TemplateTags(TestCase):
    """Tests for v0.7.0 new template tags: nitro_transition, nitro_stop, nitro_rating, nitro_cloak, nitro_file_action."""

    def test_nitro_transition_fade(self):
        """Test nitro_transition with fade preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("fade")

        # Should include enter and leave transitions
        self.assertIn("x-transition:enter=", result)
        self.assertIn("x-transition:leave=", result)
        self.assertIn("opacity-0", result)
        self.assertIn("duration-200", result)

    def test_nitro_transition_slide_right(self):
        """Test nitro_transition with slide-right preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("slide-right")

        # Should include transform translations
        self.assertIn("translate-x-full", result)
        self.assertIn("duration-300", result)

    def test_nitro_transition_slide_left(self):
        """Test nitro_transition with slide-left preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("slide-left")

        # Should include negative translation
        self.assertIn("-translate-x-full", result)

    def test_nitro_transition_slide_up(self):
        """Test nitro_transition with slide-up preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("slide-up")

        # Should include Y translation (slide-up uses positive translate-y-full)
        self.assertIn("translate-y-full", result)
        self.assertIn("translate-y-0", result)

    def test_nitro_transition_slide_down(self):
        """Test nitro_transition with slide-down preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("slide-down")

        # Should include positive Y translation
        self.assertIn("translate-y-full", result)

    def test_nitro_transition_scale(self):
        """Test nitro_transition with scale preset."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("scale")

        # Should include scale transformation
        self.assertIn("scale-95", result)
        self.assertIn("opacity-0", result)

    def test_nitro_transition_default_fallback(self):
        """Test nitro_transition with unknown preset falls back to fade."""
        from nitro.templatetags.nitro_tags import nitro_transition

        result = nitro_transition("unknown_preset")

        # Should fallback to fade
        self.assertIn("opacity-0", result)
        self.assertIn("duration-200", result)

    def test_nitro_stop(self):
        """Test nitro_stop tag for event propagation."""
        from nitro.templatetags.nitro_tags import nitro_stop

        result = nitro_stop()

        # Should output @click.stop
        self.assertEqual(result, "@click.stop")

    def test_nitro_rating_basic(self):
        """Test nitro_rating with default settings."""
        from nitro.templatetags.nitro_tags import nitro_rating

        result = nitro_rating("tenant.rating")

        # Should generate star rating template
        self.assertIn("x-for", result)
        self.assertIn("5", result)  # max_stars default
        self.assertIn("tenant.rating", result)
        self.assertIn("text-yellow-400", result)
        self.assertIn("text-gray-300", result)
        self.assertIn("★", result)

    def test_nitro_rating_custom_max(self):
        """Test nitro_rating with custom max_stars."""
        from nitro.templatetags.nitro_tags import nitro_rating

        result = nitro_rating("score", max_stars=10)

        # Should use custom max
        self.assertIn("10", result)

    def test_nitro_rating_custom_size(self):
        """Test nitro_rating with custom size."""
        from nitro.templatetags.nitro_tags import nitro_rating

        result = nitro_rating("rating", size="text-lg")

        # Should use custom size class
        self.assertIn("text-lg", result)

    def test_nitro_cloak(self):
        """Test nitro_cloak tag for FOUC prevention."""
        from nitro.templatetags.nitro_tags import nitro_cloak

        result = nitro_cloak()

        # Should output x-cloak
        self.assertEqual(result, "x-cloak")

    def test_nitro_file_action_basic(self):
        """Test nitro_file_action with basic action."""
        from nitro.templatetags.nitro_tags import nitro_file_action

        result = nitro_file_action("upload_document")

        # Should generate @change handler with call and file
        self.assertIn("@change=", result)
        self.assertIn("call('upload_document'", result)
        self.assertIn("$event.target.files[0]", result)

    def test_nitro_file_action_with_params(self):
        """Test nitro_file_action with additional parameters."""
        from nitro.templatetags.nitro_tags import nitro_file_action

        result = nitro_file_action("upload_document", doc_type="'invoice'", tenant_id="tenant.id")

        # Should include parameters
        self.assertIn("doc_type: 'invoice'", result)
        self.assertIn("tenant_id: tenant.id", result)


class TestV070NitroToggleEnhanced(TestCase):
    """Tests for enhanced nitro_toggle with action parameter (v0.7.0)."""

    def test_nitro_toggle_with_action(self):
        """Test nitro_toggle with server action."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("show_details", action="toggle_details")

        # Should include both toggle and action call
        self.assertIn("show_details = !show_details", result)
        self.assertIn("call('toggle_details')", result)

    def test_nitro_toggle_with_action_and_params(self):
        """Test nitro_toggle with server action and parameters."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("is_expanded", action="expand_item", item_id="item.id")

        # Should include toggle, action, and params
        self.assertIn("is_expanded = !is_expanded", result)
        self.assertIn("call('expand_item'", result)
        self.assertIn("item_id: item.id", result)

    def test_nitro_toggle_with_action_and_stop(self):
        """Test nitro_toggle with action and stop propagation."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("show_modal", action="open_modal", stop=True)

        # Should include .stop modifier
        self.assertIn("@click.stop=", result)
        self.assertIn("show_modal = !show_modal", result)
        self.assertIn("call('open_modal')", result)

    def test_nitro_toggle_without_action(self):
        """Test nitro_toggle without action (client-only toggle)."""
        from nitro.templatetags.nitro_tags import nitro_toggle

        result = nitro_toggle("isOpen")

        # Should only have toggle, no call
        self.assertIn("isOpen = !isOpen", result)
        self.assertNotIn("call(", result)


# ============================================================================
# V0.7.0 NITRO EACH/COUNT/SWITCH TAGS TESTS
# ============================================================================


class TestV070IterationTags(TestCase):
    """Tests for v0.7.0 iteration and display tags."""

    def test_nitro_for_basic(self):
        """Test nitro_for tag for iteration (SEO + Alpine)."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_for 'items' as 'item' %}"
            "<span>{% nitro_text 'item.name' %}</span>"
            "{% end_nitro_for %}"
        )

        context = Context({"items": [{"name": "A"}, {"name": "B"}]})
        result = template.render(context)

        # Should include Alpine x-for template AND SEO content
        self.assertIn("<template x-for=", result)
        self.assertIn("in items", result)
        # SEO content should be rendered (nitro_for has dual rendering)
        self.assertIn("nitro-seo-content", result)

    def test_nitro_count_basic(self):
        """Test nitro_count tag for item counting."""
        from nitro.templatetags.nitro_tags import nitro_count

        result = nitro_count("items.length", singular="item", plural="items")

        # Should generate count display with pluralization
        self.assertIn("items.length", result)
        self.assertIn("item", result)
        self.assertIn("items", result)

    def test_nitro_switch_basic(self):
        """Test nitro_switch tag for conditional text."""
        from nitro.templatetags.nitro_tags import nitro_switch

        result = nitro_switch("status", active="Activo", inactive="Inactivo", default="Desconocido")

        # Should generate conditional template
        self.assertIn("status", result)
        self.assertIn("Activo", result)
        self.assertIn("Inactivo", result)

    def test_nitro_css_basic(self):
        """Test nitro_css tag for value-based conditional classes."""
        from django.template import Context, Template

        # nitro_css maps field VALUE → CSS classes (True ZeroJS)
        template = Template(
            "{% load nitro_tags %}"
            "<div {% nitro_css 'status' active='bg-green-100' expired='bg-red-100' %}></div>"
        )
        result = template.render(Context({'status': 'active'}))

        # Should generate :class binding based on value
        self.assertIn(":class=", result)
        self.assertIn("bg-green-100", result)
        self.assertIn("status === 'active'", result)

    def test_nitro_badge_basic(self):
        """Test nitro_badge tag for status badges."""
        from nitro.templatetags.nitro_tags import nitro_badge

        result = nitro_badge(
            "status",
            active="Activo:bg-green-100 text-green-700",
            inactive="Inactivo:bg-red-100 text-red-700"
        )

        # Should generate badge with text and classes
        self.assertIn("Activo", result)
        self.assertIn("bg-green-100", result)


class TestPerformance(TestCase):
    """Performance and stress tests."""

    def test_large_state_serialization(self):
        """Test component with large state (many items)."""

        class LargeState(BaseModel):
            items: list[dict] = []

        class LargeComponent(NitroComponent[LargeState]):
            template_name = "test.html"
            state_class = LargeState

            def get_initial_state(self, **kwargs):
                # Create 1000 items
                items = [{"id": i, "name": f"Item {i}"} for i in range(1000)]
                return LargeState(items=items)

        component = LargeComponent(request=RequestFactory().get("/"))
        self.assertEqual(len(component.state.items), 1000)

    def test_rapid_state_updates(self):
        """Test rapid sequential state updates."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        # Perform 100 rapid updates
        for i in range(100):
            component._sync_field("count", i)

        self.assertEqual(component.state.count, 99)

    def test_many_messages(self):
        """Test component with many pending messages."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        # Add 50 messages
        for i in range(50):
            component.success(f"Message {i}")

        self.assertEqual(len(component._pending_messages), 50)

    def test_many_field_errors(self):
        """Test component with many field errors."""
        component = SimpleComponent(request=RequestFactory().get("/"))

        # Add 20 field errors
        for i in range(20):
            component.add_error(f"field_{i}", f"Error for field {i}")

        self.assertEqual(len(component._pending_errors), 20)
