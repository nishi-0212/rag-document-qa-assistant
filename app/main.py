from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
import shutil

app = FastAPI(
    title="RAG Document QA API",
    version="1.0"
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
    try:
        from app.rag_pipeline import build_database

        uploaded_files = []

        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                continue

            file_path = DATA_DIR / file.filename

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append(file.filename)

        if not uploaded_files:
            return {"error": "No valid PDF files uploaded"}

        build_result = build_database()

        return {
            "message": "Files uploaded and database rebuilt successfully",
            "uploaded_files": uploaded_files,
            "build_details": build_result
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/query")
def query_documents(request: QueryRequest):
    from app.rag_pipeline import ask_question

    try:
        return ask_question(request.question)
    except Exception as e:
        return {"error": str(e)}