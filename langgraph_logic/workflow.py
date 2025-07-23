from langgraph_logic.schema_loader import load_schema
from langgraph_logic.persistence import save_state, load_state, save_chat_message, load_chat_history
from models.schemas import FieldSchema
from typing import Dict, Any, List
from langgraph_logic.utils import generate_question, llm_generate_question, llm_is_greeting, llm_extract_and_validate, get_field_path

class UserState:
    def __init__(self, user_id: str, collected: dict = None, current_index: int = 0, subfield_stack: list = None):
        self.user_id = user_id
        self.collected = collected or {}
        self.current_index = current_index
        self.subfield_stack = subfield_stack or []  # Stack of (parent_path, subfields, subfield_index)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "collected": self.collected,
            "current_index": self.current_index,
            "subfield_stack": self.subfield_stack
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            collected=data.get("collected", {}),
            current_index=data.get("current_index", 0),
            subfield_stack=data.get("subfield_stack", [])
        )

def get_next_field(schema, state):
    # If in a subfield stack, get the next subfield
    if state.subfield_stack:
        parent_path, subfields, subfield_index = state.subfield_stack[-1]
        # Reconstruct FieldSchema objects if needed
        subfields = [FieldSchema(**sf) if isinstance(sf, dict) else sf for sf in subfields]
        if subfield_index < len(subfields):
            return subfields[subfield_index], parent_path
        else:
            # Done with this subfield group, pop and continue
            state.subfield_stack.pop()
            return get_next_field(schema, state)
    # Otherwise, get the next top-level field
    if state.current_index < len(schema):
        field = schema[state.current_index]
        if getattr(field, 'subFields', None):
            # Enter subfields, store as dicts
            state.subfield_stack.append([
                field.field,
                [subfield.model_dump() for subfield in field.subFields],
                0
            ])
            return get_next_field(schema, state)
        return field, None
    return None, None

def update_state_with_input(state, field, value, parent_path=None):
    # If in subfield, update nested dict
    if parent_path:
        if parent_path not in state.collected:
            state.collected[parent_path] = {}
        state.collected[parent_path][field] = value
        # Increment subfield index
        state.subfield_stack[-1][2] += 1
    else:
        state.collected[field] = value
        state.current_index += 1
    return state

def is_complete(schema, state):
    return state.current_index >= len(schema) and not state.subfield_stack

# LangGraph workflow definition
def run_workflow(user_id: str, user_input: str = None) -> dict:
    schema = load_schema()
    raw_state = load_state(user_id)
    state = UserState.from_dict(raw_state) if raw_state else UserState(user_id)
    chat_history = load_chat_history(user_id)
    messages = chat_history[:]

    # If user provided input, check if it's a greeting
    if user_input and isinstance(user_input, str):
        if llm_is_greeting(user_input):
            save_chat_message(user_id, "user", user_input)
            save_chat_message(user_id, "assistant", "Hello! Let's get started.")
            return {"done": False, "question": "Hello! Let's get started."}

    # If user provided input, extract and validate
    if user_input and isinstance(user_input, str):
        next_field, parent_path = get_next_field(schema, state)
        if next_field is None:
            return {"done": True, "data": state.collected, "error": "All fields are already collected."}
        result = llm_extract_and_validate(next_field, user_input, parent_path, messages)
        if "error" in result:
            question = llm_generate_question(next_field, parent_path, messages)
            save_chat_message(user_id, "user", user_input)
            save_chat_message(user_id, "assistant", f"{result['error']} {question}")
            return {
                "done": False,
                "next_field": next_field.model_dump(),
                "question": f"{result['error']} {question}",
                "examples": result.get("examples", [])
            }
        # Extracted value is valid
        value = result[next_field.field]
        state = update_state_with_input(state, next_field.field, value, parent_path)
        save_state(user_id, state.to_dict())
        save_chat_message(user_id, "user", user_input)
        save_chat_message(user_id, "assistant", str(value))

    # Check if complete
    if is_complete(schema, state):
        return {"done": True, "data": state.collected}

    # Otherwise, return next field to collect
    next_field, parent_path = get_next_field(schema, state)
    question = llm_generate_question(next_field, parent_path, messages)
    save_chat_message(user_id, "assistant", question)
    return {"done": False, "next_field": next_field.model_dump(), "question": question}
