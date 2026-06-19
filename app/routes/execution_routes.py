from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import (
    AutomationScript,
    TestExecution
)

from app.services.execution_service import execute_script

router = APIRouter(
    prefix="/execution",
    tags=["Execution"]
)


@router.post("/run/{page_id}")
def run_page_test(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Execute latest script for a page
    """
    from app.database.models import Page, AuthConfig
    import json
    import os

    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        return {
            "success": False,
            "message": "Page not found"
        }

    script = (
        db.query(AutomationScript)
        .filter(
            AutomationScript.page_id == page_id
        )
        .order_by(
            AutomationScript.id.desc()
        )
        .first()
    )

    if not script:
        return {
            "success": False,
            "message": "No script found for this page"
        }

    # Write session state to file before executing if active session exists
    auth_config = (
        db.query(AuthConfig)
        .filter(AuthConfig.project_id == page.project_id)
        .filter(AuthConfig.status == "active")
        .first()
    )
    if auth_config and auth_config.session_state:
        os.makedirs("generated_scripts", exist_ok=True)
        session_path = os.path.join("generated_scripts", f"auth_state_{page.project_id}.json")
        try:
            state_data = json.loads(auth_config.session_state)
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Error saving auth state for execution: {e}")

    started_at = datetime.utcnow()

    result = execute_script(
        script.script_path
    )

    completed_at = datetime.utcnow()

    status = (
        "PASS"
        if result.get("returncode") == 0
        else "FAIL"
    )

    execution = TestExecution(
        page_id=page_id,
        script_id=script.id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        duration=result["duration"],
        error_message=result["stderr"],
        execution_log=result["stdout"]
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return {
        "execution_id": execution.id,
        "page_id": page_id,
        "status": status,
        "duration": round(result["duration"], 2),
        "error": result["stderr"]
    }


@router.get("/history/{page_id}")
def get_execution_history(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all executions for a page
    """

    executions = (
        db.query(TestExecution)
        .filter(
            TestExecution.page_id == page_id
        )
        .order_by(
            TestExecution.id.desc()
        )
        .all()
    )

    return [
        {
            "execution_id": e.id,
            "status": e.status,
            "duration": e.duration,
            "started_at": e.started_at,
            "completed_at": e.completed_at
        }
        for e in executions
    ]


@router.get("/{execution_id}")
def get_execution_result(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """
    Get execution details
    """

    execution = (
        db.query(TestExecution)
        .filter(
            TestExecution.id == execution_id
        )
        .first()
    )

    if not execution:
        return {
            "success": False,
            "message": "Execution not found"
        }

    return {
        "execution_id": execution.id,
        "page_id": execution.page_id,
        "script_id": execution.script_id,
        "status": execution.status,
        "duration": execution.duration,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "error_message": execution.error_message,
        "execution_log": execution.execution_log,
        "screenshot_path": execution.screenshot_path
    }


@router.get("/report/{page_id}")
def get_page_report(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a full report for a page (for download)
    """
    from app.database.models import Page, Element, TestCase

    page = (
        db.query(Page)
        .filter(Page.id == page_id)
        .first()
    )

    if not page:
        return {"error": "Page not found"}

    elements = (
        db.query(Element)
        .filter(Element.page_id == page_id)
        .all()
    )

    testcases = (
        db.query(TestCase)
        .filter(TestCase.page_id == page_id)
        .all()
    )

    scripts = (
        db.query(AutomationScript)
        .filter(AutomationScript.page_id == page_id)
        .order_by(AutomationScript.version.desc())
        .all()
    )

    executions = (
        db.query(TestExecution)
        .filter(TestExecution.page_id == page_id)
        .order_by(TestExecution.id.desc())
        .all()
    )

    passed = sum(1 for e in executions if e.status == "PASS")
    failed = sum(1 for e in executions if e.status == "FAIL")

    return {
        "report_title": f"QA Report — {page.title}",
        "generated_at": datetime.utcnow().isoformat(),
        "page": {
            "id": page.id,
            "title": page.title,
            "url": page.url,
            "status_code": page.status_code,
        },
        "summary": {
            "total_elements": len(elements),
            "total_testcases": len(testcases),
            "total_scripts": len(scripts),
            "total_executions": len(executions),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{round(passed / len(executions) * 100)}%" if executions else "N/A",
        },
        "testcases": [
            {
                "id": tc.id,
                "title": tc.title,
                "category": tc.category,
                "priority": tc.priority,
                "expected_result": tc.expected_result,
                "source": tc.source,
            }
            for tc in testcases
        ],
        "scripts": [
            {
                "id": s.id,
                "script_name": s.script_name,
                "framework": s.framework,
                "generation_type": s.generation_type,
                "version": s.version,
            }
            for s in scripts
        ],
        "executions": [
            {
                "id": ex.id,
                "status": ex.status,
                "duration": ex.duration,
                "started_at": str(ex.started_at) if ex.started_at else None,
                "completed_at": str(ex.completed_at) if ex.completed_at else None,
                "error_message": ex.error_message,
                "execution_log": ex.execution_log,
            }
            for ex in executions
        ],
    }