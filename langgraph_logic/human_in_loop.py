"""
Human-in-the-Loop Workflow Implementation for LangGraph

This module implements the human-in-the-loop pattern, allowing workflows to pause
and wait for human intervention at critical decision points. It supports both
synchronous and asynchronous execution modes.

Key Concepts:
1. Workflow Checkpoints: Points where human review is required
2. Review Requests: Structured requests for human input/approval
3. State Persistence: Workflows can be paused and resumed
4. Async Handling: Non-blocking execution with proper state management
"""

import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor
import json

from models.schemas import (
    WorkflowState, WorkflowStatus, HumanReviewRequest, HumanReviewResponse,
    HumanReviewAction, AsyncWorkflowResponse, SyncWorkflowResponse
)
from langgraph_logic.persistence import (
    save_workflow_state, load_workflow_state, save_human_review_request,
    load_human_review_request, update_human_review_request, get_pending_reviews
)
from langgraph_logic.workflow import run_workflow as original_run_workflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HumanInLoopWorkflowManager:
    """
    Manages human-in-the-loop workflows with support for both sync and async execution.
    
    This class handles:
    - Workflow state management
    - Human review request creation and processing
    - Async workflow execution and monitoring
    - Timeout handling for human reviews
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.active_workflows: Dict[str, asyncio.Task] = {}
        
    async def execute_workflow_sync(
        self,
        user_id: str,
        user_input: Optional[str] = None,
        enable_human_review: bool = False,
        human_review_steps: Optional[List[str]] = None,
        reviewer_id: Optional[str] = None
    ) -> SyncWorkflowResponse:
        """
        Execute workflow synchronously with optional human-in-the-loop checkpoints.
        
        Args:
            user_id: User identifier
            user_input: User's input message
            enable_human_review: Whether to enable human review checkpoints
            human_review_steps: Specific steps that require human review
            reviewer_id: ID of the human reviewer
            
        Returns:
            SyncWorkflowResponse with execution results
        """
        workflow_id = str(uuid.uuid4())
        
        try:
            # Initialize workflow state
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                user_id=user_id,
                status=WorkflowStatus.RUNNING,
                execution_mode="sync"
            )
            save_workflow_state(workflow_state)
            
            # Run the original workflow
            result = original_run_workflow(user_id, user_input)
            
            # Check if human review is needed
            if enable_human_review and self._should_request_human_review(
                result, human_review_steps
            ):
                review_request = self._create_human_review_request(
                    workflow_id, user_id, result, reviewer_id
                )
                
                workflow_state.status = WorkflowStatus.PAUSED_FOR_HUMAN
                workflow_state.human_review_queue.append(review_request.workflow_id)
                save_workflow_state(workflow_state)
                
                return SyncWorkflowResponse(
                    workflow_id=workflow_id,
                    status=WorkflowStatus.PAUSED_FOR_HUMAN,
                    human_review_required=True,
                    review_request_id=review_request.workflow_id,
                    next_question=result.get("question")
                )
            
            # Complete workflow
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.collected_data = result
            workflow_state.completed_at = datetime.utcnow()
            save_workflow_state(workflow_state)
            
            return SyncWorkflowResponse(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                data=result,
                next_question=result.get("question")
            )
            
        except Exception as e:
            logger.error(f"Sync workflow execution failed: {str(e)}")
            
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error_message = str(e)
            save_workflow_state(workflow_state)
            
            return SyncWorkflowResponse(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error=str(e)
            )
    
    async def execute_workflow_async(
        self,
        user_id: str,
        user_input: Optional[str] = None,
        enable_human_review: bool = False,
        human_review_steps: Optional[List[str]] = None,
        reviewer_id: Optional[str] = None
    ) -> AsyncWorkflowResponse:
        """
        Execute workflow asynchronously with human-in-the-loop support.
        
        Args:
            user_id: User identifier
            user_input: User's input message
            enable_human_review: Whether to enable human review checkpoints
            human_review_steps: Specific steps that require human review
            reviewer_id: ID of the human reviewer
            
        Returns:
            AsyncWorkflowResponse with workflow tracking information
        """
        workflow_id = str(uuid.uuid4())
        
        # Initialize workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            status=WorkflowStatus.PENDING,
            execution_mode="async"
        )
        save_workflow_state(workflow_state)
        
        # Create and start async task
        task = asyncio.create_task(
            self._execute_async_workflow_task(
                workflow_id, user_id, user_input, enable_human_review,
                human_review_steps, reviewer_id
            )
        )
        
        self.active_workflows[workflow_id] = task
        
        return AsyncWorkflowResponse(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            message="Workflow started successfully",
            poll_url=f"/human-workflow/status/{workflow_id}",
            estimated_completion_time=datetime.utcnow() + timedelta(minutes=5)
        )
    
    async def _execute_async_workflow_task(
        self,
        workflow_id: str,
        user_id: str,
        user_input: Optional[str],
        enable_human_review: bool,
        human_review_steps: Optional[List[str]],
        reviewer_id: Optional[str]
    ):
        """Internal method to execute async workflow task."""
        try:
            # Update status to running
            workflow_state = load_workflow_state(workflow_id)
            workflow_state.status = WorkflowStatus.RUNNING
            workflow_state.current_step = "processing_user_input"
            save_workflow_state(workflow_state)
            
            # Simulate some async processing time
            await asyncio.sleep(1)
            
            # Run the workflow in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                original_run_workflow, 
                user_id, 
                user_input
            )
            
            # Check for human review requirements
            if enable_human_review and self._should_request_human_review(
                result, human_review_steps
            ):
                workflow_state.status = WorkflowStatus.PAUSED_FOR_HUMAN
                workflow_state.current_step = "awaiting_human_review"
                save_workflow_state(workflow_state)
                
                # Create review request
                review_request = self._create_human_review_request(
                    workflow_id, user_id, result, reviewer_id
                )
                
                # Wait for human review with timeout
                await self._wait_for_human_review(
                    workflow_id, review_request.workflow_id, timeout_minutes=30
                )
            
            # Complete workflow
            workflow_state = load_workflow_state(workflow_id)
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.collected_data = result
            workflow_state.completed_at = datetime.utcnow()
            save_workflow_state(workflow_state)
            
        except Exception as e:
            logger.error(f"Async workflow {workflow_id} failed: {str(e)}")
            
            workflow_state = load_workflow_state(workflow_id)
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error_message = str(e)
            save_workflow_state(workflow_state)
        
        finally:
            # Clean up task reference
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def process_human_review(
        self, 
        review_response: HumanReviewResponse
    ) -> Dict[str, Any]:
        """
        Process human review response and continue workflow execution.
        
        Args:
            review_response: Human's review decision and any modifications
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Load review request
            review_request = load_human_review_request(review_response.workflow_id)
            if not review_request:
                raise ValueError(f"Review request not found: {review_response.workflow_id}")
            
            # Load workflow state
            workflow_state = load_workflow_state(review_request.workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow not found: {review_request.workflow_id}")
            
            # Process the review action
            if review_response.action == HumanReviewAction.APPROVE:
                # Continue with original data
                result = {"approved": True, "data": review_request.current_data}
                
            elif review_response.action == HumanReviewAction.MODIFY:
                # Use modified data
                result = {
                    "approved": True, 
                    "data": review_response.modified_data or review_request.current_data
                }
                
            elif review_response.action == HumanReviewAction.REJECT:
                # Reject and potentially restart
                workflow_state.status = WorkflowStatus.FAILED
                workflow_state.error_message = f"Rejected by human reviewer: {review_response.comments}"
                save_workflow_state(workflow_state)
                return {"rejected": True, "reason": review_response.comments}
                
            elif review_response.action == HumanReviewAction.REQUEST_MORE_INFO:
                # Keep workflow paused, request more information
                review_request.step_description = f"More info requested: {review_response.comments}"
                update_human_review_request(review_request)
                return {"more_info_requested": True, "message": review_response.comments}
            
            # Update workflow state to continue
            workflow_state.status = WorkflowStatus.RUNNING
            workflow_state.current_step = "processing_human_feedback"
            save_workflow_state(workflow_state)
            
            # Mark review as completed
            review_request.requires_approval = False
            update_human_review_request(review_request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing human review: {str(e)}")
            return {"error": str(e)}
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get current status of a workflow."""
        return load_workflow_state(workflow_id)
    
    async def get_pending_reviews_for_user(self, reviewer_id: str) -> List[HumanReviewRequest]:
        """Get all pending review requests for a specific reviewer."""
        return get_pending_reviews(reviewer_id)
    
    async def _wait_for_human_review(
        self, 
        workflow_id: str, 
        review_request_id: str, 
        timeout_minutes: int = 30
    ):
        """Wait for human review with timeout handling."""
        timeout_seconds = timeout_minutes * 60
        check_interval = 10  # Check every 10 seconds
        
        for _ in range(0, timeout_seconds, check_interval):
            await asyncio.sleep(check_interval)
            
            review_request = load_human_review_request(review_request_id)
            if review_request and not review_request.requires_approval:
                return  # Review completed
        
        # Timeout reached
        logger.warning(f"Human review timeout for workflow {workflow_id}")
        workflow_state = load_workflow_state(workflow_id)
        workflow_state.status = WorkflowStatus.FAILED
        workflow_state.error_message = "Human review timeout"
        save_workflow_state(workflow_state)
    
    def _should_request_human_review(
        self, 
        workflow_result: Dict[str, Any], 
        human_review_steps: Optional[List[str]]
    ) -> bool:
        """Determine if human review is needed based on workflow result and configuration."""
        # Always request review if there's an error or uncertainty
        if workflow_result.get("error"):
            return True
        
        # Check if current step requires human review
        if human_review_steps:
            current_step = workflow_result.get("next_field", {}).get("field", "")
            if current_step in human_review_steps:
                return True
        
        # Request review for complex or sensitive data
        if workflow_result.get("next_field", {}).get("format") in ["object", "array"]:
            return True
        
        return False
    
    def _create_human_review_request(
        self,
        workflow_id: str,
        user_id: str,
        workflow_result: Dict[str, Any],
        reviewer_id: Optional[str]
    ) -> HumanReviewRequest:
        """Create a human review request for the current workflow step."""
        review_request = HumanReviewRequest(
            workflow_id=workflow_id,
            user_id=user_id,
            step_name=workflow_result.get("next_field", {}).get("field", "current_step"),
            step_description=f"Review required for: {workflow_result.get('question', 'No description')}",
            current_data=workflow_result,
            ai_suggestion=workflow_result.get("ai_suggestion"),
            context={"reviewer_id": reviewer_id} if reviewer_id else None,
            timeout_seconds=1800  # 30 minutes timeout
        )
        
        save_human_review_request(review_request)
        return review_request

# Global instance
workflow_manager = HumanInLoopWorkflowManager() 