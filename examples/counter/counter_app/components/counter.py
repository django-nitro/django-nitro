from pydantic import BaseModel
from nitro.base import NitroComponent
from nitro.registry import register_component


class CounterState(BaseModel):
    """State schema for the counter component."""
    count: int = 0
    step: int = 1


@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState

    def get_initial_state(self, **kwargs):
        """Initialize the component state."""
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

    def increment(self):
        """Action: increment the counter."""
        self.state.count += self.state.step
        self.success(f"Count increased to {self.state.count}")

    def decrement(self):
        """Action: decrement the counter."""
        self.state.count -= self.state.step
        self.success(f"Count decreased to {self.state.count}")

    def reset(self):
        """Action: reset to zero."""
        self.state.count = 0
        self.success("Counter reset to 0")
