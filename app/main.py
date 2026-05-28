import asyncio
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo
from app.schemas import (
    GenerateMcqRequest,
    GenerateMcqResponse,
    InsightAnalyticsResponse,
    LoginRequest,
    RegisterRequest,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    TokenResponse,
    UploadDocumentResponse,
)
from app.services.adaptive_learning import record_answer
from app.services.auth_service import login_user, register_user
from app.services.mcq_workflow import generate_mcqs_for_user
from app.services.pdf_extractor import PdfExtractionError, extract_text_from_pdf
from app.services.nlp_quality_models import get_quality_models
from app.services.quality_evaluation import evaluate_question_quality
from app.services.question_store import get_insight_analytics, get_question
from app.services.text_chunker import select_text_for_mcq


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await connect_to_mongo(settings.mongodb_uri, settings.mongodb_db_name)

    if settings.preload_nlp_models:
        models = get_quality_models()
        await asyncio.to_thread(models.initialize)

    yield

    if settings.preload_nlp_models:
        get_quality_models().shutdown()
    await close_mongo_connection()


app = FastAPI(
    title="Personalized MCQ Generator",
    description="Generate diagnostic multiple-choice questions from educational text.",
    version="1.0.0",
    lifespan=lifespan,
)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    from app.database import get_database

    try:
        db = get_database()
        await db.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@app.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    return TokenResponse(**await register_user(payload.username, payload.password))


@app.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    return TokenResponse(**await login_user(payload.username, payload.password))


@app.get("/insight-analytics", response_model=InsightAnalyticsResponse)
async def insight_analytics(current_user: CurrentUser = Depends(get_current_user)):
    return InsightAnalyticsResponse(
        **await get_insight_analytics(user_id=current_user.user_id)
    )


@app.post("/generate-mcq", response_model=GenerateMcqResponse)
async def generate_mcq(
    payload: GenerateMcqRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        settings = get_settings()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return await generate_mcqs_for_user(
        current_user.user_id,
        payload.educational_text,
        settings,
    )


@app.post("/upload-document", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        settings = get_settings()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    file_bytes = await file.read()
    try:
        raw_text = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    educational_text, chunk_meta = select_text_for_mcq(raw_text)

    result = await generate_mcqs_for_user(
        current_user.user_id,
        educational_text,
        settings,
    )

    preview = educational_text[:500] + ("…" if len(educational_text) > 500 else "")

    return UploadDocumentResponse(
        **result.model_dump(),
        source_filename=file.filename or "document.pdf",
        extracted_char_count=chunk_meta["extracted_char_count"],
        total_chunks=chunk_meta["total_chunks"],
        chunk_index_used=chunk_meta["chunk_index_used"],
        used_char_count=chunk_meta["used_char_count"],
        extracted_text_preview=preview,
    )


@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    payload: SubmitAnswerRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
    stored = await get_question(payload.question_id)
    if not stored or stored["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="Question not found")

    difficulty = await record_answer(
        user_id=current_user.user_id,
        question_id=payload.question_id,
        is_correct=payload.is_correct,
    )

    background_tasks.add_task(
        evaluate_question_quality,
        payload.question_id,
        current_user.user_id,
        payload.is_correct,
    )

    return SubmitAnswerResponse(
        user_id=current_user.user_id,
        question_id=payload.question_id,
        is_correct=payload.is_correct,
        difficulty=difficulty,
    )
