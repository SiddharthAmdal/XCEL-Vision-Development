from fastapi import FastAPI
from contextlib import asynccontextmanager
import database
from ring import router as ring_router
from api.routers import cameras as cameras_router
from fastapi.middleware.cors import CORSMiddleware
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

# Configure CORS for the frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for MVP dev, can restrict to http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ring_router.router)
app.include_router(cameras_router.router)

@app.get("/")
def read_root():
    return {"status": "XCEL Vision Backend Running"}
