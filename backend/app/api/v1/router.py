from fastapi import APIRouter
from app.api.v1.routes import auth, company, analysis, feedback, report, watchlist

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(report.router, prefix="/report", tags=["report"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
