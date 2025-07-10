from fastapi.responses import JSONResponse
from fastapi import status
from models.schemas import ErrorResponse, FieldSchema
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def error_response(message: str, code: int = status.HTTP_400_BAD_REQUEST):
    return JSONResponse(
        status_code=code,
        content=ErrorResponse(detail=message).dict()
    )

def generate_question(field_schema: FieldSchema) -> str:
    """
    Generate a clear, concise question for the user based on the field schema.
    """
    field_name = field_schema.field
    fmt = field_schema.format
    required = field_schema.isRequired
    prompt = f"What is your {field_name}?"
    if fmt and fmt != "string":
        prompt += f" (Please provide a {fmt})"
    if not required:
        prompt += " (Optional)"
    return prompt

def llm_is_greeting(user_message):
    prompt = (
        f"Is the following message a greeting (like 'hello', 'hi', 'hey', etc.)? "
        f"Respond with only 'yes' or 'no'.\nMessage: \"{user_message}\""
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=3,
        temperature=0,
    )
    return response.choices[0].message.content.strip().lower() == "yes"

def llm_validate_answer(field_schema, user_answer):
    prompt = (
        f"Field: {field_schema.field}\n"
        f"Expected format: {field_schema.format}\n"
        f"Required: {'yes' if field_schema.isRequired else 'no'}\n"
        f"User answer: {user_answer}\n"
        "Is this a valid answer for the field? Respond with only 'yes' or 'no'."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=3,
        temperature=0,
    )
    return response.choices[0].message.content.strip().lower() == "yes"

def get_field_path(field_schema, parent_path=None):
    if parent_path:
        return f"{parent_path} {field_schema.field}"
    return field_schema.field

def llm_generate_question(field_schema, parent_path=None, messages=None):
    field_path = get_field_path(field_schema, parent_path)
    schema_desc = (
        f"Field: {field_path}\n"
        f"Expected format: {field_schema.format}\n"
        f"Required: {'yes' if field_schema.isRequired else 'no'}"
    )
    prompt = (
        "You are a polite, friendly assistant helping a user fill out a form. "
        "Based on the conversation so far and the following schema, "
        "please ask the user the next required question in a clear and friendly way.\n"
        f"Schema:\n{schema_desc}"
    )
    chat_msgs = messages[:] if messages else []
    chat_msgs.append({"role": "system", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_msgs,
        max_tokens=50,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def llm_extract_and_validate(field_schema, user_message, parent_path=None, messages=None):
    field_path = get_field_path(field_schema, parent_path)
    schema_desc = (
        f"Field: {field_path}\n"
        f"Expected format: {field_schema.format}\n"
        f"Required: {'yes' if field_schema.isRequired else 'no'}"
    )
    prompt = (
        f"You are a data collection assistant. "
        f"Given the following field schema:\n{schema_desc}\n"
        f"The user said: \"{user_message}\"\n"
        f"1. If the message answers the field, extract the value as JSON: {{ \"{field_schema.field}\": value }}.\n"
        f"2. If the input is invalid, reply with a JSON object: {{ \"error\": \"reason\", \"examples\": [example1, example2] }}.\n"
        f"3. If the message does not answer this field, reply with: {{ \"error\": \"Field not answered\" }}."
    )
    chat_msgs = messages[:] if messages else []
    chat_msgs.append({"role": "user", "content": user_message})
    chat_msgs.append({"role": "system", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_msgs,
        max_tokens=200,
        temperature=0.2,
    )
    import json as pyjson
    try:
        return pyjson.loads(response.choices[0].message.content.strip())
    except Exception:
        return {"error": "Could not parse LLM response."}
