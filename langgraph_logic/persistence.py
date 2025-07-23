import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, List
from models.schemas import WorkflowState, HumanReviewRequest

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_CHAT_HISTORY = os.getenv("MONGO_CHAT_HISTORY", "chat_history")
MONGO_SUBSCRIPTIONS = os.getenv("MONGO_SUBSCRIPTIONS", "subscriptions")
MONGO_WORKFLOWS = os.getenv("MONGO_WORKFLOWS", "workflows")
MONGO_HUMAN_REVIEWS = os.getenv("MONGO_HUMAN_REVIEWS", "human_reviews")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set in environment variables.")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
chat_history_collection = db[MONGO_CHAT_HISTORY]
subscriptions_collection = db[MONGO_SUBSCRIPTIONS]
workflows_collection = db[MONGO_WORKFLOWS]
human_reviews_collection = db[MONGO_HUMAN_REVIEWS]

def save_chat_message(user_id, role, content):
    chat_history_collection.update_one(
        {"user_id": user_id},
        {"$push": {"history": {"role": role, "content": content, "timestamp": datetime.utcnow()}}},
        upsert=True
    )

def serialize_history(history):
    for msg in history:
        if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
            msg['timestamp'] = msg['timestamp'].isoformat()
    return history

def load_chat_history(user_id):
    doc = chat_history_collection.find_one({"user_id": user_id})
    history = doc["history"] if doc and "history" in doc else []
    return serialize_history(history)

def save_state(user_id: str, state: dict):
    subscriptions_collection.update_one({"user_id": user_id}, {"$set": {"state": state}}, upsert=True)

def load_state(user_id: str) -> dict:
    doc = subscriptions_collection.find_one({"user_id": user_id})
    return doc["state"] if doc and "state" in doc else {}

# Human-in-the-Loop Persistence Functions
def save_workflow_state(workflow_state: WorkflowState):
    """Save workflow state to database."""
    workflow_data = workflow_state.model_dump()
    # Convert datetime objects to strings for MongoDB
    for field in ['created_at', 'updated_at', 'completed_at']:
        if workflow_data.get(field):
            workflow_data[field] = workflow_data[field].isoformat() if isinstance(workflow_data[field], datetime) else workflow_data[field]
    
    workflows_collection.update_one(
        {"workflow_id": workflow_state.workflow_id},
        {"$set": workflow_data},
        upsert=True
    )

def load_workflow_state(workflow_id: str) -> Optional[WorkflowState]:
    """Load workflow state from database."""
    doc = workflows_collection.find_one({"workflow_id": workflow_id})
    if not doc:
        return None
    
    # Convert string timestamps back to datetime objects
    for field in ['created_at', 'updated_at', 'completed_at']:
        if doc.get(field) and isinstance(doc[field], str):
            try:
                doc[field] = datetime.fromisoformat(doc[field])
            except ValueError:
                pass  # Keep as string if conversion fails
    
    # Remove MongoDB's _id field
    doc.pop('_id', None)
    
    try:
        return WorkflowState(**doc)
    except Exception as e:
        print(f"Error deserializing workflow state: {e}")
        return None

def save_human_review_request(review_request: HumanReviewRequest):
    """Save human review request to database."""
    review_data = review_request.model_dump()
    # Convert datetime to string for MongoDB
    if review_data.get('created_at'):
        review_data['created_at'] = review_data['created_at'].isoformat() if isinstance(review_data['created_at'], datetime) else review_data['created_at']
    
    human_reviews_collection.update_one(
        {"workflow_id": review_request.workflow_id},
        {"$set": review_data},
        upsert=True
    )

def load_human_review_request(workflow_id: str) -> Optional[HumanReviewRequest]:
    """Load human review request from database."""
    doc = human_reviews_collection.find_one({"workflow_id": workflow_id})
    if not doc:
        return None
    
    # Convert string timestamp back to datetime
    if doc.get('created_at') and isinstance(doc['created_at'], str):
        try:
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        except ValueError:
            pass
    
    # Remove MongoDB's _id field
    doc.pop('_id', None)
    
    try:
        return HumanReviewRequest(**doc)
    except Exception as e:
        print(f"Error deserializing human review request: {e}")
        return None

def update_human_review_request(review_request: HumanReviewRequest):
    """Update existing human review request."""
    review_data = review_request.model_dump()
    # Convert datetime to string for MongoDB
    if review_data.get('created_at'):
        review_data['created_at'] = review_data['created_at'].isoformat() if isinstance(review_data['created_at'], datetime) else review_data['created_at']
    
    human_reviews_collection.update_one(
        {"workflow_id": review_request.workflow_id},
        {"$set": review_data}
    )

def get_pending_reviews(reviewer_id: Optional[str] = None) -> List[HumanReviewRequest]:
    """Get all pending review requests, optionally filtered by reviewer."""
    query = {"requires_approval": True}
    if reviewer_id:
        query["context.reviewer_id"] = reviewer_id
    
    docs = human_reviews_collection.find(query)
    reviews = []
    
    for doc in docs:
        # Convert string timestamp back to datetime
        if doc.get('created_at') and isinstance(doc['created_at'], str):
            try:
                doc['created_at'] = datetime.fromisoformat(doc['created_at'])
            except ValueError:
                pass
        
        # Remove MongoDB's _id field
        doc.pop('_id', None)
        
        try:
            reviews.append(HumanReviewRequest(**doc))
        except Exception as e:
            print(f"Error deserializing human review request: {e}")
            continue
    
    return reviews

def get_workflows_by_user(user_id: str) -> List[WorkflowState]:
    """Get all workflows for a specific user."""
    docs = workflows_collection.find({"user_id": user_id})
    workflows = []
    
    for doc in docs:
        # Convert string timestamps back to datetime objects
        for field in ['created_at', 'updated_at', 'completed_at']:
            if doc.get(field) and isinstance(doc[field], str):
                try:
                    doc[field] = datetime.fromisoformat(doc[field])
                except ValueError:
                    pass
        
        # Remove MongoDB's _id field
        doc.pop('_id', None)
        
        try:
            workflows.append(WorkflowState(**doc))
        except Exception as e:
            print(f"Error deserializing workflow state: {e}")
            continue
    
    return workflows
