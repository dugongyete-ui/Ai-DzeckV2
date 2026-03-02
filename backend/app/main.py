from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.interfaces.dependencies import get_agent_service
from app.interfaces.api.routes import router
from app.infrastructure.logging import setup_logging
from app.interfaces.errors.exception_handlers import register_exception_handlers
from app.infrastructure.models.documents import AgentDocument, SessionDocument, UserDocument
from beanie import init_beanie

# Initialize logging system
setup_logging()
logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()


async def _seed_admin_user():
    """Seed the admin user in MongoDB if not already present (password auth mode)."""
    if settings.auth_provider != "password":
        return
    
    if not settings.local_auth_email or not settings.local_auth_password:
        return
    
    try:
        from app.infrastructure.repositories.user_repository import MongoUserRepository
        from app.application.services.auth_service import AuthService
        from app.application.services.token_service import TokenService
        from app.domain.models.user import UserRole
        
        token_service = TokenService()
        user_repo = MongoUserRepository()
        auth_service = AuthService(user_repo, token_service)
        
        existing = await user_repo.get_user_by_email(settings.local_auth_email)
        if not existing:
            logger.info(f"Seeding admin user: {settings.local_auth_email}")
            await auth_service.register_user(
                fullname="Admin",
                password=settings.local_auth_password,
                email=settings.local_auth_email,
                role=UserRole.ADMIN
            )
            logger.info("Admin user seeded successfully")
        else:
            logger.info(f"Admin user already exists: {settings.local_auth_email}")
    except Exception as e:
        logger.warning(f"Admin user seeding skipped: {e}")


# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup
    logger.info("Application startup - Dzeck AI Agent initializing")
    
    # Initialize MongoDB and Beanie
    await get_mongodb().initialize()

    # Initialize Beanie
    await init_beanie(
        database=get_mongodb().client[settings.mongodb_database],
        document_models=[AgentDocument, SessionDocument, UserDocument]
    )
    logger.info("Successfully initialized Beanie")
    
    # Initialize Redis
    await get_redis().initialize()
    
    # Seed admin user if needed
    await _seed_admin_user()
    
    try:
        yield
    finally:
        # Code executed on shutdown
        logger.info("Application shutdown - Dzeck AI Agent terminating")
        # Disconnect from MongoDB
        await get_mongodb().shutdown()
        # Disconnect from Redis
        await get_redis().shutdown()


        logger.info("Cleaning up AgentService instance")
        try:
            await asyncio.wait_for(get_agent_service().shutdown(), timeout=30.0)
            logger.info("AgentService shutdown completed successfully")
        except asyncio.TimeoutError:
            logger.warning("AgentService shutdown timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error during AgentService cleanup: {str(e)}")

app = FastAPI(title="Dzeck AI Agent", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routes
app.include_router(router, prefix="/api/v1")

# Register Inngest endpoint (if configured)
try:
    from app.infrastructure.external.inngest_setup import setup_inngest
    setup_inngest(app)
except Exception as _inngest_err:
    logger.warning(f"Inngest setup skipped: {_inngest_err}")
