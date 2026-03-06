"""
API Routes
"""
from app.routes.agents import router as agents_router
from app.routes.jobs import router as jobs_router
from app.routes.platforms import router as platforms_router
from app.routes.auth import router as auth_router
from app.routes.credentials import router as credentials_router
from app.routes.trends import router as trends_router
from app.routes.scripts import router as scripts_router
from app.routes.upload_quotas import router as upload_quotas_router
from app.routes.sim_cards import router as sim_cards_router
from app.routes.platform_accounts import router as platform_accounts_router

__all__ = [
    "agents_router", 
    "jobs_router", 
    "platforms_router", 
    "auth_router", 
    "credentials_router",
    "trends_router",
    "scripts_router",
    "upload_quotas_router",
    "sim_cards_router",
    "platform_accounts_router"
]
