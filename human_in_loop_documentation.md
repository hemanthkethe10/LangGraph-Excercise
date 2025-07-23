# Human-in-the-Loop Workflow Documentation

## Overview

The Human-in-the-Loop (HITL) pattern is a workflow design where AI systems pause at critical decision points to get human input, approval, or correction before continuing. This implementation provides both synchronous and asynchronous execution modes with comprehensive state management and review capabilities.

## Key Concepts

### What is Human-in-the-Loop?

Human-in-the-Loop is a pattern that combines AI automation with human judgment, allowing workflows to:

1. **Pause for Review**: Stop execution at predefined checkpoints
2. **Request Human Input**: Get approval, correction, or additional information
3. **Continue Execution**: Resume workflow based on human feedback
4. **Maintain State**: Preserve workflow state during pauses
5. **Handle Timeouts**: Gracefully handle delayed human responses

### Why Use Human-in-the-Loop?

- **Quality Assurance**: Human oversight prevents AI errors
- **Compliance**: Meet regulatory requirements for human approval
- **Edge Case Handling**: Humans can process scenarios AI cannot
- **Continuous Learning**: Human feedback improves future AI decisions
- **Risk Management**: Critical decisions require human validation

## Architecture Components

### 1. Workflow State Management
- **WorkflowState**: Tracks execution progress and status
- **Persistence**: MongoDB-based state storage
- **Status Tracking**: Real-time workflow monitoring

### 2. Human Review System
- **Review Requests**: Structured requests for human intervention
- **Review Actions**: Approve, reject, modify, or request more info
- **Assignment**: Route reviews to specific human reviewers
- **Timeout Handling**: Automatic failure on review timeouts

### 3. Execution Modes

#### Synchronous Execution
- **Blocking**: Waits for workflow completion or human review
- **Immediate Response**: Returns results or review requests immediately
- **Use Case**: Interactive applications requiring immediate feedback

#### Asynchronous Execution
- **Non-blocking**: Returns immediately with workflow ID
- **Background Processing**: Workflow runs in separate task
- **Polling**: Clients check status via API calls
- **Use Case**: Long-running workflows with human checkpoints

## API Reference

### Base URL
```
http://localhost:8000/api
```

### Environment Variables Required
```bash
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=langgraph_db
MONGO_WORKFLOWS=workflows
MONGO_HUMAN_REVIEWS=human_reviews

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
PORT=8000
```

### Endpoints

#### 1. Execute Synchronous Human-in-Loop Workflow

**POST** `/human-workflow/execute`

Execute a workflow synchronously with human review capabilities.

**Request Body:**
```json
{
  "user_id": "user123",
  "user_input": "I want to open a high-value savings account",
  "execution_mode": "sync",
  "enable_human_review": true,
  "human_review_steps": ["financial_verification", "risk_assessment"],
  "reviewer_id": "reviewer001"
}
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "status": "paused_for_human",
  "data": null,
  "human_review_required": true,
  "review_request_id": "rev_xyz789",
  "next_question": "What is your annual income?",
  "error": null
}
```

#### 2. Execute Asynchronous Human-in-Loop Workflow

**POST** `/human-workflow/execute-async`

Execute a workflow asynchronously with background processing.

**Request Body:**
```json
{
  "user_id": "user456",
  "user_input": "Process my loan application",
  "execution_mode": "async",
  "enable_human_review": true,
  "reviewer_id": "reviewer002"
}
```

**Response:**
```json
{
  "workflow_id": "wf_def456",
  "status": "pending",
  "message": "Workflow started successfully",
  "poll_url": "/api/human-workflow/status/wf_def456",
  "estimated_completion_time": "2024-01-15T10:30:00Z"
}
```

#### 3. Check Workflow Status

**GET** `/human-workflow/status/{workflow_id}`

Get current status of a workflow (essential for async execution).

**Response:**
```json
{
  "workflow_id": "wf_def456",
  "user_id": "user456",
  "status": "paused_for_human",
  "current_step": "awaiting_human_review",
  "collected_data": {},
  "human_review_queue": ["rev_abc123"],
  "execution_mode": "async",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:15:00Z",
  "completed_at": null,
  "error_message": null
}
```

#### 4. Process Human Review

**POST** `/human-workflow/review`

Submit human review decision for a paused workflow.

**Request Body:**
```json
{
  "workflow_id": "rev_abc123",
  "action": "approve",
  "modified_data": {
    "annual_income": 75000,
    "verified": true
  },
  "comments": "Income verified through tax documents",
  "reviewer_id": "reviewer001"
}
```

**Response:**
```json
{
  "approved": true,
  "data": {
    "annual_income": 75000,
    "verified": true
  }
}
```

#### 5. Get Pending Reviews

**GET** `/human-workflow/pending-reviews?reviewer_id=reviewer001`

Get all pending review requests for a reviewer.

**Response:**
```json
[
  {
    "workflow_id": "rev_abc123",
    "user_id": "user123",
    "step_name": "financial_verification",
    "step_description": "Review required for: What is your annual income?",
    "current_data": {},
    "ai_suggestion": null,
    "context": {"reviewer_id": "reviewer001"},
    "created_at": "2024-01-15T10:00:00Z",
    "requires_approval": true,
    "timeout_seconds": 1800
  }
]
```

#### 6. Get User Workflows

**GET** `/human-workflow/user/{user_id}/workflows`

Get all workflows for a specific user.

#### 7. Demo Endpoint

**POST** `/human-workflow/demo`

Comprehensive demonstration of human-in-the-loop concepts.

## Usage Examples

### Example 1: Financial Transaction Approval

```python
import requests
import time

# 1. Start async workflow for high-value transaction
response = requests.post("http://localhost:8000/api/human-workflow/execute-async", json={
    "user_id": "customer_001",
    "user_input": "I want to transfer $50,000 to an international account",
    "execution_mode": "async",
    "enable_human_review": True,
    "human_review_steps": ["transaction_verification", "fraud_check"],
    "reviewer_id": "compliance_officer_001"
})

workflow_id = response.json()["workflow_id"]

# 2. Poll for status
while True:
    status_response = requests.get(f"http://localhost:8000/api/human-workflow/status/{workflow_id}")
    status = status_response.json()["status"]
    
    if status == "paused_for_human":
        print("Workflow paused for human review")
        break
    elif status == "completed":
        print("Workflow completed")
        break
    elif status == "failed":
        print("Workflow failed")
        break
    
    time.sleep(5)  # Poll every 5 seconds

# 3. Human reviewer processes the request
review_response = requests.post("http://localhost:8000/api/human-workflow/review", json={
    "workflow_id": workflow_id,
    "action": "approve",
    "comments": "Transaction verified and approved",
    "reviewer_id": "compliance_officer_001"
})
```

### Example 2: Content Moderation

```python
# Sync execution for real-time content moderation
response = requests.post("http://localhost:8000/api/human-workflow/execute", json={
    "user_id": "content_creator_123",
    "user_input": "Check this content for policy compliance",
    "execution_mode": "sync",
    "enable_human_review": True,
    "human_review_steps": ["content_review"],
    "reviewer_id": "moderator_001"
})

if response.json()["human_review_required"]:
    print("Content flagged for human review")
    # Handle review workflow
else:
    print("Content approved automatically")
```

## Review Actions Explained

### 1. APPROVE
- **Purpose**: Accept AI decision as-is
- **Effect**: Workflow continues with original data
- **Use Case**: AI decision is correct and acceptable

### 2. REJECT
- **Purpose**: Completely reject the workflow
- **Effect**: Workflow marked as failed
- **Use Case**: Fundamental issues that cannot be corrected

### 3. MODIFY
- **Purpose**: Correct or enhance AI decision
- **Effect**: Workflow continues with modified data
- **Use Case**: AI decision needs minor corrections

### 4. REQUEST_MORE_INFO
- **Purpose**: Need additional information before deciding
- **Effect**: Workflow remains paused
- **Use Case**: Insufficient information to make decision

## Async Execution Deep Dive

### How Async Handles Human Review

1. **Background Execution**: Workflow runs in asyncio task
2. **State Persistence**: Current state saved to database
3. **Review Creation**: Human review request created when needed
4. **Waiting Loop**: Background task polls for review completion
5. **Timeout Handling**: Workflow fails if review takes too long
6. **Continuation**: Workflow resumes after human decision

### Polling Best Practices

```python
def poll_workflow_status(workflow_id, timeout_minutes=30):
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        response = requests.get(f"/api/human-workflow/status/{workflow_id}")
        status = response.json()["status"]
        
        if status in ["completed", "failed", "cancelled"]:
            return response.json()
        
        # Exponential backoff
        time.sleep(min(30, 2 ** (int((time.time() - start_time) / 10))))
    
    raise TimeoutError("Workflow polling timeout")
```

## Error Handling

### Common Error Scenarios

1. **Review Timeout**: Human doesn't respond within timeout period
2. **Workflow Not Found**: Invalid workflow ID
3. **Invalid Review Action**: Unsupported review action
4. **Database Connection**: MongoDB connection issues

### Error Response Format

```json
{
  "detail": "Human review timeout",
  "workflow_id": "wf_abc123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Security Considerations

### Access Control
- Implement authentication for reviewer endpoints
- Validate reviewer permissions for specific workflow types
- Audit trail for all human decisions

### Data Protection
- Encrypt sensitive data in review requests
- Implement data retention policies
- Secure transmission of review data

### Environment Variables Security
```bash
# Use secure methods to set environment variables
export OPENAI_API_KEY="sk-..."
export MONGO_URI="mongodb://username:password@host:port/db"

# For production, use secrets management
kubectl create secret generic hitl-secrets \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=mongo-uri="mongodb://..."
```

## Monitoring and Observability

### Key Metrics to Monitor

1. **Review Response Time**: Time from request to human decision
2. **Approval Rate**: Percentage of reviews approved vs rejected
3. **Timeout Rate**: Percentage of reviews that timeout
4. **Workflow Completion Rate**: Success rate of workflows

### Logging

The system includes structured logging for:
- Workflow state changes
- Human review requests and responses
- Error conditions and timeouts
- Performance metrics

## Best Practices

### When to Use Human-in-the-Loop

✅ **Use HITL when:**
- High-stakes decisions with significant consequences
- Regulatory compliance requires human approval
- AI confidence is below threshold
- Novel scenarios outside training data
- Customer requests human verification

❌ **Avoid HITL when:**
- High-volume, low-stakes operations
- Real-time requirements (sub-second response)
- Simple, well-defined rules can be automated
- Human expertise doesn't add value

### Configuration Guidelines

1. **Set Appropriate Timeouts**: Balance urgency with reviewer availability
2. **Define Clear Review Criteria**: Help reviewers make consistent decisions
3. **Implement Escalation**: Route urgent reviews to available reviewers
4. **Monitor Performance**: Track review times and approval rates

## Troubleshooting

### Common Issues

1. **Workflows Stuck in Pending**
   - Check MongoDB connection
   - Verify background tasks are running
   - Review error logs

2. **Review Requests Not Created**
   - Verify human_review_steps configuration
   - Check review criteria logic
   - Validate reviewer assignment

3. **Timeouts**
   - Adjust timeout settings
   - Implement reviewer notifications
   - Add escalation mechanisms

## Extension Points

The system is designed for extensibility:

1. **Custom Review Criteria**: Implement domain-specific review triggers
2. **Notification Systems**: Add email/SMS notifications for pending reviews
3. **Review UI**: Build web interfaces for human reviewers
4. **Approval Workflows**: Implement multi-stage approval processes
5. **Analytics**: Add dashboards for workflow and review metrics

## Support

For questions or issues:
- Check the API documentation at `/docs` when server is running
- Review system logs for error details
- Use the demo endpoint for testing functionality
- Monitor workflow status for debugging async issues 