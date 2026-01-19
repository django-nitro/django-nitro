# properties/schemas.py

from pydantic import BaseModel, Field

from nitro.list import BaseListState

# --- SCHEMAS DE FORMULARIOS (Aquí faltaba el Config) ---

class TenantFormSchema(BaseModel):
    full_name: str = ""
    email: str = ""

    # AGREGAR ESTO:
    class Config:
        from_attributes = True

class PropertyFormSchema(BaseModel):
    name: str = ""
    address: str = ""

    # AGREGAR ESTO:
    class Config:
        from_attributes = True

# --- SCHEMAS DE DB ---

class TenantSchema(TenantFormSchema):
    id: int
    is_active: bool
    document_url: str | None = None  # URL del archivo, no el archivo en sí

    class Config:
        from_attributes = True

class PropertySchema(PropertyFormSchema):
    id: int
    tenant_count: int = 0
    class Config:
        from_attributes = True

# --- ESTADOS DE LOS COMPONENTES ---

class TenantManagerState(BaseModel):
    property_id: int
    property_name: str
    tenants: list[TenantSchema] = []

    create_buffer: TenantFormSchema = Field(default_factory=TenantFormSchema)
    edit_buffer: TenantFormSchema | None = None
    editing_id: int | None = None

class PropertyListState(BaseListState):
    """
    State for PropertyList component.

    Extends BaseListState to get pagination, search, and filters automatically.
    Renamed 'properties' to 'items' to match BaseListState convention.
    """
    items: list[PropertySchema] = []
    # search, page, per_page, filters, etc. inherited from BaseListState

    # Must specify buffer types explicitly (BaseListState uses Any)
    create_buffer: PropertyFormSchema = Field(default_factory=PropertyFormSchema)
    edit_buffer: PropertyFormSchema | None = None
