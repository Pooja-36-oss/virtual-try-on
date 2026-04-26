from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api import routes

app = FastAPI(
    title="Virtual Try-On API",
    description="Backend for AI Virtual Try-On application with Indian Ethnic Wear optimization.",
    version="1.0.0"
)

# Configure CORS for iPhone/frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(routes.router, prefix="/api/v1")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "V-TON API is running"}

import os
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
