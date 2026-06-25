from fastapi import APIRouter

from app.api.routes import agent, auth, calculation, chat, monitoring, notifications, recommendation, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chatbot"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(calculation.router, prefix="/calculation", tags=["Calculation"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(recommendation.router, prefix="/recommendation", tags=["PV Recommendation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
# api_router.include_router(solar.router, prefix="/solar", tags=["Solar Data"])
# api_router.include_router(stores.router, prefix="/stores", tags=["Stores"])
