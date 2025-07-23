"""
Enhanced Production-Ready Workflow for LangGraph

This module provides a smooth, user-friendly chatbot experience with:
- Context-aware question generation
- Progress tracking and indicators
- Proper validation with helpful error messages
- Clear completion flow with final JSON summary
- Production-ready conversation management
"""

from langgraph_logic.schema_loader import load_schema
from langgraph_logic.persistence import save_state, load_state, save_chat_message, load_chat_history
from models.schemas import FieldSchema
from typing import Dict, Any, List, Optional, Tuple
from langgraph_logic.utils import get_field_path
import json
import re

class EnhancedUserState:
    def __init__(self, user_id: str, collected: dict = None, current_index: int = 0, 
                 subfield_stack: list = None, conversation_context: dict = None):
        self.user_id = user_id
        self.collected = collected or {}
        self.current_index = current_index
        self.subfield_stack = subfield_stack or []
        self.conversation_context = conversation_context or {
            "user_name": None,
            "fields_completed": [],
            "total_fields": 0,
            "current_section": None
        }

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "collected": self.collected,
            "current_index": self.current_index,
            "subfield_stack": self.subfield_stack,
            "conversation_context": self.conversation_context
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            collected=data.get("collected", {}),
            current_index=data.get("current_index", 0),
            subfield_stack=data.get("subfield_stack", []),
            conversation_context=data.get("conversation_context", {
                "user_name": None, "fields_completed": [], "total_fields": 0, "current_section": None
            })
        )

class ProductionReadyChatbot:
    """Production-ready chatbot with enhanced conversation flow."""
    
    def __init__(self):
        self.field_descriptions = {
            "Name": "your full name",
            "Age": "your age",
            "DoorNo": "your house/door number",
            "Street": "your street name",
            "Pincode": "your postal/ZIP code",
            "Address": "your complete address"
        }
        
        self.field_examples = {
            "Name": ["John Smith", "Mary Johnson", "David Wilson"],
            "Age": ["25", "30", "45"],
            "DoorNo": ["123", "45A", "B-102"],
            "Street": ["Main Street", "Oak Avenue", "Park Road"],
            "Pincode": ["12345", "SW1A 1AA", "10001"]
        }
        
        self.validation_patterns = {
            "string": r".+",
            "number": r"^\d+$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }

    def enhanced_llm_is_greeting(self, user_message: str) -> bool:
        """Enhanced greeting detection with common variations."""
        greeting_patterns = [
            r'\b(hi|hello|hey|hiya|greetings)\b',
            r'\b(good\s+(morning|afternoon|evening))\b',
            r'\b(start|begin|let\'s\s+start)\b'
        ]
        user_message_lower = user_message.lower().strip()
        
        for pattern in greeting_patterns:
            if re.search(pattern, user_message_lower):
                return True
        return len(user_message_lower.split()) <= 3 and any(
            word in user_message_lower for word in ['hi', 'hello', 'hey', 'start']
        )

    def generate_welcome_message(self) -> str:
        """Generate a warm, professional welcome message."""
        return (
            "👋 Hello! I'm here to help you fill out your information form. "
            "This will only take a few minutes, and I'll guide you through each step. "
            "Let's start with your basic details!"
        )

    def get_progress_indicator(self, state: EnhancedUserState, schema: List[FieldSchema]) -> str:
        """Generate a progress indicator for the user."""
        total_fields = self.count_total_fields(schema)
        completed_fields = len(state.conversation_context.get("fields_completed", []))
        progress_percent = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
        
        progress_bar = "▓" * (progress_percent // 10) + "░" * (10 - (progress_percent // 10))
        return f"📋 Progress: [{progress_bar}] {progress_percent}% ({completed_fields}/{total_fields} fields)"

    def count_total_fields(self, schema: List[FieldSchema]) -> int:
        """Count total number of fields including subfields."""
        total = 0
        for field in schema:
            if field.subFields:
                total += len(field.subFields)
            else:
                total += 1
        return total

    def generate_contextual_question(self, field_schema: FieldSchema, parent_path: Optional[str], 
                                   state: EnhancedUserState, schema: List[FieldSchema]) -> str:
        """Generate context-aware, user-friendly questions."""
        
        field_name = field_schema.field
        field_desc = self.field_descriptions.get(field_name, field_name.lower())
        examples = self.field_examples.get(field_name, [])
        user_name = state.conversation_context.get("user_name", "")
        
        # Progress indicator
        progress = self.get_progress_indicator(state, schema)
        
        # Personalize with user's name if available
        greeting = f"Thanks, {user_name}! " if user_name and user_name != field_name else ""
        
        # Context-aware question based on field type and position
        if parent_path == "Address":
            if field_name == "DoorNo":
                question = f"{greeting}Now I need your address details. What's your house or apartment number?"
            elif field_name == "Street":
                question = f"{greeting}What's the street name for your address?"
            elif field_name == "Pincode":
                question = f"{greeting}Finally, what's your postal/ZIP code?"
        else:
            if field_name == "Name":
                question = "Let's start with your full name. What should I call you?"
            elif field_name == "Age":
                question = f"{greeting}Could you share your age? (This field is optional)"
            else:
                question = f"{greeting}Please provide {field_desc}."
        
        # Add examples for clarity
        if examples and field_schema.isRequired:
            examples_text = ", ".join(f'"{ex}"' for ex in examples[:2])
            question += f" For example: {examples_text}"
        
        # Add requirement indicator
        req_indicator = " ✓ Required" if field_schema.isRequired else " (Optional)"
        
        return f"{progress}\n\n{question}{req_indicator}"

    def validate_and_extract_with_context(self, field_schema: FieldSchema, user_message: str, 
                                        state: EnhancedUserState) -> Dict[str, Any]:
        """Enhanced validation with context-aware error messages."""
        
        field_name = field_schema.field
        field_format = field_schema.format
        user_message_clean = user_message.strip()
        
        # Extract user name for context
        if field_name == "Name" and not state.conversation_context.get("user_name"):
            # Extract name from various formats
            name_patterns = [
                r'(?:my name is|i\'m|i am|call me)\s+([a-zA-Z\s]+)',
                r'^([a-zA-Z\s]+)$'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, user_message_clean, re.IGNORECASE)
                if match:
                    extracted_name = match.group(1).strip().title()
                    if len(extracted_name.split()) <= 4:  # Reasonable name length
                        state.conversation_context["user_name"] = extracted_name
                        return {field_name: extracted_name}
        
        # Number validation
        if field_format == "number":
            numbers = re.findall(r'\d+', user_message_clean)
            if numbers:
                return {field_name: int(numbers[0])}
            elif not field_schema.isRequired and any(word in user_message_clean.lower() 
                                                   for word in ['skip', 'pass', 'no', 'none', 'prefer not']):
                return {field_name: None}
            else:
                examples = self.field_examples.get(field_name, ["123"])
                return {
                    "error": f"I need a number for {self.field_descriptions.get(field_name, field_name)}.",
                    "examples": examples,
                    "suggestion": f"Please provide just the number, like: {examples[0]}"
                }
        
        # String validation
        if field_format == "string":
            # Extract meaningful text (not just numbers for string fields)
            if field_name in ["DoorNo"]:
                # Door numbers can be alphanumeric
                door_patterns = [r'(?:door|house|apartment|unit)?\s*(?:number|no\.?)?\s*([a-zA-Z0-9-]+)', r'^([a-zA-Z0-9-]+)$']
                for pattern in door_patterns:
                    match = re.search(pattern, user_message_clean, re.IGNORECASE)
                    if match:
                        return {field_name: match.group(1).strip()}
            else:
                # Regular string fields
                text_pattern = r'(?:is|called|name|street)?\s*([a-zA-Z\s]+)'
                match = re.search(text_pattern, user_message_clean, re.IGNORECASE)
                if match:
                    extracted_text = match.group(1).strip()
                    if len(extracted_text) >= 2:  # Minimum meaningful length
                        return {field_name: extracted_text.title()}
                
                # If no pattern match, check if it's a simple direct answer
                if len(user_message_clean) >= 2 and user_message_clean.replace(' ', '').isalpha():
                    return {field_name: user_message_clean.title()}
            
            examples = self.field_examples.get(field_name, ["Example"])
            return {
                "error": f"I couldn't understand the {self.field_descriptions.get(field_name, field_name)} you provided.",
                "examples": examples,
                "suggestion": f"Please provide it like: {examples[0]}"
            }
        
        # Fallback for unrecognized input
        return {
            "error": "I didn't quite catch that. Could you please rephrase your answer?",
            "examples": self.field_examples.get(field_name, []),
            "suggestion": "Try providing just the information requested."
        }

    def generate_completion_summary(self, collected_data: Dict[str, Any], user_name: str = None) -> str:
        """Generate a comprehensive completion summary with final JSON."""
        
        # Create a user-friendly summary
        summary_parts = []
        summary_parts.append("🎉 Perfect! I've collected all your information. Here's a summary:")
        summary_parts.append("")
        
        # Personal details
        if "Name" in collected_data:
            summary_parts.append(f"👤 **Name**: {collected_data['Name']}")
        
        if "Age" in collected_data and collected_data["Age"]:
            summary_parts.append(f"📅 **Age**: {collected_data['Age']}")
        
        # Address details
        if "Address" in collected_data:
            addr = collected_data["Address"]
            address_line = f"{addr.get('DoorNo', '')}, {addr.get('Street', '')}, {addr.get('Pincode', '')}"
            summary_parts.append(f"🏠 **Address**: {address_line}")
        
        summary_parts.append("")
        summary_parts.append("📄 **Complete Data in JSON Format**:")
        summary_parts.append("```json")
        summary_parts.append(json.dumps(collected_data, indent=2))
        summary_parts.append("```")
        
        summary_parts.append("")
        summary_parts.append("✅ **Form completed successfully!** Thank you for providing your information.")
        
        return "\n".join(summary_parts)

    def handle_error_with_context(self, error_info: Dict[str, Any], field_schema: FieldSchema) -> str:
        """Generate user-friendly error messages with helpful suggestions."""
        
        error_msg = error_info.get("error", "")
        suggestion = error_info.get("suggestion", "")
        examples = error_info.get("examples", [])
        
        user_friendly_msg = f"💭 {error_msg}"
        
        if suggestion:
            user_friendly_msg += f"\n\n💡 **Suggestion**: {suggestion}"
        
        if examples:
            user_friendly_msg += f"\n\n📝 **Examples**: {', '.join(examples[:2])}"
        
        return user_friendly_msg


def get_next_field_enhanced(schema: List[FieldSchema], state: EnhancedUserState) -> Tuple[Optional[FieldSchema], Optional[str]]:
    """Enhanced field navigation with better state management."""
    # Handle subfields
    if state.subfield_stack:
        parent_path, subfields, subfield_index = state.subfield_stack[-1]
        subfields = [FieldSchema(**sf) if isinstance(sf, dict) else sf for sf in subfields]
        if subfield_index < len(subfields):
            return subfields[subfield_index], parent_path
        else:
            # Done with subfields, pop and continue
            state.subfield_stack.pop()
            return get_next_field_enhanced(schema, state)
    
    # Handle main fields
    if state.current_index < len(schema):
        field = schema[state.current_index]
        if getattr(field, 'subFields', None):
            # Enter subfields
            state.subfield_stack.append([
                field.field,
                [subfield.model_dump() for subfield in field.subFields],
                0
            ])
            state.conversation_context["current_section"] = field.field
            return get_next_field_enhanced(schema, state)
        return field, None
    return None, None


def update_state_enhanced(state: EnhancedUserState, field: str, value: Any, parent_path: Optional[str] = None):
    """Enhanced state update with conversation context tracking."""
    
    if parent_path:
        if parent_path not in state.collected:
            state.collected[parent_path] = {}
        state.collected[parent_path][field] = value
        # Increment subfield index
        if state.subfield_stack:
            state.subfield_stack[-1][2] += 1
        # Track completed field
        state.conversation_context["fields_completed"].append(f"{parent_path}.{field}")
    else:
        state.collected[field] = value
        state.current_index += 1
        # Track completed field
        state.conversation_context["fields_completed"].append(field)
        
        # Update conversation context
        if field == "Name" and value:
            state.conversation_context["user_name"] = value
    
    return state


def is_complete_enhanced(schema: List[FieldSchema], state: EnhancedUserState) -> bool:
    """Enhanced completion check."""
    return state.current_index >= len(schema) and not state.subfield_stack


def run_enhanced_workflow(user_id: str, user_input: str = None) -> dict:
    """
    Enhanced workflow with production-ready conversation flow.
    
    Features:
    - Context-aware question generation
    - Progress tracking
    - User-friendly error handling
    - Smooth conversation flow
    - Professional completion summary
    """
    
    schema = load_schema()
    raw_state = load_state(user_id)
    state = EnhancedUserState.from_dict(raw_state) if raw_state else EnhancedUserState(user_id)
    chatbot = ProductionReadyChatbot()
    
    # Initialize conversation context
    if not state.conversation_context.get("total_fields"):
        state.conversation_context["total_fields"] = chatbot.count_total_fields(schema)
    
    # Handle greetings
    if user_input and chatbot.enhanced_llm_is_greeting(user_input):
        welcome_msg = chatbot.generate_welcome_message()
        save_chat_message(user_id, "user", user_input)
        save_chat_message(user_id, "assistant", welcome_msg)
        return {"done": False, "question": welcome_msg, "conversation_type": "greeting"}
    
    # Process user input
    if user_input and isinstance(user_input, str):
        next_field, parent_path = get_next_field_enhanced(schema, state)
        if next_field is None:
            # Form is complete
            completion_summary = chatbot.generate_completion_summary(
                state.collected, 
                state.conversation_context.get("user_name")
            )
            return {
                "done": True, 
                "data": state.collected,
                "summary": completion_summary,
                "conversation_type": "completion"
            }
        
        # Validate and extract
        result = chatbot.validate_and_extract_with_context(next_field, user_input, state)
        
        if "error" in result:
            # Handle error with context
            error_msg = chatbot.handle_error_with_context(result, next_field)
            retry_question = chatbot.generate_contextual_question(next_field, parent_path, state, schema)
            
            full_response = f"{error_msg}\n\n{retry_question}"
            
            save_chat_message(user_id, "user", user_input)
            save_chat_message(user_id, "assistant", full_response)
            
            return {
                "done": False,
                "next_field": next_field.model_dump(),
                "question": full_response,
                "conversation_type": "error_correction",
                "error_details": result
            }
        
        # Success - update state
        value = result[next_field.field]
        state = update_state_enhanced(state, next_field.field, value, parent_path)
        save_state(user_id, state.to_dict())
        
        # Generate acknowledgment
        user_name = state.conversation_context.get("user_name", "")
        if next_field.field == "Name":
            acknowledgment = f"Nice to meet you, {value}! ✅"
        elif parent_path == "Address":
            acknowledgment = f"Got it! ✅"
        else:
            acknowledgment = f"Perfect! ✅"
        
        save_chat_message(user_id, "user", user_input)
        save_chat_message(user_id, "assistant", acknowledgment)
    
    # Check if complete
    if is_complete_enhanced(schema, state):
        completion_summary = chatbot.generate_completion_summary(
            state.collected, 
            state.conversation_context.get("user_name")
        )
        return {
            "done": True, 
            "data": state.collected,
            "summary": completion_summary,
            "conversation_type": "completion"
        }
    
    # Generate next question
    next_field, parent_path = get_next_field_enhanced(schema, state)
    question = chatbot.generate_contextual_question(next_field, parent_path, state, schema)
    save_chat_message(user_id, "assistant", question)
    
    return {
        "done": False, 
        "next_field": next_field.model_dump(), 
        "question": question,
        "conversation_type": "data_collection"
    } 