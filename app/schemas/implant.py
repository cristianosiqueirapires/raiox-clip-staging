from pydantic import BaseModel
from typing import Optional, List

class ImplantBase(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None
    image_url: Optional[str] = None

class ImplantCreate(ImplantBase):
    pass

class ImplantSchema(ImplantBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True  # Versão atualizada do orm_mode para Pydantic v2
