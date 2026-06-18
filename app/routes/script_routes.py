import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import (
    Page,
    Element,
    AutomationScript,
    TestCase
)
from app.generators.playwright_generator import (
    generate_playwright_script
)

router = APIRouter(
    prefix="/scripts",
    tags=["Automation Scripts"]
)


@router.post("/generate/{page_id}")
def generate_script(
    page_id: int,
    db: Session = Depends(get_db)
):

    page = (
        db.query(Page)
        .filter(Page.id == page_id)
        .first()
    )

    if not page:
        return {
            "error": "Page not found"
        }

    elements = (
        db.query(Element)
        .filter(Element.page_id == page_id)
        .all()
    )

    script_content = generate_playwright_script(
        page.title,
        page.url,
        elements
    )

    # Version logic
    latest_script = (
        db.query(AutomationScript)
        .filter(AutomationScript.page_id == page_id)
        .order_by(AutomationScript.version.desc())
        .first()
    )
    new_version = (latest_script.version + 1) if latest_script and latest_script.version else 1

    script_name = f"page_{page.id}_v{new_version}.py"

    # Save to file system
    os.makedirs("generated_scripts", exist_ok=True)
    file_path = os.path.join("generated_scripts", script_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    script = AutomationScript(
        page_id=page.id,
        framework="playwright",
        script_name=script_name,
        script_content=script_content,
        generation_type="template",
        model_name=None,
        version=new_version,
        script_path=file_path
    )

    db.add(script)
    db.commit()
    db.refresh(script)

    return {
        "script_id": script.id,
        "version": script.version,
        "file_name": script_name,
        "message": "Script Generated"
    }


@router.post("/ai-generate/{page_id}")
def generate_ai_script(
    page_id: int,
    db: Session = Depends(get_db)
):
    page = (
        db.query(Page)
        .filter(Page.id == page_id)
        .first()
    )

    if not page:
        return {
            "error": "Page not found"
        }

    elements = (
        db.query(Element)
        .filter(Element.page_id == page_id)
        .all()
    )

    # Convert DB elements to clean payloads — exclude hidden elements
    elements_payload = [
        {
            "tag": e.tag_name or e.element_type,
            "type": e.element_type,
            "name": e.name,
            "id": e.element_id or "",
            "input_type": e.input_type or "",
            "locator": e.locator,
            "text": e.text,
            "placeholder": e.placeholder or "",
            "href": e.href or "",
            "required": e.required or "false",
            "visible": e.visible or "true",
        }
        for e in elements
        if e.visible != "false"  # Don't send hidden elements to AI
    ]

    # Get test cases
    testcases = (
        db.query(TestCase)
        .filter(TestCase.page_id == page_id)
        .all()
    )

    # Convert DB testcases to clean payloads
    testcases_payload = [
        {
            "title": tc.title,
            "category": tc.category,
            "priority": tc.priority,
            "expected_result": tc.expected_result
        }
        for tc in testcases
    ]

    # Generate via AI
    from app.services.ai_playwright_service import generate_playwright_script_via_ai
    
    try:
        script_content = generate_playwright_script_via_ai(
            page.title,
            page.url,
            elements_payload,
            testcases_payload
        )
    except Exception as e:
        return {
            "error": f"AI generation failed: {e}"
        }

    # Version logic
    latest_script = (
        db.query(AutomationScript)
        .filter(AutomationScript.page_id == page_id)
        .order_by(AutomationScript.version.desc())
        .first()
    )
    new_version = (latest_script.version + 1) if latest_script and latest_script.version else 1

    script_name = f"page_{page.id}_v{new_version}.py"
    
    # Save script to file system
    os.makedirs("generated_scripts", exist_ok=True)
    file_path = os.path.join("generated_scripts", script_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # Save to database
    script = AutomationScript(
        page_id=page.id,
        framework="playwright",
        script_name=script_name,
        script_content=script_content,
        generation_type="ai",
        model_name="gpt-oss:120b",
        version=new_version,
        script_path=file_path
    )

    db.add(script)
    db.commit()
    db.refresh(script)

    return {
        "script_id": script.id,
        "version": script.version,
        "model": script.model_name,
        "file_name": script_name,
        "message": "AI Script Generated"
    }


@router.get("/{page_id}")
def get_script(
    page_id: int,
    db: Session = Depends(get_db)
):

    script = (
        db.query(AutomationScript)
        .filter(
            AutomationScript.page_id == page_id
        )
        .order_by(AutomationScript.version.desc())
        .first()
    )

    if not script:
        return {
            "error": "Script not found"
        }

    return {
        "script_id": script.id,
        "version": script.version,
        "script_name": script.script_name,
        "generation_type": script.generation_type,
        "script": script.script_content
    }