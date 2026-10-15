"""
VidyaMarksheet Backend Application
FastAPI Server compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Developed at VidyaLabs. Copyright © 2026 VidyaLabs.
"""

import sys
import asyncio

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.upload import router as upload_router
from backend.routes.schemas_route import router as schemas_router, INSTITUTIONAL_METADATA
from backend.routes.grading_route import router as grading_router
from backend.routes.exam_cell_route import router as exam_cell_router
from backend.routes.evaluation_route import router as evaluation_router
from backend.routes.audit_route import router as audit_router
from backend.routes.pdf_route import router as pdf_router
from backend.routes.examination_db_route import router as examination_db_router
from backend.routes.tabulation_register_route import router as tabulation_register_router
from backend.routes.workflow_route import router as workflow_router
from backend.db.init_db import init_database, seed_courses

app = FastAPI(
    title="VidyaMarksheet API",
    description=(
        "Institution-Grade B.Sc. Nursing Marksheet Generation & Evaluation System "
        "compliant with Indian Nursing Council (INC) Gazette and SGPGIMS Lucknow regulations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Next.js frontend (standard ports 3000, 3001, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload_router)
app.include_router(schemas_router)
app.include_router(grading_router)
app.include_router(exam_cell_router)
app.include_router(evaluation_router)
app.include_router(audit_router)
app.include_router(pdf_router)
app.include_router(examination_db_router)
app.include_router(tabulation_register_router)
app.include_router(workflow_router)


@app.on_event("startup")
def on_startup():
    try:
        init_database()
        seed_courses()
    except Exception as e:
        print(f"Warning: Database startup initialization failed: {e}")


@app.get("/")
def root():
    return {
        "status": "online",
        "system": "VidyaMarksheet API",
        "regulations": "INC Gazette & SGPGIMS Lucknow",
        "attribution": INSTITUTIONAL_METADATA["branding"],
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform": "VidyaMarksheet",
        "institution": INSTITUTIONAL_METADATA["institution_name"],
        "footer_attribution": "Developed at VidyaLabs | Copyright © 2026 VidyaLabs. All Rights Reserved. | Contact: Priyanka Kumari (+91-9140189586)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
