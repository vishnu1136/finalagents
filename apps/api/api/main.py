from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

from api.routes import admin, ingest, search


def create_app() -> FastAPI:
    # Load environment variables from potential locations
    load_dotenv()  # default .env in CWD
    # Look for .env in the apps directory (one level up from api/)
    api_env = Path(__file__).resolve().parent.parent.parent / ".env"
    if api_env.exists():
        load_dotenv(dotenv_path=api_env, override=True)

    app = FastAPI(title="IKB Navigator API", version="0.1.0")

    cors_origin = os.getenv("CORS_ORIGIN", "*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cors_origin] if cors_origin != "*" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(admin.router)
    app.include_router(ingest.router, prefix="/ingest")
    app.include_router(search.router)
    return app


app = create_app()


