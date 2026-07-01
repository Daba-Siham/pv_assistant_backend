from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
from datetime import datetime

from app.api.router import api_router
from app.config import settings
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 - ensure SQLAlchemy models are registered

from app.services.calculation.calculation_service import calculate_system
from app.services.agent.agent_engine import process_chat
from app.services.llm.llm_service import LLMService
from app.schemas.chat import ChatRequest, SaveChatMessageInput
from app.schemas.monitoring import MonitoringSimulationRequest
from app.services.monitoring.simulation_service import SimulationService
from pdf.generator import generate_pdf_report
from app.dependencies import AuthToken, get_db
from app.core.security import get_user_id_from_token
from app.models.user import User
from sqlalchemy.orm import Session


# =========================================
# SCHEMAS
# =========================================

class SolarInput(BaseModel):
    city: str
    daily_consumption_kwh: float
    available_area_m2: float
    budget: float
    orientation: str
    installation_type: str
    autonomy_days: int
    shade_factor: float
    roof_type: str
    distance_to_load_m: float

class ChatInput(BaseModel):
    question: str
    session_id: str | None = None
    user_id: int | None = None
    context: dict | None = None


def _resolve_client_name(db: Session, token: str | None) -> str:
    fallback = "Client non renseigné"
    if token is None:
        return fallback

    user_id = get_user_id_from_token(token)
    if user_id is None:
        return fallback

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return fallback

    full_name = str(getattr(user, "full_name", "") or "").strip()
    if full_name:
        return full_name

    name = str(getattr(user, "name", "") or "").strip()
    if name:
        return name

    email = str(getattr(user, "email", "") or "").strip()
    if email:
        return email

    return fallback


# =========================================
# APP
# =========================================

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # =========================================
    # MIDDLEWARES
    # =========================================

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Report-Pdf-Path",
            "X-Report-Pdf-Filename",
            "Content-Disposition",
        ],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # =========================================
    # ROUTERS (auth, monitoring, etc.)
    # =========================================

    app.include_router(api_router, prefix=settings.API_PREFIX)

    @app.on_event("startup")
    def ensure_database_tables():
        Base.metadata.create_all(bind=engine)

    # =========================================
    # ROOT
    # =========================================

    @app.get("/")
    def root():
        return {
            "message": "Bienvenue dans l'API PV Intelligent Assistant",
            "version": settings.PROJECT_VERSION,
            "docs": "/docs",
            "status": "running"
        }

    @app.get("/health")
    def health_check():
        return {
            "status": "ok",
            "project": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT
        }

    # =========================================
    # CALCUL SOLAIRE
    # =========================================

    @app.post("/calculate")
    def calculate(data: SolarInput):
        return calculate_system(data)

    # =========================================
    # CHAT
    # =========================================

    @app.post("/chat")
    def chat(data: ChatInput, token: AuthToken, db: Session = Depends(get_db)):
        llm_service = LLMService(db=db)
        return llm_service.generate_response(
            request=ChatRequest(
                message=data.question,
                question=data.question,
                session_id=data.session_id,
                user_id=data.user_id,
                context=data.context,
            ),
            token=token,
        )

    @app.get("/chat/sessions")
    def get_chat_sessions(token: AuthToken, db: Session = Depends(get_db)):
        return LLMService(db=db).get_chat_sessions(token=token)

    @app.get("/chat/sessions/{session_id}/messages")
    def get_chat_session_messages(session_id: str, token: AuthToken, db: Session = Depends(get_db)):
        return LLMService(db=db).get_chat_session_messages(token=token, session_id=session_id)

    @app.delete("/chat/sessions/{session_id}")
    def delete_chat_session(session_id: str, token: AuthToken, db: Session = Depends(get_db)):
        return LLMService(db=db).delete_chat_session(token=token, session_id=session_id)

    @app.delete("/chat/sessions")
    def delete_all_chat_sessions(token: AuthToken, db: Session = Depends(get_db)):
        return LLMService(db=db).delete_all_chat_sessions(token=token)

    @app.get("/chat/history")
    def get_chat_history(
        token: AuthToken,
        db: Session = Depends(get_db),
        session_id: str | None = None,
        limit: int = 50,
    ):
        return LLMService(db=db).get_chat_history(token=token, session_id=session_id, limit=limit)

    @app.post("/chat/messages")
    def save_chat_message(data: SaveChatMessageInput, token: AuthToken, db: Session = Depends(get_db)):
        return LLMService(db=db).save_chat_message(
            token=token,
            session_id=data.session_id,
            role=data.role,
            content=data.content,
            context=data.context,
        )

    @app.delete("/chat/history")
    def clear_chat_history(token: AuthToken, db: Session = Depends(get_db), session_id: str | None = None):
        return LLMService(db=db).clear_chat_history(token=token, session_id=session_id)

    # =========================================
    # PDF
    # =========================================

    @app.post("/generate-pdf")
    def generate_pdf(data: SolarInput, token: AuthToken, db: Session = Depends(get_db)):
        try:
            result = calculate_system(data)
            os.makedirs("generated_reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"rapport_solaire_{timestamp}.pdf"
            pdf_path = os.path.join("generated_reports", pdf_filename)
            client_name = _resolve_client_name(db, token)
            generate_pdf_report(
                filename=pdf_path,
                user_data=data.model_dump(),
                results=result,
                client_name=client_name,
            )
            return {
                "message": "PDF generated successfully",
                "pdf_url": f"/download-pdf/{pdf_filename}"
            }
        except Exception as e:
            return {"error": str(e)}

    @app.get("/download-pdf/{file_name}")
    def download_pdf(file_name: str):
        pdf_path = os.path.join("generated_reports", file_name)
        if not os.path.exists(pdf_path):
            return {"error": "File not found"}
        return FileResponse(path=pdf_path, media_type="application/pdf")

    # =========================================
    # MONITORING
    # =========================================

    @app.post("/monitoring/simulate")
    def simulate_monitoring(data: MonitoringSimulationRequest):
        return SimulationService().simulate(data)

    # =========================================
    # EXCEPTION HANDLERS
    # =========================================

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Une erreur interne est survenue"
                }
            }
        )

    return app


app = create_application()
