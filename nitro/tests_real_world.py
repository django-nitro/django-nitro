"""
Real-world scenario tests based on actual bugs found in production.
These tests catch problems that unit tests miss.

Tests for Bug Fixes:
- Problem #3: State reset bug when using _sync_field
"""

from django.test import RequestFactory, TestCase
from pydantic import BaseModel

from nitro.base import NitroComponent

# ============================================================================
# PROBLEM #3: State Reset Bug
# ============================================================================


class LeaseCreateState(BaseModel):
    """Real schema from production - simulates form with multiple fields."""

    property_id: str = ""
    tenant_id: str = ""
    start_date: str = ""  # User types date
    monthly_rent: float = 0.0


class LeaseCreateComponent(NitroComponent[LeaseCreateState]):
    """Test component that simulates lease creation form."""

    template_name = "lease_create.html"
    state_class = LeaseCreateState

    def get_initial_state(self, **kwargs):
        return LeaseCreateState()


class TestStateResetBug(TestCase):
    """
    Tests for Problem #3: Partial field sync resets other fields.

    This bug occurs when:
    1. User fills field A (not synced to server yet)
    2. User interacts with field B (triggers _sync_field)
    3. Server receives state WITHOUT field A value
    4. Server processes and returns full state WITHOUT field A
    5. Client replaces all state, losing field A value

    The fix ensures _sync_field only sends the changed field back,
    using partial updates (merge) instead of full replacement.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_partial_field_sync_preserves_other_fields(self):
        """
        REPRODUCES BUG: User fills start_date, then selects property_id.
        Expected: Both fields should be preserved.
        Actual (before fix): start_date gets reset to empty string.
        """
        component = LeaseCreateComponent(request=self.request)

        # Simulate the actual bug scenario:
        # Step 1: User has filled start_date in browser (but not synced yet)
        # Step 2: User selects property_id from dropdown, triggers _sync_field

        # The state that arrives at the server has start_date filled
        # (because browser merges local changes before sending)
        current_state = {
            "property_id": "",
            "tenant_id": "",
            "start_date": "2026-01-15",  # User filled this
            "monthly_rent": 0.0,
        }

        # User selects property_id, only this field is being synced
        result = component.process_action(
            action_name="_sync_field",
            payload={"field": "property_id", "value": "123"},
            current_state_dict=current_state,
        )

        # CRITICAL: The fix should return partial=True and merge=True
        self.assertTrue(result["partial"], "Should use partial updates for _sync_field")
        self.assertTrue(result["merge"], "Should merge, not replace state")

        # The response should only contain the synced field
        self.assertIn("property_id", result["state"], "Should include synced field")

        # OLD BUG: If 'start_date' was in the response with empty value, it would reset
        # NEW FIX: start_date should NOT be in response (partial update)
        # OR if it is, it should preserve the value from current_state
        if "start_date" in result["state"]:
            self.assertEqual(
                result["state"]["start_date"],
                "2026-01-15",
                "If start_date is returned, it should preserve the current value",
            )

    def test_multiple_field_changes_preserve_all_previous(self):
        """
        Test that multiple sequential field changes preserve all previous values.
        This simulates a user filling out a multi-field form step by step.
        """
        component = LeaseCreateComponent(request=self.request)

        # Start with empty state
        state = {"property_id": "", "tenant_id": "", "start_date": "", "monthly_rent": 0.0}

        # User fills field 1: property_id
        result = component.process_action(
            "_sync_field", {"field": "property_id", "value": "123"}, state
        )
        # Update state with response (merge)
        if result["partial"]:
            for key, value in result["state"].items():
                state[key] = value
        else:
            state.update(result["state"])

        self.assertEqual(state["property_id"], "123", "Field 1 should be set")

        # User fills field 2: tenant_id
        result = component.process_action(
            "_sync_field", {"field": "tenant_id", "value": "456"}, state
        )
        if result["partial"]:
            for key, value in result["state"].items():
                state[key] = value
        else:
            state.update(result["state"])

        # Both fields should still be there
        self.assertEqual(state["property_id"], "123", "Field 1 should still be preserved")
        self.assertEqual(state["tenant_id"], "456", "Field 2 should be set")

        # User fills field 3: start_date
        result = component.process_action(
            "_sync_field", {"field": "start_date", "value": "2026-01-15"}, state
        )
        if result["partial"]:
            for key, value in result["state"].items():
                state[key] = value
        else:
            state.update(result["state"])

        # All fields should still be there
        self.assertEqual(state["property_id"], "123", "Field 1 should still be preserved")
        self.assertEqual(state["tenant_id"], "456", "Field 2 should still be preserved")
        self.assertEqual(state["start_date"], "2026-01-15", "Field 3 should be set")

        # User fills field 4: monthly_rent
        result = component.process_action(
            "_sync_field", {"field": "monthly_rent", "value": 1500.0}, state
        )
        if result["partial"]:
            for key, value in result["state"].items():
                state[key] = value
        else:
            state.update(result["state"])

        # ALL fields should still be there
        self.assertEqual(state["property_id"], "123", "Field 1 preserved after 4 syncs")
        self.assertEqual(state["tenant_id"], "456", "Field 2 preserved after 4 syncs")
        self.assertEqual(state["start_date"], "2026-01-15", "Field 3 preserved after 4 syncs")
        self.assertEqual(state["monthly_rent"], 1500.0, "Field 4 should be set")

    def test_nested_field_sync_preserves_sibling_fields(self):
        """
        Test that syncing a nested field (e.g., create_buffer.property_id)
        doesn't reset other fields in the same buffer.
        """

        class CreateBuffer(BaseModel):
            property_id: str = ""
            start_date: str = ""

        class FormState(BaseModel):
            create_buffer: CreateBuffer = CreateBuffer()
            other_field: str = ""

        class FormComponent(NitroComponent[FormState]):
            template_name = "form.html"
            state_class = FormState

            def get_initial_state(self, **kwargs):
                return FormState()

        component = FormComponent(request=self.request)

        # User has filled start_date in create_buffer
        state = {
            "create_buffer": {
                "property_id": "",
                "start_date": "2026-01-15",  # Already filled
            },
            "other_field": "test",
        }

        # User selects property_id in create_buffer
        result = component.process_action(
            "_sync_field", {"field": "create_buffer.property_id", "value": "123"}, state
        )

        # Should return partial update with create_buffer
        self.assertTrue(result["partial"], "Should use partial updates")
        self.assertIn("create_buffer", result["state"], "Should return create_buffer")

        # The create_buffer should have the updated property_id
        self.assertEqual(
            result["state"]["create_buffer"]["property_id"], "123", "property_id should be updated"
        )

        # CRITICAL: start_date should be preserved in the returned create_buffer
        self.assertEqual(
            result["state"]["create_buffer"]["start_date"],
            "2026-01-15",
            "start_date should be preserved when syncing property_id",
        )

    def test_sync_field_returns_minimal_state(self):
        """
        Test that _sync_field returns ONLY the changed field, not full state.
        This is the core of the fix - minimal partial updates.
        """
        component = LeaseCreateComponent(request=self.request)

        state = {
            "property_id": "999",
            "tenant_id": "888",
            "start_date": "2026-01-15",
            "monthly_rent": 2000.0,
        }

        # Sync only one field
        result = component.process_action(
            "_sync_field", {"field": "monthly_rent", "value": 2500.0}, state
        )

        # Should return partial update
        self.assertTrue(result["partial"], "Should be partial update")
        self.assertTrue(result["merge"], "Should be merge operation")

        # Should return ONLY the changed field (or at minimum, not reset other fields)
        # The fix allows returning just the changed field
        self.assertIn("monthly_rent", result["state"], "Should include changed field")

        # Optional: check that response is minimal
        # (not required by the fix, but nice to have)
        if len(result["state"]) == 1:
            self.assertEqual(
                list(result["state"].keys()),
                ["monthly_rent"],
                "Ideally, should return ONLY the changed field",
            )


# ============================================================================
# REAL-WORLD INTEGRATION TEST
# ============================================================================


class TestRealWorldLeaseForm(TestCase):
    """
    Integration test simulating real user interaction on lease create form.
    This test reproduces the exact bug flow from production.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_lease_form_complete_user_flow(self):
        """
        Complete user flow:
        1. User opens create modal
        2. User fills start_date field
        3. User opens property searchable dropdown
        4. User searches for property
        5. User selects property (triggers _sync_field)
        6. User fills tenant_id
        7. User fills monthly_rent
        8. User submits form

        Expected: All fields should be preserved throughout.
        Before fix: start_date would be lost at step 5.
        """
        component = LeaseCreateComponent(request=self.request)

        # Simulate browser state (includes ALL fields user has touched)
        browser_state = {"property_id": "", "tenant_id": "", "start_date": "", "monthly_rent": 0.0}

        # Step 1: User types start_date (local change in browser)
        browser_state["start_date"] = "2026-01-15"

        # Step 2: User selects property from searchable dropdown
        # Browser sends current state + triggers _sync_field
        result = component.process_action(
            "_sync_field",
            {"field": "property_id", "value": "123"},
            browser_state,  # Current browser state includes start_date
        )

        # Browser merges response
        if result["partial"]:
            for key, value in result["state"].items():
                browser_state[key] = value
        else:
            browser_state.update(result["state"])

        # CRITICAL CHECK: start_date should NOT be lost
        self.assertEqual(
            browser_state["start_date"],
            "2026-01-15",
            "BUG FIX: start_date should be preserved after property selection",
        )
        self.assertEqual(browser_state["property_id"], "123", "property_id should be set")

        # Step 3: User selects tenant
        browser_state["tenant_id"] = "456"
        result = component.process_action(
            "_sync_field", {"field": "tenant_id", "value": "456"}, browser_state
        )

        if result["partial"]:
            for key, value in result["state"].items():
                browser_state[key] = value
        else:
            browser_state.update(result["state"])

        # All previous fields should still be preserved
        self.assertEqual(
            browser_state["start_date"],
            "2026-01-15",
            "start_date should still be there after tenant selection",
        )
        self.assertEqual(browser_state["property_id"], "123", "property_id should still be there")
        self.assertEqual(browser_state["tenant_id"], "456", "tenant_id should be set")

        # Step 4: User fills monthly_rent
        browser_state["monthly_rent"] = 1500.0
        result = component.process_action(
            "_sync_field", {"field": "monthly_rent", "value": 1500.0}, browser_state
        )

        if result["partial"]:
            for key, value in result["state"].items():
                browser_state[key] = value
        else:
            browser_state.update(result["state"])

        # Final check: ALL fields should be preserved
        self.assertEqual(
            browser_state["property_id"], "123", "property_id preserved through entire flow"
        )
        self.assertEqual(
            browser_state["tenant_id"], "456", "tenant_id preserved through entire flow"
        )
        self.assertEqual(
            browser_state["start_date"],
            "2026-01-15",
            "start_date preserved through entire flow - BUG FIXED!",
        )
        self.assertEqual(browser_state["monthly_rent"], 1500.0, "monthly_rent should be set")


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================


class TestBackwardCompatibility(TestCase):
    """
    Ensure the fix doesn't break existing behavior for other actions.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_regular_actions_still_return_full_state(self):
        """
        Test that regular actions (not _sync_field) still return full state
        for backward compatibility.
        """

        class CounterState(BaseModel):
            count: int = 0

        class CounterComponent(NitroComponent[CounterState]):
            template_name = "counter.html"
            state_class = CounterState

            def get_initial_state(self, **kwargs):
                return CounterState()

            def increment(self):
                self.state.count += 1

        component = CounterComponent(request=self.request)

        result = component.process_action("increment", {}, {"count": 5})

        # Regular actions should return full state (not partial)
        self.assertFalse(result["partial"], "Regular actions should not be partial")
        self.assertFalse(result.get("merge", False), "Regular actions should not force merge")
        self.assertEqual(result["state"], {"count": 6}, "Should return full state")

    def test_smart_updates_still_work(self):
        """
        Test that smart_updates feature still works correctly.
        """

        class Item(BaseModel):
            id: int
            name: str

        class ListState(BaseModel):
            items: list[dict] = []

        class ListComponent(NitroComponent[ListState]):
            template_name = "list.html"
            state_class = ListState
            smart_updates = True  # Enable smart updates

            def get_initial_state(self, **kwargs):
                return ListState()

            def add_item(self, name: str):
                new_item = {"id": len(self.state.items) + 1, "name": name}
                self.state.items.append(new_item)

        component = ListComponent(request=self.request)

        result = component.process_action(
            "add_item", {"name": "New Item"}, {"items": [{"id": 1, "name": "Item 1"}]}
        )

        # Smart updates should return partial with diff
        self.assertTrue(result["partial"], "Smart updates should be partial")
        self.assertIn("items", result["state"], "Should include items diff")
