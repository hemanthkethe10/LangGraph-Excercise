"""
LLM-Driven Workflow for Schema-Agnostic Data Collection

This module provides a completely LLM-driven approach where:
- LLM analyzes any JSON schema dynamically
- LLM generates contextual questions based on schema
- LLM validates all user responses
- LLM extracts and structures data
- LLM provides error messages and guidance
- Uses Chain of Thought prompting for better reasoning

Just change the schema.json and it works for any field structure!
"""

from langgraph_logic.schema_loader import load_schema
from langgraph_logic.persistence import save_state, load_state, save_chat_message, load_chat_history
from langgraph_logic.utils import client
from typing import Dict, Any, List, Optional
import json

class LLMDrivenState:
    """Simple state management for LLM-driven workflow."""
    
    def __init__(self, user_id: str, collected: dict = None, conversation_context: dict = None):
        self.user_id = user_id
        self.collected = collected or {}
        self.conversation_context = conversation_context or {
            "fields_completed": [],
            "current_conversation": [],
            "user_name": None,
            "form_started": False
        }

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "collected": self.collected,
            "conversation_context": self.conversation_context
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            collected=data.get("collected", {}),
            conversation_context=data.get("conversation_context", {
                "fields_completed": [],
                "current_conversation": [],
                "user_name": None,
                "form_started": False
            })
        )

def llm_analyze_schema_and_progress(schema: List[Dict], collected_data: Dict, conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    LLM analyzes the schema and current progress to determine next steps.
    Uses Chain of Thought reasoning.
    """
    
    schema_json = json.dumps(schema, indent=2)
    collected_json = json.dumps(collected_data, indent=2)
    history_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-6:]])  # Last 6 messages for context
    
    prompt = f"""
You are an intelligent form assistant that helps users fill out forms dynamically based on any given schema.

CHAIN OF THOUGHT ANALYSIS:

1. SCHEMA ANALYSIS:
Schema to collect:
{schema_json}

2. CURRENT PROGRESS:
Data collected so far:
{collected_json}

3. CONVERSATION HISTORY:
Recent conversation:
{history_summary}

4. REASONING PROCESS:
Now I need to think step by step:

a) What fields are defined in the schema?
b) Which fields have already been collected successfully?
c) Which is the next field that needs to be collected?
d) Is the form complete (all required fields collected)?
e) What's the appropriate question for the next field considering the conversation context?

5. DECISION:
Based on my analysis, I will determine:
- Is the form complete? (true/false)
- What is the next field to collect? (if not complete)
- What question should I ask? (contextual and user-friendly)
- How many fields are completed vs total?

Please respond with a JSON object in this exact format:
{{
    "form_complete": false,
    "next_field": {{
        "field_name": "FieldName",
        "field_path": "ParentField.ChildField" or "FieldName",
        "is_required": true,
        "field_type": "string/number/object",
        "description": "What this field represents"
    }},
    "progress": {{
        "completed": 2,
        "total": 5,
        "percentage": 40
    }},
    "question": "User-friendly question to ask for the next field",
    "reasoning": "Brief explanation of why this field is next"
}}

If the form is complete, set form_complete to true and omit next_field.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better reasoning
            messages=[{"role": "system", "content": prompt}],
            max_tokens=800,
            temperature=0.3,
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
    except Exception as e:
        # Fallback response
        return {
            "form_complete": False,
            "next_field": {"field_name": "unknown", "field_path": "unknown", "is_required": True, "field_type": "string", "description": "Next field"},
            "progress": {"completed": 0, "total": 1, "percentage": 0},
            "question": "I need to analyze the form structure. Could you please provide your response again?",
            "reasoning": f"Error in analysis: {str(e)}"
        }

def llm_validate_and_extract(user_input: str, expected_field: Dict, schema: List[Dict], collected_data: Dict, conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    LLM validates user input and extracts the value for the expected field.
    Uses Chain of Thought reasoning.
    """
    
    schema_json = json.dumps(schema, indent=2)
    collected_json = json.dumps(collected_data, indent=2)
    field_info = json.dumps(expected_field, indent=2)
    history_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-4:]])
    
    prompt = f"""
You are a smart form validation assistant. I need you to validate and extract data from user input.

CHAIN OF THOUGHT VALIDATION:

1. CONTEXT:
Full schema:
{schema_json}

Expected field to collect:
{field_info}

Current collected data:
{collected_json}

Recent conversation:
{history_summary}

2. USER INPUT TO VALIDATE:
"{user_input}"

3. REASONING PROCESS:
Let me think through this step by step:

a) What field am I trying to collect?
b) What type of data is expected (string, number, object)?
c) Is the user input relevant to this field?
d) Can I extract a valid value from their input?
e) If not valid, what specific guidance should I provide?

4. VALIDATION DECISION:
Based on my analysis:
- Is the input valid for this field?
- What value should I extract?
- What error message and suggestions if invalid?

Please respond with a JSON object in this exact format:

For VALID input:
{{
    "valid": true,
    "extracted_value": "the extracted value",
    "field_name": "FieldName",
    "acknowledgment": "Friendly confirmation message"
}}

For INVALID input:
{{
    "valid": false,
    "error_message": "Clear explanation of what's wrong",
    "suggestions": ["suggestion 1", "suggestion 2"],
    "examples": ["example 1", "example 2"],
    "retry_question": "Rephrased question to help user"
}}

Be helpful and understanding in your responses.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
    except Exception as e:
        return {
            "valid": False,
            "error_message": "I had trouble processing your response. Could you please try again?",
            "suggestions": ["Please rephrase your answer", "Provide the information more clearly"],
            "examples": [],
            "retry_question": "Could you please provide that information again?"
        }

def llm_generate_completion_summary(schema: List[Dict], collected_data: Dict, conversation_context: Dict) -> str:
    """
    LLM generates a comprehensive completion summary with final JSON.
    """
    
    schema_json = json.dumps(schema, indent=2)
    collected_json = json.dumps(collected_data, indent=2)
    user_name = conversation_context.get("user_name", "")
    
    prompt = f"""
You are completing a form collection process. Generate a comprehensive, professional summary.

CONTEXT:
Original schema:
{schema_json}

Collected data:
{collected_json}

User name: {user_name if user_name else "Not provided"}

Please create a completion summary that includes:

1. A congratulatory message
2. A human-readable summary of what was collected
3. The complete JSON data in a formatted code block
4. A professional closing

Make it warm, professional, and clear. Use emojis appropriately to make it engaging.

Format your response as plain text (not JSON).
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=800,
            temperature=0.7,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"""
🎉 Congratulations! Your form has been completed successfully.

📊 Collected Information:
{json.dumps(collected_data, indent=2)}

✅ All required information has been gathered. Thank you for your participation!
"""

def llm_handle_greeting(user_input: str, schema: List[Dict]) -> str:
    """
    LLM generates a contextual welcome message based on the schema.
    """
    
    schema_json = json.dumps(schema, indent=2)
    
    prompt = f"""
A user has just greeted you with: "{user_input}"

You are a form assistant and need to respond warmly and explain what you'll be collecting based on this schema:
{schema_json}

Generate a friendly, professional welcome message that:
1. Responds to their greeting
2. Explains what information you'll be collecting (based on the schema)
3. Sets expectations about the process
4. Encourages them to start

Keep it concise but warm. Use emojis appropriately.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "👋 Hello! I'm here to help you fill out a form. Let's get started by collecting some information from you."

def llm_detect_greeting(user_input: str) -> bool:
    """
    LLM detects if user input is a greeting.
    """
    
    prompt = f"""
Determine if this user input is a greeting or conversation starter: "{user_input}"

Common greetings include: hello, hi, hey, good morning, start, begin, etc.

Respond with just "true" or "false".
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        
        return response.choices[0].message.content.strip().lower() == "true"
    except Exception:
        return False

def update_collected_data(collected_data: Dict, field_path: str, value: Any) -> Dict:
    """
    Update collected data with new field value, handling nested paths.
    """
    
    if "." in field_path:
        # Handle nested fields like "Address.Street"
        parts = field_path.split(".")
        current = collected_data
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the final value
        current[parts[-1]] = value
    else:
        # Simple field
        collected_data[field_path] = value
    
    return collected_data

def run_llm_driven_workflow(user_id: str, user_input: str = None) -> dict:
    """
    LLM-driven workflow that adapts to any schema structure.
    
    Features:
    - Schema-agnostic: Works with any JSON schema
    - LLM handles all validation and navigation
    - Chain of Thought reasoning for better decisions
    - Dynamic question generation
    - Smart error handling
    """
    
    # Load schema and state
    raw_schema = load_schema()
    # Convert FieldSchema objects to dictionaries for JSON serialization
    schema = []
    for field in raw_schema:
        if hasattr(field, 'model_dump'):
            schema.append(field.model_dump())
        elif isinstance(field, dict):
            schema.append(field)
        else:
            # Convert object to dict manually
            field_dict = {
                'field': getattr(field, 'field', 'unknown'),
                'isRequired': getattr(field, 'isRequired', True),
                'format': getattr(field, 'format', 'string')
            }
            if hasattr(field, 'subFields') and field.subFields:
                field_dict['subFields'] = [
                    sf.model_dump() if hasattr(sf, 'model_dump') else sf 
                    for sf in field.subFields
                ]
            schema.append(field_dict)
    
    raw_state = load_state(user_id)
    state = LLMDrivenState.from_dict(raw_state) if raw_state else LLMDrivenState(user_id)
    chat_history = load_chat_history(user_id)
    
    # Convert chat history to conversation context
    conversation_messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    
    # Handle greetings
    if user_input and llm_detect_greeting(user_input):
        welcome_message = llm_handle_greeting(user_input, schema)
        state.conversation_context["form_started"] = True
        
        save_chat_message(user_id, "user", user_input)
        save_chat_message(user_id, "assistant", welcome_message)
        save_state(user_id, state.to_dict())
        
        return {
            "done": False,
            "question": welcome_message,
            "conversation_type": "greeting"
        }
    
    # Process user input if provided
    if user_input and isinstance(user_input, str):
        # Get current progress and next field
        analysis = llm_analyze_schema_and_progress(schema, state.collected, conversation_messages)
        
        if not analysis.get("form_complete", False):
            next_field = analysis.get("next_field", {})
            
            # Validate the user input for the expected field
            validation_result = llm_validate_and_extract(
                user_input, next_field, schema, state.collected, conversation_messages
            )
            
            if validation_result.get("valid", False):
                # Extract and store the value
                field_name = validation_result.get("field_name")
                field_path = next_field.get("field_path", field_name)
                extracted_value = validation_result.get("extracted_value")
                
                # Update collected data
                state.collected = update_collected_data(state.collected, field_path, extracted_value)
                state.conversation_context["fields_completed"].append(field_path)
                
                # Store user name for context
                if field_name.lower() in ["name", "fullname", "username"] and not state.conversation_context.get("user_name"):
                    state.conversation_context["user_name"] = str(extracted_value)
                
                # Save state and messages
                save_state(user_id, state.to_dict())
                save_chat_message(user_id, "user", user_input)
                save_chat_message(user_id, "assistant", validation_result.get("acknowledgment", "Got it! ✅"))
                
            else:
                # Handle validation error
                error_message = validation_result.get("error_message", "Invalid input")
                suggestions = validation_result.get("suggestions", [])
                examples = validation_result.get("examples", [])
                retry_question = validation_result.get("retry_question", "Please try again.")
                
                # Format error response
                error_response = f"💭 {error_message}"
                if suggestions:
                    error_response += f"\n\n💡 Suggestions:\n" + "\n".join([f"• {s}" for s in suggestions])
                if examples:
                    error_response += f"\n\n📝 Examples:\n" + "\n".join([f"• {e}" for e in examples])
                
                error_response += f"\n\n{retry_question}"
                
                save_chat_message(user_id, "user", user_input)
                save_chat_message(user_id, "assistant", error_response)
                
                return {
                    "done": False,
                    "question": error_response,
                    "conversation_type": "error_correction",
                    "field_info": next_field
                }
    
    # Get current status and next steps
    analysis = llm_analyze_schema_and_progress(schema, state.collected, conversation_messages)
    
    # Check if form is complete
    if analysis.get("form_complete", False):
        completion_summary = llm_generate_completion_summary(schema, state.collected, state.conversation_context)
        
        return {
            "done": True,
            "data": state.collected,
            "summary": completion_summary,
            "conversation_type": "completion"
        }
    
    # Generate next question
    next_field = analysis.get("next_field", {})
    question = analysis.get("question", "What would you like to provide next?")
    progress = analysis.get("progress", {})
    
    # Add progress indicator to question
    if progress:
        progress_text = f"📋 Progress: {progress['completed']}/{progress['total']} fields ({progress['percentage']}%)"
        question = f"{progress_text}\n\n{question}"
    
    save_chat_message(user_id, "assistant", question)
    save_state(user_id, state.to_dict())
    
    return {
        "done": False,
        "question": question,
        "conversation_type": "data_collection",
        "field_info": next_field,
        "progress": progress
    } 