from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class GenerateMcqRequest(BaseModel):
    educational_text: str = Field(..., min_length=1, description="Source material for MCQs")


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    is_correct: bool = Field(..., description="True if the learner answered correctly")


class SubmitAnswerResponse(BaseModel):
    user_id: str
    question_id: str
    is_correct: bool
    difficulty: int = Field(..., ge=1, le=10, description="Updated adaptive difficulty (1-10)")


class McqItem(BaseModel):
    question: str
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str
    explanation: str


class McqItemWithId(McqItem):
    question_id: str


class GenerateMcqResponse(BaseModel):
    user_id: str
    difficulty: int = Field(..., ge=1, le=10, description="Adaptive difficulty used for generation")
    questions: list[McqItemWithId]


class UploadDocumentResponse(GenerateMcqResponse):
    source_filename: str
    extracted_char_count: int
    total_chunks: int
    chunk_index_used: int
    used_char_count: int
    extracted_text_preview: str


class RecentEvaluation(BaseModel):
    question_id: str
    relevance: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    user_was_correct: bool
    question_preview: str


class InsightAnalyticsResponse(BaseModel):
    total_evaluations: int
    avg_relevance: float
    avg_clarity: float
    avg_overall: float
    recent_evaluations: list[RecentEvaluation]
