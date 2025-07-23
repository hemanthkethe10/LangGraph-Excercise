from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum
from datetime import datetime

class FieldSchema(BaseModel):
    field: str
    isRequired: bool
    format: str
    subFields: Optional[List['FieldSchema']] = None

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
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

# Human-in-the-Loop Schemas
class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED_FOR_HUMAN = "paused_for_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class HumanReviewAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    REQUEST_MORE_INFO = "request_more_info"

class HumanReviewRequest(BaseModel):
    workflow_id: str
    user_id: str
    step_name: str
    step_description: str
    current_data: Dict[str, Any]
    ai_suggestion: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    requires_approval: bool = True
    timeout_seconds: Optional[int] = None

class HumanReviewResponse(BaseModel):
    workflow_id: str
    action: HumanReviewAction
    modified_data: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    reviewer_id: Optional[str] = None

class WorkflowExecutionRequest(BaseModel):
    user_id: str
    user_input: Optional[str] = None
    execution_mode: str = Field(default="sync", pattern="^(sync|async)$")
    enable_human_review: bool = Field(default=False)
    human_review_steps: Optional[List[str]] = Field(default_factory=list)
    reviewer_id: Optional[str] = None

class WorkflowState(BaseModel):
    workflow_id: str
    user_id: str
    status: WorkflowStatus
    current_step: Optional[str] = None
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    human_review_queue: List[str] = Field(default_factory=list)  # List of review request IDs
    execution_mode: str = "sync"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AsyncWorkflowResponse(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    message: str
    poll_url: Optional[str] = None
    estimated_completion_time: Optional[datetime] = None

class SyncWorkflowResponse(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    data: Optional[Dict[str, Any]] = None
    human_review_required: bool = False
    review_request_id: Optional[str] = None
    next_question: Optional[str] = None
    error: Optional[str] = None
