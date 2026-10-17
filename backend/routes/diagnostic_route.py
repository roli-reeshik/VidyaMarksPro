"""
Admin Diagnostic Suite & Health Checker Route
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with INC Gazette Corrigendum & SGPGIMS Lucknow Regulations.

Endpoints:
- POST /api/v1/admin/run-system-tests: Executes 7-subsystem non-destructive test suite.
- GET  /api/v1/admin/stream-system-tests: Server-Sent Events (SSE) live execution log stream.
"""

import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.db.database import get_sync_session
from backend.services.diagnostic_service import DiagnosticService, DiagnosticReport
from backend.security import (
    require_admin,
    log_security_event,
    get_client_ip,
    decode_access_token,
    get_current_user_from_token,
    AuthenticatedUser,
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Diagnostic & Health Suite"])
diagnostic_service = DiagnosticService()


class DiagnosticPayload(BaseModel):
    verbose: bool = Field(default=True, description="Enable verbose diagnostic logs")
    test_subsystems: Optional[List[str]] = Field(default=None, description="Optional list of specific subsystems to test")


@router.post("/run-system-tests", response_model=DiagnosticReport)
def run_system_tests(
    request: Request,
    payload: Optional[DiagnosticPayload] = None,
    current_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Executes the comprehensive, non-destructive 7-subsystem diagnostic suite:
    1. Database Connectivity & Schema Integrity (all 11 tables + indexes)
    2. INC Regulatory Rules & Math Matrix (151 credit divisor, subcomponents)
    3. Authentication, Password Hashing & RBAC Policy
    4. Excel Ingestion Engine & Openpyxl AutoFilter Monkeypatch
    5. Marksheet Template Compiler & PDF Engine
    6. Backlog Queueing & Reappear Scheduler
    7. Storage Directories & File System Read/Write Readiness
    """
    opts = payload or DiagnosticPayload()
    service = DiagnosticService()
    report = service.run_all_diagnostics(
        verbose=opts.verbose,
        test_subsystems=opts.test_subsystems,
    )

    # Log to security audit trail
    try:
        with get_sync_session() as session:
            client_ip = get_client_ip(request)
            log_security_event(
                session=session,
                username=current_user.username,
                action="SYSTEM_DIAGNOSTIC_RUN",
                ip_address=client_ip,
                user_agent=(
                    f"Verdict: {report.status} | Passed: {report.passed_checks}/{report.total_checks} | "
                    f"Duration: {report.duration_ms}ms"
                ),
            )
    except Exception as e:
        print(f"Notice: Failed to log diagnostic audit: {e}")

    return report


@router.get("/stream-system-tests")
async def stream_system_tests(
    request: Request,
    token: Optional[str] = Query(None, description="Bearer token for EventSource authentication"),
    subsystems: Optional[str] = Query(None, description="Comma-separated list of subsystems"),
):
    """
    Server-Sent Events (SSE) stream providing real-time log output and milestone events
    as each diagnostic check executes on the server.
    """
    # Authenticate token from header, cookie or query parameter
    auth_user = None
    with get_sync_session() as session:
        # Check query token
        resolved_token = token
        if not resolved_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                resolved_token = auth_header[7:].strip()
            elif request.cookies.get("vidya_access_token"):
                resolved_token = request.cookies.get("vidya_access_token")

        if not resolved_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for diagnostic streaming."
            )

        payload = decode_access_token(resolved_token)
        username = payload.get("sub")
        role = payload.get("role", "")
        if not username or role.lower() != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Admin role required for diagnostic streaming."
            )

    selected_subsystems = [s.strip() for s in subsystems.split(",") if s.strip()] if subsystems else None

    async def event_generator():
        log_queue = asyncio.Queue()

        def log_cb(level: str, message: str, timestamp: str):
            log_queue.put_nowait({
                "type": "log",
                "level": level,
                "message": message,
                "timestamp": timestamp,
            })

        # Run diagnostics in executor thread to keep event loop responsive
        loop = asyncio.get_running_loop()
        service = DiagnosticService()

        # Emit initial start event
        yield f"data: {json.dumps({'type': 'start', 'message': 'Diagnostic test suite initialized'})}\n\n"

        task = loop.run_in_executor(
            None,
            service.run_all_diagnostics,
            True,
            selected_subsystems,
            log_cb,
        )

        while not task.done() or not log_queue.empty():
            try:
                # Poll queue with small timeout
                item = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                yield f"data: {json.dumps(item)}\n\n"
            except asyncio.TimeoutError:
                await asyncio.sleep(0.05)

        report: DiagnosticReport = await task
        # Emit complete event with final report
        yield f"data: {json.dumps({'type': 'complete', 'report': report.model_dump()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
