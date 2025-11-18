
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    type: str
    description: str

class InputSchema(BaseModel):
    type: str = "object"
    properties: dict[str, ToolParameter]
    required: list[str] = Field(default_factory=list)

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: InputSchema = Field(alias="inputSchema")

    class Config:
        populate_by_name = True
