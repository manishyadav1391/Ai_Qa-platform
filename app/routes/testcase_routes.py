from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db

from app.database.models import (
    Page,
    Element,
    TestCase,
    PageFeature
)

from app.generators.testcase_generator import (
    generate_page_testcases,
    generate_feature_testcases
)

router = APIRouter(
    prefix="/testcases",
    tags=["Test Cases"]
)

@router.post("/generate/{page_id}")
def generate_testcases(
    page_id: int,
    db: Session = Depends(get_db)
):

    elements = (
        db.query(Element)
        .filter(Element.page_id == page_id)
        .all()
    )

    features = (
        db.query(PageFeature)
        .filter(PageFeature.page_id == page_id)
        .all()
    )

    generated = generate_page_testcases(
        elements
    )

    generated.extend(
        generate_feature_testcases(features)
    )

    count = 0

    for tc in generated:

        testcase = TestCase(
            page_id=page_id,
            title=tc["title"],
            category=tc["category"],
            priority=tc["priority"],
            expected_result=tc["expected"],
            source="rule-based",
            generated_by="rule_engine"
        )

        db.add(testcase)

        count += 1

    db.commit()

    return {
        "generated": count
    }


@router.get("/{page_id}")
def get_testcases(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all test cases for a page
    """

    testcases = (
        db.query(TestCase)
        .filter(TestCase.page_id == page_id)
        .all()
    )

    return [
        {
            "id": tc.id,
            "title": tc.title,
            "category": tc.category,
            "priority": tc.priority,
            "expected_result": tc.expected_result,
            "source": tc.source,
            "generated_by": tc.generated_by,
        }
        for tc in testcases
    ]