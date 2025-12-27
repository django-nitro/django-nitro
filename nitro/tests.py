from django.test import TestCase, RequestFactory
from django.db import models
from pydantic import BaseModel
from nitro.base import NitroComponent, ModelNitroComponent
from nitro.registry import register_component, get_component_class, _component_registry


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
        self.request = self.factory.get('/')

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
            action_name="increment",
            payload={},
            current_state_dict={"count": 0, "message": ""}
        )
        self.assertEqual(result["state"]["count"], 1)

    def test_process_action_with_parameters(self):
        """Test actions with parameters."""
        component = SimpleComponent(request=self.request)
        result = component.process_action(
            action_name="set_message",
            payload={"text": "test message"},
            current_state_dict={"count": 0, "message": ""}
        )
        self.assertEqual(result["state"]["message"], "test message")

    def test_process_action_invalid(self):
        """Test that invalid action raises ValueError."""
        component = SimpleComponent(request=self.request)
        with self.assertRaises(ValueError):
            component.process_action(
                action_name="nonexistent_action",
                payload={},
                current_state_dict={"count": 0, "message": ""}
            )

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
        _component_registry.clear()

    def tearDown(self):
        # Clear registry after each test
        _component_registry.clear()

    def test_register_component(self):
        """Test component registration."""
        @register_component
        class TestComp(NitroComponent[SimpleState]):
            template_name = "test.html"
            state_class = SimpleState
            def get_initial_state(self, **kwargs):
                return SimpleState()

        self.assertIn("TestComp", _component_registry)
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
                app_label = 'nitro'

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
        self.assertIn('id', component.secure_fields)
        self.assertIn('property_id', component.secure_fields)
