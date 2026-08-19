from fastapi import FastAPI
from contextlib import asynccontextmanager
import database
from ring import router as ring_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
database.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting XCEL Vision backend...")
    yield
    logger.info("Shutting down XCEL Vision backend...")

app = FastAPI(title="XCEL Vision Backend", lifespan=lifespan)

# Note: Explicit CORS configuration is delayed until required by the web frontend
# as per requirements. Ring webhook/auth traffic is server-to-server.

app.include_router(ring_router.router)

@app.get("/")
def read_root():
    return {"status": "XCEL Vision Backend Running"}
