from fastapi import APIRouter, Request, status, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from models.schemas import (
    UserInput, CollectedData, ErrorResponse, WorkflowExecutionRequest,
    HumanReviewResponse, AsyncWorkflowResponse, SyncWorkflowResponse,
    WorkflowState, HumanReviewRequest
)
from langgraph_logic.workflow import run_workflow
from langgraph_logic.enhanced_workflow import run_enhanced_workflow
from langgraph_logic.llm_driven_workflow import run_llm_driven_workflow
from langgraph_logic.utils import error_response
from langgraph_logic.human_in_loop import workflow_manager
from langgraph_logic.persistence import get_pending_reviews, get_workflows_by_user

router = APIRouter()

@router.post("/collect")
async def collect(request: Request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return error_response("Request body must be a JSON object", status.HTTP_400_BAD_REQUEST)
        user_id = body.get("user_id")
        user_input = body.get("user_input")
        if not user_id:
            return error_response("user_id is required", status.HTTP_400_BAD_REQUEST)
        result = run_workflow(user_id, user_input)
        return JSONResponse(content=result)
    except Exception as e:
        return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/collect-enhanced")
async def collect_enhanced(request: Request):
    """
    🚀 **PRODUCTION-READY CHATBOT ENDPOINT**
    
    This endpoint provides a smooth, professional chatbot experience with:
    
    **✨ Enhanced Features:**
    - 📊 **Progress Tracking**: Users see completion progress (e.g., 60% - 3/5 fields)
    - 🎯 **Context-Aware Questions**: Personalized, friendly questions based on conversation flow
    - ✅ **Smart Validation**: Intelligent extraction from natural language responses
    - 🔄 **Error Handling**: User-friendly error messages with helpful suggestions
    - 📋 **Professional Completion**: Clear summary with formatted JSON output
    - 👤 **Personalization**: Uses user's name throughout the conversation
    
    **🎭 User Journey Example:**
    1. **Greeting**: "Hello!" → Warm welcome with clear expectations
    2. **Name Collection**: "John Smith" → "Nice to meet you, John!"
    3. **Progress Updates**: Shows "[▓▓▓░░░░░░░] 30% (1/5 fields)" 
    4. **Context Questions**: "Thanks, John! Could you share your age? (Optional)"
    5. **Smart Extraction**: "I'm 30" → Extracts "30" automatically
    6. **Final Summary**: Professional completion with formatted JSON
    
    **🔧 Production Features:**
    - Handles various input formats naturally
    - Provides examples when users are confused
    - Graceful error recovery with suggestions
    - Clear completion with both human-readable and JSON formats
    """
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return error_response("Request body must be a JSON object", status.HTTP_400_BAD_REQUEST)
        
        user_id = body.get("user_id")
        user_input = body.get("user_input")
        
        if not user_id:
            return error_response("user_id is required", status.HTTP_400_BAD_REQUEST)
        
        # Use the enhanced workflow for production-ready experience
        result = run_enhanced_workflow(user_id, user_input)
        return JSONResponse(content=result)
        
    except Exception as e:
        return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/collect-ai")
async def collect_ai_driven(request: Request):
    """
    🤖 **LLM-DRIVEN SCHEMA-AGNOSTIC CHATBOT**
    
    This endpoint demonstrates a completely AI-driven approach where:
    
    **🧠 LLM Intelligence:**
    - 📜 **Schema Analysis**: LLM dynamically analyzes any JSON schema structure
    - 🔍 **Chain of Thought**: Uses step-by-step reasoning for better decisions
    - 🎯 **Context Understanding**: Generates appropriate questions based on schema and conversation
    - ✅ **Smart Validation**: LLM validates all inputs and provides helpful feedback
    - 📊 **Progress Tracking**: AI calculates and displays completion progress
    - 🎉 **Dynamic Completion**: Generates contextual completion summaries
    
    **🚀 Key Benefits:**
    - **Schema Agnostic**: Just change `schema.json` and it works for ANY field structure
    - **Zero Configuration**: No hardcoded field descriptions, examples, or validation rules
    - **Natural Language**: Handles conversational input intelligently
    - **Adaptive Questions**: LLM creates contextual questions based on schema meaning
    - **Smart Error Recovery**: AI provides specific suggestions when users provide invalid input
    
    **🎭 Example Workflows:**
    
    **Simple Form (Name, Age):**
    ```json
    [
      {"field": "Name", "isRequired": true, "format": "string"},
      {"field": "Age", "isRequired": false, "format": "number"}
    ]
    ```
    
    **Complex Nested Form (User Profile):**
    ```json
    [
      {"field": "PersonalInfo", "format": "object", "subFields": [
        {"field": "FirstName", "isRequired": true, "format": "string"},
        {"field": "LastName", "isRequired": true, "format": "string"},
        {"field": "Email", "isRequired": true, "format": "email"}
      ]},
      {"field": "Company", "isRequired": false, "format": "string"}
    ]
    ```
    
    **🔧 How It Works:**
    1. **Schema Understanding**: LLM reads the JSON schema and understands field relationships
    2. **Question Generation**: AI creates natural, contextual questions for each field
    3. **Input Processing**: LLM validates responses and extracts relevant data
    4. **Error Handling**: AI provides specific guidance when input doesn't match expectations
    5. **Progress Management**: LLM tracks completion and generates appropriate next steps
    6. **Completion Summary**: AI creates a comprehensive final report with JSON
    
    **💡 Usage:**
    - Modify `schema.json` to define any form structure
    - AI automatically adapts to new schemas without code changes
    - Supports nested objects, optional fields, different data types
    - Handles complex validation logic through natural language understanding
    """
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return error_response("Request body must be a JSON object", status.HTTP_400_BAD_REQUEST)
        
        user_id = body.get("user_id")
        user_input = body.get("user_input")
        
        if not user_id:
            return error_response("user_id is required", status.HTTP_400_BAD_REQUEST)
        
        # Use the LLM-driven workflow for complete AI control
        result = run_llm_driven_workflow(user_id, user_input)
        return JSONResponse(content=result)
        
    except Exception as e:
        return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

# Human-in-the-Loop Endpoints

@router.post("/human-workflow/execute", response_model=SyncWorkflowResponse)
async def execute_human_workflow_sync(request: WorkflowExecutionRequest):
    """
    Execute a workflow with human-in-the-loop capabilities (synchronous).
    
    This endpoint demonstrates the human-in-the-loop concept by allowing workflows
    to pause and wait for human intervention at critical decision points.
    
    **Human-in-the-Loop Concept:**
    - Workflows can be configured to pause at specific steps
    - Human reviewers can approve, reject, or modify AI decisions
    - State is persisted, allowing workflows to be resumed after human input
    - Supports both automatic triggers and explicit step configuration
    
    **Synchronous Execution:**
    - Blocks until workflow completes or requires human review
    - Returns immediate results or review requests
    - Suitable for interactive applications
    """
    try:
        if request.execution_mode != "sync":
            raise HTTPException(
                status_code=400, 
                detail="This endpoint only supports synchronous execution"
            )
        
        result = await workflow_manager.execute_workflow_sync(
            user_id=request.user_id,
            user_input=request.user_input,
            enable_human_review=request.enable_human_review,
            human_review_steps=request.human_review_steps,
            reviewer_id=request.reviewer_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/human-workflow/execute-async", response_model=AsyncWorkflowResponse)
async def execute_human_workflow_async(request: WorkflowExecutionRequest):
    """
    Execute a workflow with human-in-the-loop capabilities (asynchronous).
    
    **Asynchronous Execution with Human-in-the-Loop:**
    - Non-blocking execution - returns immediately with workflow ID
    - Workflow runs in background, can pause for human review
    - Clients poll for status updates
    - Supports long-running workflows with human checkpoints
    - Handles timeouts and error recovery
    
    **How Async Handles Human Review:**
    1. Workflow starts and runs in background task
    2. When human review is needed, workflow pauses
    3. Review request is created and stored
    4. Background task waits for human response (with timeout)
    5. Once approved/rejected, workflow continues or fails
    6. Client can poll status to track progress
    """
    try:
        if request.execution_mode != "async":
            request.execution_mode = "async"  # Override for this endpoint
        
        result = await workflow_manager.execute_workflow_async(
            user_id=request.user_id,
            user_input=request.user_input,
            enable_human_review=request.enable_human_review,
            human_review_steps=request.human_review_steps,
            reviewer_id=request.reviewer_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human-workflow/status/{workflow_id}", response_model=WorkflowState)
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow.
    
    This endpoint allows clients to poll for workflow status updates,
    which is essential for asynchronous execution patterns.
    """
    try:
        workflow_state = await workflow_manager.get_workflow_status(workflow_id)
        if not workflow_state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return workflow_state
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/human-workflow/review")
async def process_human_review(review_response: HumanReviewResponse):
    """
    Process a human review response for a paused workflow.
    
    **Human Review Actions:**
    - **APPROVE**: Continue workflow with original AI decision
    - **REJECT**: Fail workflow with rejection reason
    - **MODIFY**: Continue with human-modified data
    - **REQUEST_MORE_INFO**: Keep workflow paused, request additional information
    
    This endpoint demonstrates how human feedback is integrated back into
    the workflow execution process.
    """
    try:
        result = await workflow_manager.process_human_review(review_response)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human-workflow/pending-reviews", response_model=List[HumanReviewRequest])
async def get_pending_reviews_endpoint(reviewer_id: str = None):
    """
    Get all pending human review requests.
    
    Optionally filter by reviewer_id to get reviews assigned to a specific person.
    This enables building review dashboards and assignment systems.
    """
    try:
        reviews = await workflow_manager.get_pending_reviews_for_user(reviewer_id)
        return reviews
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/human-workflow/user/{user_id}/workflows", response_model=List[WorkflowState])
async def get_user_workflows(user_id: str):
    """
    Get all workflows for a specific user.
    
    Useful for building user dashboards showing workflow history and status.
    """
    try:
        workflows = get_workflows_by_user(user_id)
        return workflows
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/human-workflow/demo")
async def human_in_loop_demo():
    """
    **DEMO ENDPOINT: Human-in-the-Loop Concept Demonstration**
    
    This endpoint provides a practical example of how human-in-the-loop works:
    
    1. **Automatic Execution**: Starts a workflow that processes user data
    2. **AI Decision Point**: AI makes a decision that might need human review
    3. **Human Checkpoint**: Workflow pauses if review criteria are met
    4. **Human Review**: Human can approve, reject, or modify the AI decision
    5. **Continuation**: Workflow resumes based on human feedback
    
    **Key Benefits:**
    - **Quality Control**: Human oversight prevents AI errors
    - **Compliance**: Ensures critical decisions have human approval
    - **Learning**: Human feedback improves future AI decisions
    - **Flexibility**: Humans can handle edge cases AI cannot
    
    **Industry Applications:**
    - Financial transaction approvals
    - Medical diagnosis verification
    - Legal document review
    - Content moderation decisions
    - Risk assessment validation
    """
    try:
        # Demonstrate sync execution with human review
        demo_request = WorkflowExecutionRequest(
            user_id="demo_user_123",
            user_input="I want to set up a high-value financial account",
            execution_mode="sync",
            enable_human_review=True,
            human_review_steps=["financial_verification", "risk_assessment"],
            reviewer_id="human_reviewer_001"
        )
        
        sync_result = await workflow_manager.execute_workflow_sync(
            user_id=demo_request.user_id,
            user_input=demo_request.user_input,
            enable_human_review=demo_request.enable_human_review,
            human_review_steps=demo_request.human_review_steps,
            reviewer_id=demo_request.reviewer_id
        )
        
        # Demonstrate async execution
        async_demo_request = WorkflowExecutionRequest(
            user_id="demo_user_async_456",
            user_input="Process this complex data analysis request",
            execution_mode="async",
            enable_human_review=True,
            reviewer_id="human_reviewer_002"
        )
        
        async_result = await workflow_manager.execute_workflow_async(
            user_id=async_demo_request.user_id,
            user_input=async_demo_request.user_input,
            enable_human_review=async_demo_request.enable_human_review,
            reviewer_id=async_demo_request.reviewer_id
        )
        
        return {
            "message": "Human-in-the-Loop Demo Executed",
            "concept_explanation": {
                "what_is_human_in_loop": "A pattern where AI workflows pause at critical points to get human input, approval, or correction before continuing",
                "sync_vs_async": {
                    "synchronous": "Blocks and waits for immediate response, good for interactive applications",
                    "asynchronous": "Runs in background, allows long-running workflows with human checkpoints"
                },
                "key_benefits": [
                    "Quality assurance through human oversight",
                    "Compliance with regulations requiring human approval",
                    "Handling of edge cases AI cannot process",
                    "Continuous learning from human feedback"
                ]
            },
            "demo_results": {
                "synchronous_execution": sync_result.model_dump(),
                "asynchronous_execution": async_result.model_dump()
            },
            "next_steps": [
                "Check workflow status using GET /human-workflow/status/{workflow_id}",
                "View pending reviews using GET /human-workflow/pending-reviews",
                "Submit review decisions using POST /human-workflow/review"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")
