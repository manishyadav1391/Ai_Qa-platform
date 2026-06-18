from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.dependencies import get_db
from app.database.models import (
    Page,
    Element,
    TestCase,
    AutomationScript,
    TestExecution
)

router = APIRouter(
    prefix="/pages",
    tags=["Pages"]
)


@router.get("/detail/{page_id}")
def get_page_detail(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed info for a single page
    """

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

    return {
        "id": page.id,
        "title": page.title,
        "url": page.url,
        "status_code": page.status_code,
        "depth": page.depth,
        "crawl_date": page.crawl_date,
        "elements": [
            {
                "id": e.id,
                "element_type": e.element_type,
                "name": e.name,
                "locator": e.locator,
                "text": e.text,
            }
            for e in elements
        ],
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
                "started_at": ex.started_at,
                "completed_at": ex.completed_at,
            }
            for ex in executions
        ],
    }


@router.get("/{project_id}")
def get_pages_by_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all pages for a project with summary stats
    """

    pages = (
        db.query(Page)
        .filter(Page.project_id == project_id)
        .all()
    )

    result = []

    for page in pages:
        element_count = (
            db.query(func.count(Element.id))
            .filter(Element.page_id == page.id)
            .scalar()
        )

        testcase_count = (
            db.query(func.count(TestCase.id))
            .filter(TestCase.page_id == page.id)
            .scalar()
        )

        script_count = (
            db.query(func.count(AutomationScript.id))
            .filter(AutomationScript.page_id == page.id)
            .scalar()
        )

        execution_count = (
            db.query(func.count(TestExecution.id))
            .filter(TestExecution.page_id == page.id)
            .scalar()
        )

        last_execution = (
            db.query(TestExecution)
            .filter(TestExecution.page_id == page.id)
            .order_by(TestExecution.id.desc())
            .first()
        )

        result.append({
            "id": page.id,
            "title": page.title,
            "url": page.url,
            "status_code": page.status_code,
            "depth": page.depth,
            "crawl_date": page.crawl_date,
            "element_count": element_count,
            "testcase_count": testcase_count,
            "script_count": script_count,
            "execution_count": execution_count,
            "last_execution_status": last_execution.status if last_execution else None,
            "last_execution_date": last_execution.completed_at if last_execution else None,
        })

    return result
