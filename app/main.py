from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
import shutil
from fastapi.middleware.cors import CORSMiddleware

from app.rag_pipeline import build_database, ask_question


app = FastAPI(
    title="RAG Document QA API",
    version="1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # okay for demo project
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data/docs")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class QueryRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {"message": "RAG API is running"}


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    uploaded_files = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            continue

        file_path = DATA_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_files.append(file.filename)

    build_result = build_database()

    return {
        "message": "Files uploaded and database rebuilt successfully",
        "uploaded_files": uploaded_files,
        "build_details": build_result
    }


@app.post("/query")
def query_documents(request: QueryRequest):
    return ask_question(request.question)