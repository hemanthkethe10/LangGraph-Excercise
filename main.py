import os
from fastapi import FastAPI
from dotenv import load_dotenv
from api.routes import router as api_router

load_dotenv()

app = FastAPI()
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True) 