#!/usr/bin/env python3
"""
Test script for Human-in-the-Loop Workflow functionality.

This script demonstrates how to use the human-in-the-loop endpoints
with both synchronous and asynchronous execution modes.

Prerequisites:
1. Start the FastAPI server: python main.py
2. Ensure MongoDB is running
3. Set up environment variables in .env file
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api"
TIMEOUT = 30  # seconds

def test_sync_workflow():
    """Test synchronous human-in-the-loop workflow execution."""
    print("\n🔄 Testing Synchronous Human-in-the-Loop Workflow")
    print("=" * 60)
    
    # Request payload
    payload = {
        "user_id": "test_sync_user_001",
        "user_input": "I want to open a high-value business account with initial deposit of $100,000",
        "execution_mode": "sync",
        "enable_human_review": True,
        "human_review_steps": ["financial_verification", "compliance_check"],
        "reviewer_id": "compliance_officer_001"
    }
    
    try:
        print(f"📤 Sending request to {BASE_URL}/human-workflow/execute")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/human-workflow/execute",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            
            if result.get("human_review_required"):
                print("\n🔍 Human review required!")
                print(f"📝 Review Request ID: {result.get('review_request_id')}")
                print(f"❓ Next Question: {result.get('next_question')}")
                
                # Simulate human review
                review_payload = {
                    "workflow_id": result.get("review_request_id"),
                    "action": "approve",
                    "comments": "High-value account approved after verification",
                    "reviewer_id": "compliance_officer_001"
                }
                
                print(f"\n🧑‍💼 Simulating human review approval...")
                review_response = requests.post(
                    f"{BASE_URL}/human-workflow/review",
                    json=review_payload,
                    timeout=TIMEOUT
                )
                
                if review_response.status_code == 200:
                    print(f"✅ Review processed: {review_response.json()}")
                else:
                    print(f"❌ Review failed: {review_response.status_code} - {review_response.text}")
            else:
                print("✅ Workflow completed without human review")
                
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_async_workflow():
    """Test asynchronous human-in-the-loop workflow execution."""
    print("\n🚀 Testing Asynchronous Human-in-the-Loop Workflow")
    print("=" * 60)
    
    # Request payload
    payload = {
        "user_id": "test_async_user_002",
        "user_input": "Process my mortgage application for $500,000 home loan",
        "execution_mode": "async",
        "enable_human_review": True,
        "reviewer_id": "loan_officer_001"
    }
    
    try:
        print(f"📤 Sending async request to {BASE_URL}/human-workflow/execute-async")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/human-workflow/execute-async",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result.get("workflow_id")
            print(f"✅ Async workflow started: {json.dumps(result, indent=2)}")
            print(f"🆔 Workflow ID: {workflow_id}")
            
            # Poll for status
            print(f"\n🔄 Polling workflow status...")
            for attempt in range(10):  # Poll for up to 10 attempts
                time.sleep(2)  # Wait 2 seconds between polls
                
                status_response = requests.get(
                    f"{BASE_URL}/human-workflow/status/{workflow_id}",
                    timeout=TIMEOUT
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get("status")
                    print(f"📊 Attempt {attempt + 1}: Status = {current_status}")
                    
                    if current_status == "paused_for_human":
                        print("🔍 Workflow paused for human review!")
                        print(f"📝 Workflow details: {json.dumps(status, indent=2)}")
                        
                        # Get pending reviews
                        reviews_response = requests.get(
                            f"{BASE_URL}/human-workflow/pending-reviews",
                            params={"reviewer_id": "loan_officer_001"},
                            timeout=TIMEOUT
                        )
                        
                        if reviews_response.status_code == 200:
                            reviews = reviews_response.json()
                            print(f"📋 Pending reviews: {len(reviews)}")
                            
                            if reviews:
                                # Process the first review
                                review = reviews[0]
                                review_payload = {
                                    "workflow_id": review["workflow_id"],
                                    "action": "modify",
                                    "modified_data": {
                                        "loan_amount": 450000,  # Reduced amount
                                        "approved": True,
                                        "conditions": ["Provide additional income verification"]
                                    },
                                    "comments": "Approved with reduced amount and conditions",
                                    "reviewer_id": "loan_officer_001"
                                }
                                
                                print(f"🧑‍💼 Processing review with modifications...")
                                review_response = requests.post(
                                    f"{BASE_URL}/human-workflow/review",
                                    json=review_payload,
                                    timeout=TIMEOUT
                                )
                                
                                if review_response.status_code == 200:
                                    print(f"✅ Review processed: {review_response.json()}")
                                else:
                                    print(f"❌ Review failed: {review_response.status_code}")
                        break
                        
                    elif current_status in ["completed", "failed", "cancelled"]:
                        print(f"🏁 Workflow finished with status: {current_status}")
                        print(f"📊 Final state: {json.dumps(status, indent=2)}")
                        break
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    break
            else:
                print("⏰ Polling timeout - workflow may still be running")
                
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_demo_endpoint():
    """Test the comprehensive demo endpoint."""
    print("\n🎭 Testing Demo Endpoint")
    print("=" * 60)
    
    try:
        print(f"📤 Calling demo endpoint: {BASE_URL}/human-workflow/demo")
        
        response = requests.post(f"{BASE_URL}/human-workflow/demo", timeout=TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Demo completed successfully!")
            print(f"📖 Concept explanation: {result.get('concept_explanation', {}).get('what_is_human_in_loop')}")
            print(f"🔄 Sync vs Async: {json.dumps(result.get('concept_explanation', {}).get('sync_vs_async'), indent=2)}")
            print(f"📈 Benefits: {result.get('concept_explanation', {}).get('key_benefits')}")
            print(f"👥 Next steps: {result.get('next_steps')}")
        else:
            print(f"❌ Demo failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_pending_reviews():
    """Test getting pending reviews."""
    print("\n📋 Testing Pending Reviews Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/human-workflow/pending-reviews", timeout=TIMEOUT)
        
        if response.status_code == 200:
            reviews = response.json()
            print(f"✅ Found {len(reviews)} pending reviews")
            
            for i, review in enumerate(reviews[:3], 1):  # Show first 3 reviews
                print(f"\n📝 Review {i}:")
                print(f"   Workflow ID: {review.get('workflow_id')}")
                print(f"   User ID: {review.get('user_id')}")
                print(f"   Step: {review.get('step_name')}")
                print(f"   Description: {review.get('step_description')}")
                print(f"   Created: {review.get('created_at')}")
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_server_health():
    """Check if the FastAPI server is running."""
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run all tests."""
    print("🧪 Human-in-the-Loop Workflow Test Suite")
    print("=" * 60)
    
    # Check server health
    if not check_server_health():
        print("❌ FastAPI server is not running!")
        print("💡 Start the server with: python main.py")
        return
    
    print("✅ FastAPI server is running")
    
    # Run tests
    test_demo_endpoint()
    test_pending_reviews()
    test_sync_workflow()
    test_async_workflow()
    
    print("\n🎉 Test suite completed!")
    print("\n📚 For more information, check:")
    print("   - API docs: http://localhost:8000/docs")
    print("   - Documentation: human_in_loop_documentation.md")
    print("   - Server logs for detailed execution info")

if __name__ == "__main__":
    main() 