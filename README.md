# LangGraph Human-in-the-Loop Workflow System

A comprehensive FastAPI-based implementation of human-in-the-loop workflows using LangGraph, supporting both synchronous and asynchronous execution with MongoDB persistence.

## 🚀 Features

- **Human-in-the-Loop Workflows**: AI workflows that pause for human intervention at critical decision points
- **Dual Execution Modes**: Both synchronous (blocking) and asynchronous (non-blocking) execution
- **State Persistence**: MongoDB-based workflow state management with resume capabilities
- **Review System**: Structured human review requests with approval, rejection, and modification options
- **Timeout Handling**: Automatic workflow failure on review timeouts
- **Comprehensive API**: RESTful endpoints for workflow management and monitoring
- **Production Ready**: Industry-standard error handling, logging, and security practices

## 📋 Prerequisites

- Python 3.8+
- MongoDB (local or remote)
- OpenAI API key
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## 🛠️ Installation & Setup

### 1. Install [uv](https://github.com/astral-sh/uv):

```sh
curl -Ls https://astral.sh/uv/install.sh | sh
# or
brew install uv
```

### 2. Install dependencies:

```sh
uv pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=langgraph_db
MONGO_CHAT_HISTORY=chat_history
MONGO_SUBSCRIPTIONS=subscriptions
MONGO_WORKFLOWS=workflows
MONGO_HUMAN_REVIEWS=human_reviews

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
PORT=8000
```

### 4. Start MongoDB

Ensure MongoDB is running on your system:

```sh
# macOS with Homebrew
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 5. Run the FastAPI app:

```sh
uv venv exec uvicorn main:app --reload
# or
python main.py
```

The server will start at `http://localhost:8000`

## 🎯 Human-in-the-Loop Concept

Human-in-the-Loop (HITL) is a workflow pattern where AI systems pause at critical decision points to get human input, approval, or correction before continuing. This implementation provides:

### Key Benefits:
- **Quality Assurance**: Human oversight prevents AI errors
- **Compliance**: Meet regulatory requirements for human approval
- **Edge Case Handling**: Humans can process scenarios AI cannot
- **Continuous Learning**: Human feedback improves future AI decisions
- **Risk Management**: Critical decisions require human validation

### Execution Modes:

#### Synchronous Execution
- **Blocking**: Waits for workflow completion or human review
- **Immediate Response**: Returns results or review requests immediately
- **Use Case**: Interactive applications requiring immediate feedback

#### Asynchronous Execution
- **Non-blocking**: Returns immediately with workflow ID
- **Background Processing**: Workflow runs in separate task
- **Polling**: Clients check status via API calls
- **Use Case**: Long-running workflows with human checkpoints

## 📚 API Documentation

### Core Endpoints

#### 1. Execute Synchronous Workflow
```http
POST /api/human-workflow/execute
```

#### 2. Execute Asynchronous Workflow
```http
POST /api/human-workflow/execute-async
```

#### 3. Check Workflow Status
```http
GET /api/human-workflow/status/{workflow_id}
```

#### 4. Process Human Review
```http
POST /api/human-workflow/review
```

#### 5. Get Pending Reviews
```http
GET /api/human-workflow/pending-reviews
```

#### 6. Demo Endpoint
```http
POST /api/human-workflow/demo
```

### Interactive API Documentation
Visit `http://localhost:8000/docs` for complete Swagger documentation.

## 🧪 Testing

### Quick Demo
```sh
# Run the comprehensive test suite
python test_human_in_loop.py
```

### Manual Testing with curl

#### 1. Test Synchronous Execution
```bash
curl -X POST "http://localhost:8000/api/human-workflow/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user_001",
       "user_input": "I want to open a high-value account",
       "execution_mode": "sync",
       "enable_human_review": true,
       "human_review_steps": ["financial_verification"],
       "reviewer_id": "reviewer_001"
     }'
```

#### 2. Test Asynchronous Execution
```bash
curl -X POST "http://localhost:8000/api/human-workflow/execute-async" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user_002",
       "user_input": "Process my loan application",
       "execution_mode": "async",
       "enable_human_review": true,
       "reviewer_id": "reviewer_002"
     }'
```

#### 3. Check Workflow Status
```bash
curl -X GET "http://localhost:8000/api/human-workflow/status/{workflow_id}"
```

#### 4. Demo the Concept
```bash
curl -X POST "http://localhost:8000/api/human-workflow/demo"
```

## 📖 Usage Examples

### Python Client Example

```python
import requests
import time

# 1. Start async workflow
response = requests.post("http://localhost:8000/api/human-workflow/execute-async", json={
    "user_id": "customer_001",
    "user_input": "I want to transfer $50,000",
    "execution_mode": "async",
    "enable_human_review": True,
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
    elif status in ["completed", "failed"]:
        print(f"Workflow finished: {status}")
        break
    
    time.sleep(5)

# 3. Process human review
if status == "paused_for_human":
    review_response = requests.post("http://localhost:8000/api/human-workflow/review", json={
        "workflow_id": workflow_id,
        "action": "approve",
        "comments": "Transaction approved",
        "reviewer_id": "compliance_officer_001"
    })
```

## 🏭 Industry Applications

- **Financial Services**: Transaction approvals, loan processing, risk assessment
- **Healthcare**: Medical diagnosis verification, treatment plan approval
- **Legal**: Document review, compliance checking, contract analysis
- **Content Moderation**: Policy compliance, content approval
- **Manufacturing**: Quality control, safety inspections

## 📊 Monitoring & Observability

The system includes comprehensive logging for:
- Workflow state changes
- Human review requests and responses
- Error conditions and timeouts
- Performance metrics

Monitor key metrics:
- Review response times
- Approval rates
- Timeout rates
- Workflow completion rates

## 🔒 Security Features

- Environment variable-based configuration
- Input validation with Pydantic models
- Error handling and timeout protection
- Structured logging for audit trails
- Database connection security

## 📁 Project Structure

```
LangGraph-Excercise/
├── api/
│   └── routes.py                    # API endpoints including HITL routes
├── langgraph_logic/
│   ├── human_in_loop.py            # Core HITL workflow manager
│   ├── persistence.py              # Database operations
│   ├── workflow.py                 # Original LangGraph workflow
│   └── utils.py                    # Utility functions
├── models/
│   └── schemas.py                  # Pydantic models and schemas
├── main.py                         # FastAPI application entry point
├── test_human_in_loop.py          # Comprehensive test suite
├── human_in_loop_documentation.md # Detailed documentation
├── requirements.txt               # Project dependencies
└── README.md                      # This file
```

## 🆘 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```
   Check MONGO_URI in .env file
   Ensure MongoDB service is running
   ```

2. **OpenAI API Errors**
   ```
   Verify OPENAI_API_KEY is set correctly
   Check API key has sufficient credits
   ```

3. **Workflows Stuck in Pending**
   ```
   Check server logs for background task errors
   Verify MongoDB collections are accessible
   ```

4. **Review Timeouts**
   ```
   Adjust timeout settings in human_in_loop.py
   Implement reviewer notification systems
   ```

## 🚀 Advanced Configuration

### Custom Review Criteria
Modify `_should_request_human_review()` in `human_in_loop.py` to implement domain-specific triggers.

### Notification Systems
Extend the system to add email/SMS notifications for pending reviews.

### Multi-stage Approvals
Implement hierarchical approval workflows with multiple reviewer levels.

## 📝 Documentation

- **API Reference**: `http://localhost:8000/docs` (when server is running)
- **Detailed Guide**: `human_in_loop_documentation.md`
- **Test Examples**: `test_human_in_loop.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Support

For questions or issues:
- Check the comprehensive documentation
- Review API docs at `/docs`
- Run the test suite for examples
- Check server logs for debugging information