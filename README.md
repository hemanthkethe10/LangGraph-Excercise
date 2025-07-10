# LangGraph-Excercise

# LangGraph FastAPI Project

## Running the Project with uv

1. **Install [uv](https://github.com/astral-sh/uv):**

   ```sh
   curl -Ls https://astral.sh/uv/install.sh | sh
   # or
   brew install uv
   ```

2. **Install dependencies:**

   ```sh
   uv pip install -r requirements.txt
   ```

3. **Run the FastAPI app:**

   ```sh
   uv venv exec uvicorn main:app --reload
   ```

All dependencies and execution are handled by `uv`—no need for pip or venv!