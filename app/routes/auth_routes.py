"""
Auth routes — Browser Session Capture (Approach B)

Flow:
1. POST /auth/{project_id}/start-session   → Launch visible browser, user logs in manually
2. POST /auth/{project_id}/capture-session  → Extract cookies + localStorage after login
3. GET  /auth/{project_id}/status           → Check if session is active/expired
4. DELETE /auth/{project_id}/clear          → Remove stored session

Threading model:
- The browser thread stays alive (waiting on an Event) so all Playwright
  operations happen on the same thread that created them.
- capture-session signals the thread → thread captures state → thread sends result back.
"""

import json
import datetime
import threading

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Project, AuthConfig

from playwright.sync_api import sync_playwright

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ── In-memory registry of active login browser sessions ──────────
# Maps project_id → {
#   "capture_event": Event,   — set by API to tell thread to capture
#   "close_event": Event,     — set by API to tell thread to close browser
#   "result_event": Event,    — set by thread when result is ready
#   "result": dict,           — the captured storage_state (or error)
#   "login_url": str,
#   "started_at": datetime,
#   "thread": Thread,
# }
active_login_sessions: dict[int, dict] = {}


def _launch_login_browser(project_id: int, login_url: str):
    """
    Launch a visible browser and STAY ALIVE waiting for signals.

    This runs in a background thread. The thread does NOT exit after
    navigating — it waits for either:
      - capture_event (capture session state, then close)
      - close_event   (just close, no capture)
    """
    session = active_login_sessions.get(project_id)
    if not session:
        return

    pw = None
    browser = None

    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass  # Page loaded enough for the user to interact

        # Mark browser as ready
        session["browser_ready"] = True

        # ── Block here: wait for either capture or close signal ──
        while True:
            # Check capture signal
            if session["capture_event"].wait(timeout=0.5):
                break
            # Check close signal
            if session["close_event"].is_set():
                session["result"] = {"success": False, "error": "Browser closed without capture"}
                session["result_event"].set()
                return

        # ── Capture session state (same thread that created the context!) ──
        try:
            storage_state = context.storage_state()
            session["result"] = {
                "success": True,
                "storage_state": storage_state,
                "landing_url": page.url,
            }
        except Exception as e:
            session["result"] = {
                "success": False,
                "error": f"Capture failed: {str(e)}",
            }

        session["result_event"].set()

    except Exception as e:
        if session:
            session["result"] = {"success": False, "error": str(e)}
            session["result_event"].set()

    finally:
        # Clean up browser
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if pw:
                pw.stop()
        except Exception:
            pass


@router.post("/{project_id}/start-session")
def start_login_session(
    project_id: int,
    login_url: str = None,
    db: Session = Depends(get_db)
):
    """
    Launch a visible browser for the user to log in manually.
    The browser stays open until the user calls /capture-session.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}

    # If there's already an active session browser, close it first
    if project_id in active_login_sessions:
        old_session = active_login_sessions.pop(project_id)
        old_session["close_event"].set()
        # Give the old thread a moment to clean up
        old_thread = old_session.get("thread")
        if old_thread:
            old_thread.join(timeout=3)

    # Use provided login_url, or fall back to project URL
    url = login_url or project.url

    # Set up the session entry with synchronization primitives
    session_entry = {
        "capture_event": threading.Event(),
        "close_event": threading.Event(),
        "result_event": threading.Event(),
        "result": None,
        "browser_ready": False,
        "login_url": url,
        "started_at": datetime.datetime.now(datetime.timezone.utc),
    }
    active_login_sessions[project_id] = session_entry

    # Launch browser thread (stays alive until capture or close)
    thread = threading.Thread(
        target=_launch_login_browser,
        args=(project_id, url),
        daemon=True,
    )
    session_entry["thread"] = thread
    thread.start()

    # Wait for browser to be ready (up to 10 seconds)
    import time
    for _ in range(20):
        if session_entry.get("browser_ready"):
            break
        time.sleep(0.5)

    return {
        "message": "Login browser launched. Please log in manually, then click Capture Session.",
        "project_id": project_id,
        "login_url": url,
        "status": "browser_open"
    }


@router.post("/{project_id}/capture-session")
def capture_session(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Capture the current browser session (cookies + localStorage)
    after the user has logged in manually.

    Signals the browser thread to capture state (on the correct thread),
    then waits for the result.
    """
    if project_id not in active_login_sessions:
        return {
            "error": "No active login browser for this project. Call /start-session first."
        }

    session = active_login_sessions[project_id]

    # Signal the browser thread to capture
    session["capture_event"].set()

    # Wait for the result (up to 15 seconds)
    got_result = session["result_event"].wait(timeout=15)

    if not got_result:
        active_login_sessions.pop(project_id, None)
        return {"error": "Capture timed out. The browser may have been closed."}

    result = session["result"]
    login_url = session["login_url"]

    # Clean up from registry
    active_login_sessions.pop(project_id, None)

    if not result or not result.get("success"):
        error_msg = result.get("error", "Unknown error") if result else "No result"
        return {"error": f"Failed to capture session: {error_msg}"}

    # ── Save to database ──
    storage_state = result["storage_state"]
    landing_url = result.get("landing_url")
    session_json = json.dumps(storage_state)

    auth_config = (
        db.query(AuthConfig)
        .filter(AuthConfig.project_id == project_id)
        .first()
    )

    if auth_config:
        auth_config.session_state = session_json
        auth_config.status = "active"
        auth_config.captured_at = datetime.datetime.now(datetime.timezone.utc)
        auth_config.login_url = login_url
        auth_config.landing_url = landing_url
    else:
        auth_config = AuthConfig(
            project_id=project_id,
            status="active",
            session_state=session_json,
            captured_at=datetime.datetime.now(datetime.timezone.utc),
            login_url=login_url,
            landing_url=landing_url,
        )
        db.add(auth_config)

    db.commit()

    # Count what we captured
    cookie_count = len(storage_state.get("cookies", []))
    origin_count = len(storage_state.get("origins", []))

    return {
        "message": "Session captured successfully!",
        "project_id": project_id,
        "cookies_captured": cookie_count,
        "origins_captured": origin_count,
        "captured_at": auth_config.captured_at.isoformat(),
        "landing_url": auth_config.landing_url,
        "status": "active"
    }


@router.get("/{project_id}/status")
def get_auth_status(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a project has an active auth session.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}

    auth_config = (
        db.query(AuthConfig)
        .filter(AuthConfig.project_id == project_id)
        .first()
    )

    browser_open = project_id in active_login_sessions

    if not auth_config:
        return {
            "project_id": project_id,
            "auth_status": "none",
            "has_session": False,
            "browser_open": browser_open,
            "captured_at": None,
            "login_url": None,
        }

    # Parse session to get cookie count
    cookie_count = 0
    if auth_config.session_state:
        try:
            state = json.loads(auth_config.session_state)
            cookie_count = len(state.get("cookies", []))
        except Exception:
            pass

    return {
        "project_id": project_id,
        "auth_status": auth_config.status,
        "has_session": auth_config.session_state is not None,
        "browser_open": browser_open,
        "captured_at": auth_config.captured_at.isoformat() if auth_config.captured_at else None,
        "login_url": auth_config.login_url,
        "landing_url": auth_config.landing_url,
        "cookie_count": cookie_count,
    }


@router.delete("/{project_id}/clear")
def clear_auth(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove stored auth session for a project.
    """
    auth_config = (
        db.query(AuthConfig)
        .filter(AuthConfig.project_id == project_id)
        .first()
    )

    if auth_config:
        auth_config.session_state = None
        auth_config.status = "none"
        auth_config.captured_at = None
        auth_config.login_url = None
        db.commit()

    # Also close any open login browser
    if project_id in active_login_sessions:
        session = active_login_sessions.pop(project_id)
        session["close_event"].set()
        thread = session.get("thread")
        if thread:
            thread.join(timeout=3)

    return {
        "message": "Auth session cleared",
        "project_id": project_id,
        "status": "none"
    }
