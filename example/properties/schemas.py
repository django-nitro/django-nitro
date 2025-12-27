# properties/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

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
    document_url: Optional[str] = None  # URL del archivo, no el archivo en sí

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
    tenants: List[TenantSchema] = []
    
    create_buffer: TenantFormSchema = Field(default_factory=TenantFormSchema)
    edit_buffer: Optional[TenantFormSchema] = None
    editing_id: Optional[int] = None

class PropertyListState(BaseModel):
    properties: List[PropertySchema] = []
    search_query: str = ""
    
    create_buffer: PropertyFormSchema = Field(default_factory=PropertyFormSchema)
    edit_buffer: Optional[PropertyFormSchema] = None
    editing_id: Optional[int] = None