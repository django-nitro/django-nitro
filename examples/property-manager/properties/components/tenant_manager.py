# properties/components/tenant_manager.py
from django.shortcuts import get_object_or_404
from properties.models import Property, Tenant
from properties.schemas import TenantManagerState, TenantSchema

from nitro.base import CrudNitroComponent
from nitro.registry import register_component


@register_component
class TenantManager(CrudNitroComponent[TenantManagerState]):
    """
    Tenant management component for a specific property.

    Displays tenants for a property and supports CRUD operations.

    Note: This is a demo component. In production, you should:
    - Verify the user has permission to view/edit this property
    - Add validation to prevent duplicate emails per property
    - Handle IntegrityError exceptions gracefully
    """
    template_name = "components/tenant_manager.html"
    model = Tenant
    # state_class auto-inferred from Generic[TenantManagerState] (v0.7.0)

    def get_initial_state(self, property_id: int = None, **kwargs):
        """
        Load tenants for the specified property.

        Args:
            property_id: ID of the property to manage tenants for
        """
        if not property_id and hasattr(self, 'state'):
            property_id = self.state.property_id

        # Use get_object_or_404 for better error handling
        prop = get_object_or_404(Property, id=property_id)

        # Order by created_at for consistent ordering
        return TenantManagerState(
            property_id=prop.id,
            property_name=prop.name,
            tenants=[self._tenant_to_schema(t) for t in prop.tenants.all().order_by('-created_at')]
        )

    def _tenant_to_schema(self, tenant):
        """Convert Tenant model to schema with document_url."""
        schema = TenantSchema.model_validate(tenant)
        schema.document_url = tenant.document.url if tenant.document else None
        return schema

    def refresh(self):
        """Reload tenants for the current property."""
        from properties.schemas import TenantFormSchema

        prop = get_object_or_404(Property, id=self.state.property_id)
        self.state.tenants = [self._tenant_to_schema(t) for t in prop.tenants.all().order_by('-created_at')]

        # Clear buffers
        self.state.create_buffer = TenantFormSchema()
        self.state.edit_buffer = None
        self.state.editing_id = None

    def create_item(self):
        """Create a new tenant - optimized to avoid full refresh."""
        from properties.schemas import TenantFormSchema

        if not self.state.create_buffer or not self.state.create_buffer.full_name.strip():
            self.error("Por favor completa el nombre del inquilino")
            return

        try:
            # Create in database
            created_tenant = self.model.objects.create(
                property_id=self.state.property_id,
                full_name=self.state.create_buffer.full_name,
                email=self.state.create_buffer.email
            )

            # Add to state directly (prepend to show newest first)
            new_tenant = self._tenant_to_schema(created_tenant)
            self.state.tenants.insert(0, new_tenant)

            # Clear buffer
            self.state.create_buffer = TenantFormSchema()
            self.success("Inquilino agregado correctamente")

        except Exception as e:
            self.error(f"Error al crear: {str(e)}")

    def delete_item(self, id: int):
        """Delete a tenant - optimized to avoid full refresh."""
        self.model.objects.filter(id=id).delete()

        # Remove from state directly
        self.state.tenants = [t for t in self.state.tenants if t.id != id]
        self.success("Inquilino eliminado correctamente")

    def save_edit(self):
        """Save tenant edits - optimized to avoid full refresh."""
        if self.state.editing_id and self.state.edit_buffer:
            # Update database
            self.model.objects.filter(id=self.state.editing_id).update(
                full_name=self.state.edit_buffer.full_name,
                email=self.state.edit_buffer.email
            )

            # Update state directly
            for i, tenant in enumerate(self.state.tenants):
                if tenant.id == self.state.editing_id:
                    self.state.tenants[i].full_name = self.state.edit_buffer.full_name
                    self.state.tenants[i].email = self.state.edit_buffer.email
                    break

            # Clear edit state
            self.state.editing_id = None
            self.state.edit_buffer = None
            self.success("Guardado correctamente")

    def upload_document(self, tenant_id: int, uploaded_file=None):
        """Upload a document for a tenant."""
        if not uploaded_file:
            self.error("No se seleccionó ningún archivo")
            return

        # Validate file type (PDF only)
        if not uploaded_file.name.lower().endswith('.pdf'):
            self.error("Solo se permiten archivos PDF")
            return

        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        if uploaded_file.size > max_size:
            self.error("Archivo muy grande (máximo 5MB)")
            return

        try:
            # Get tenant and update document
            tenant = self.model.objects.get(id=tenant_id, property_id=self.state.property_id)
            tenant.document = uploaded_file
            tenant.save()

            # Update state directly
            for i, t in enumerate(self.state.tenants):
                if t.id == tenant_id:
                    self.state.tenants[i] = self._tenant_to_schema(tenant)
                    break

            self.success(f"Documento '{uploaded_file.name}' subido correctamente")

        except Tenant.DoesNotExist:
            self.error("Inquilino no encontrado")
        except Exception as e:
            self.error(f"Error al subir documento: {str(e)}")
