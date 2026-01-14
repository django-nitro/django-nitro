"""
Django management command to scaffold Nitro components.

Usage:
    python manage.py startnitro ComponentName --app myapp [--list] [--crud]
"""

import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a new Nitro component with boilerplate code"

    def add_arguments(self, parser):
        parser.add_argument(
            "component_name",
            type=str,
            help="Name of the component (e.g., PropertyList, UserProfile)",
        )
        parser.add_argument(
            "--app", type=str, required=True, help="Django app where the component will be created"
        )
        parser.add_argument(
            "--list", action="store_true", help="Create a list component with pagination and search"
        )
        parser.add_argument(
            "--crud", action="store_true", help="Create a CRUD component (implies --list)"
        )

    def handle(self, *args, **options):
        component_name = options["component_name"]
        app_name = options["app"]
        is_list = options["list"] or options["crud"]
        is_crud = options["crud"]

        # Validate component name
        if not component_name[0].isupper():
            raise CommandError("Component name must start with an uppercase letter")

        # Find app directory
        app_dir = self._find_app_dir(app_name)
        if not app_dir:
            raise CommandError(f'App "{app_name}" not found')

        # Create components directory
        components_dir = os.path.join(app_dir, "components")
        os.makedirs(components_dir, exist_ok=True)

        # Create __init__.py if not exists
        init_file = os.path.join(components_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Components package\n")

        # Create component file
        snake_name = self._to_snake_case(component_name)
        component_file = os.path.join(components_dir, f"{snake_name}.py")
        if os.path.exists(component_file):
            raise CommandError(f"Component file already exists: {component_file}")

        # Create templates directory
        templates_dir = os.path.join(app_dir, "templates", "components")
        os.makedirs(templates_dir, exist_ok=True)

        # Create template file
        template_file = os.path.join(templates_dir, f"{snake_name}.html")

        # Generate component code
        if is_list or is_crud:
            component_code = self._generate_list_component(component_name, is_crud)
            template_code = self._generate_list_template(component_name)
        else:
            component_code = self._generate_simple_component(component_name, snake_name)
            template_code = self._generate_simple_template(component_name)

        # Write files
        with open(component_file, "w") as f:
            f.write(component_code)

        with open(template_file, "w") as f:
            f.write(template_code)

        self.stdout.write(self.style.SUCCESS(f"✓ Created component: {component_file}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template_file}"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Edit the component and state schema")
        self.stdout.write(f"2. Use in template: {{% nitro_component '{component_name}' %}}")

    def _find_app_dir(self, app_name):
        """Find the directory of a Django app."""
        for app in settings.INSTALLED_APPS:
            if app.split(".")[-1] == app_name:
                try:
                    module = __import__(app, fromlist=[""])
                    return os.path.dirname(module.__file__)
                except ImportError:
                    continue

        # Try BASE_DIR
        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir:
            potential_path = os.path.join(base_dir, app_name)
            if os.path.isdir(potential_path):
                return potential_path

        return None

    def _to_snake_case(self, name):
        """Convert CamelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _generate_simple_component(self, component_name, snake_name):
        """Generate code for a simple component."""
        return f'''from pydantic import BaseModel
from nitro import NitroComponent, register_component


class {component_name}State(BaseModel):
    """State schema for {component_name} component."""
    message: str = ""


@register_component
class {component_name}(NitroComponent[{component_name}State]):
    """
    {component_name} component.

    Usage:
        {{% nitro_component '{component_name}' %}}
    """
    template_name = "components/{snake_name}.html"
    state_class = {component_name}State

    def get_initial_state(self, **kwargs):
        """Initialize component state."""
        return {component_name}State(
            message=kwargs.get('message', 'Hello from {component_name}!')
        )

    def example_action(self):
        """Example action method."""
        self.state.message = "Action executed!"
        self.success("Action completed successfully")
'''

    def _generate_simple_template(self, component_name):
        """Generate template for a simple component."""
        return f"""<!-- {component_name} Component Template -->
<div>
    <h2>{component_name}</h2>

    <p x-text="message"></p>

    <button
        @click="call('example_action')"
        :disabled="isLoading"
        class="btn"
    >
        <span x-show="!isLoading">Execute Action</span>
        <span x-show="isLoading">Loading...</span>
    </button>
</div>
"""

    def _generate_list_component(self, component_name, is_crud):
        """Generate code for a list component."""
        snake_name = self._to_snake_case(component_name)
        model_name = component_name.replace("List", "")
        snake_component = snake_name  # For use in f-string

        return f'''from pydantic import BaseModel, ConfigDict, Field
from nitro import BaseListComponent, BaseListState, register_component
# from {snake_name}.models import {model_name}


class {model_name}Schema(BaseModel):
    """Schema for {model_name} item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    # TODO: Add more fields


class {model_name}FormSchema(BaseModel):
    """Form schema for creating/editing {model_name}."""
    name: str = ""
    # TODO: Add more fields


class {component_name}State(BaseListState):
    """State schema for {component_name} component."""
    items: list[{model_name}Schema] = []
    create_buffer: {model_name}FormSchema = Field(default_factory={model_name}FormSchema)
    edit_buffer: {model_name}FormSchema | None = None


@register_component
class {component_name}(BaseListComponent[{component_name}State]):
    """
    {component_name} component with pagination, search, and CRUD.

    Usage:
        {{% nitro_component '{component_name}' %}}
    """
    template_name = "components/{snake_component}.html"
    state_class = {component_name}State
    # model = {model_name}  # TODO: Uncomment and import model

    # Configure search and pagination
    search_fields = ['name']  # TODO: Adjust search fields
    per_page = 20
    order_by = '-id'

    def get_base_queryset(self, search='', filters=None):
        """Override to add custom filtering or annotations."""
        qs = self.model.objects.all()

        if search:
            qs = self.apply_search(qs, search)

        if filters:
            qs = self.apply_filters(qs, filters)

        return qs.order_by(self.order_by)

    def create_item(self):
        """Override to add custom create logic."""
        super().create_item()
        self.success("Item created successfully")

    def delete_item(self, id: int):
        """Override to add custom delete logic."""
        super().delete_item(id)
        self.success("Item deleted successfully")
'''

    def _generate_list_template(self, component_name):
        """Generate template for a list component."""
        return f"""<!-- {component_name} Component Template -->
<div>
    <h2>{component_name}</h2>

    <!-- Search bar -->
    <div class="mb-4">
        <input
            type="text"
            x-model="search"
            @input.debounce.300ms="call('search_items', {{search: $el.value}})"
            placeholder="Search..."
            class="border rounded px-4 py-2 w-full"
        >
    </div>

    <!-- Create form -->
    <div class="mb-4 p-4 bg-gray-50 rounded">
        <h3>Add New Item</h3>
        <input
            type="text"
            x-model="create_buffer.name"
            placeholder="Name"
            class="border rounded px-4 py-2 w-full mb-2"
        >
        <!-- TODO: Add more form fields -->

        <button
            @click="call('create_item')"
            :disabled="isLoading"
            class="bg-blue-500 text-white px-4 py-2 rounded"
        >
            Create
        </button>
    </div>

    <!-- Items list -->
    <div class="space-y-2">
        <template x-for="item in items" :key="item.id">
            <div class="border rounded p-4 flex justify-between items-center">
                <div>
                    <span x-text="item.name"></span>
                </div>
                <div class="space-x-2">
                    <button
                        @click="call('start_edit', {{id: item.id}})"
                        class="text-blue-500"
                    >
                        Edit
                    </button>
                    <button
                        @click="confirm('Delete?') && call('delete_item', {{id: item.id}})"
                        class="text-red-500"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </template>
    </div>

    <!-- Pagination -->
    <div class="mt-4 flex justify-between items-center" x-show="num_pages > 1">
        <div>
            Page <span x-text="page"></span> of <span x-text="num_pages"></span>
        </div>
        <div class="space-x-2">
            <button
                @click="call('previous_page')"
                :disabled="!has_previous || isLoading"
                class="px-4 py-2 border rounded"
            >
                Previous
            </button>
            <button
                @click="call('next_page')"
                :disabled="!has_next || isLoading"
                class="px-4 py-2 border rounded"
            >
                Next
            </button>
        </div>
    </div>
</div>
"""
