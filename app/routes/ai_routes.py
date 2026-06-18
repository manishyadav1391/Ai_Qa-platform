from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.database.models import (
    Page,
    Element,
    TestCase
)

from app.services.ai_service import (
    generate_ai_testcases
)

router = APIRouter(
    prefix="/ai",
    tags=["AI Test Generation"]
)

@router.post("/generate/{page_id}")
def generate_ai_tests(
    page_id: int,
    db: Session = Depends(get_db)
):

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

    existing_tests = (
        db.query(TestCase)
        .filter(TestCase.page_id == page_id)
        .all()
    )

    element_data = []

    for e in elements:
        # Skip hidden and non-testable elements
        if e.visible == "false":
            continue
        if e.input_type in ("hidden", "submit", "reset", "image"):
            continue

        element_data.append({
            "tag": e.tag_name or e.element_type,
            "type": e.element_type,
            "name": e.name,
            "id": e.element_id or "",
            "input_type": e.input_type or "",
            "text": e.text,
            "placeholder": e.placeholder or "",
            "href": e.href or "",
            "required": e.required or "false",
        })

    existing_titles = [
        tc.title
        for tc in existing_tests
    ]
  

    ai_cases = generate_ai_testcases(
        page.title,
        element_data,
        existing_titles
    )

    saved = 0

    for tc in ai_cases:

        testcase = TestCase(
            page_id=page_id,
            title=tc["title"],
            category=tc["category"],
            priority=tc["priority"],
            expected_result=tc["expected_result"],
            source="ai",
            generated_by="gpt-oss:120b"
        )

        db.add(testcase)
        saved += 1

    db.commit()

    return {
        "saved": saved
    }