from pydantic import BaseModel, Field
from typing import List, Optional, Any

class FieldSchema(BaseModel):
    field: str
    isRequired: bool
    format: str
    subFields: Optional[List['FieldSchema']] = None

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "field": "Address",
                "isRequired": True,
                "format": "object",
                "subFields": [
                    {"field": "DoorNo", "isRequired": True, "format": "string"},
                    {"field": "Street", "isRequired": True, "format": "string"},
                    {"field": "Pincode", "isRequired": True, "format": "number"}
                ]
            }
        }

FieldSchema.model_rebuild()

class UserInput(BaseModel):
    field: str
    value: Any

class CollectedData(BaseModel):
    data: dict

class ErrorResponse(BaseModel):
    detail: str
