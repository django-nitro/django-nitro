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

        result = nitro_action("delete", id="item.id", confirm="true")

        # Should include all parameters
        self.assertIn("call('delete'", result)
        self.assertIn("id: item.id", result)
        self.assertIn("confirm: true", result)

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
        """Test nitro_text tag rendering."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}{% nitro_text 'count' %}")
        context = Context({"count": 42})
        result = template.render(context)

        # Should include both server-rendered value and x-text binding
        self.assertIn("42", result)
        self.assertIn('x-text="count"', result)
        self.assertIn("<span", result)

    def test_nitro_text_with_missing_variable(self):
        """Test nitro_text with non-existent variable."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}{% nitro_text 'missing' %}")
        context = Context({})
        result = template.render(context)

        # Should render empty but include binding
        self.assertIn('x-text="missing"', result)

    def test_nitro_text_escapes_html(self):
        """Test nitro_text escapes HTML for XSS protection."""
        from django.template import Context, Template

        template = Template("{% load nitro_tags %}{% nitro_text 'value' %}")
        context = Context({"value": "<script>alert('xss')</script>"})
        result = template.render(context)

        # Should escape HTML in server-rendered content
        self.assertIn("&lt;script&gt;", result)
        self.assertNotIn("<script>", result)

    def test_nitro_for_tag_basic(self):
        """Test nitro_for tag with basic list."""
        from django.template import Context, Template

        template = Template(
            "{% load nitro_tags %}"
            "{% nitro_for 'items' as 'item' %}"
            "<div>{% nitro_text 'item.name' %}</div>"
            "{% end_nitro_for %}"
        )

        items = [{"name": "Item 1", "id": 1}, {"name": "Item 2", "id": 2}]
        context = Context({"items": items})
        result = template.render(context)

        # Should include both SEO content and Alpine template
        self.assertIn("Item 1", result)
        self.assertIn("Item 2", result)
        self.assertIn('<template x-for=', result)
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
        self.assertIn('<template x-for=', result)


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
