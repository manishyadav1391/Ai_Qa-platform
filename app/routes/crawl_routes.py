import datetime
from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Project, Page, Element, PageLink, CrawlRun, PageFeature

from app.crawler.crawler import scan_page
from app.crawler.site_crawler import crawl_site

router = APIRouter(
    prefix="/crawl",
    tags=["Crawler"]
)

@router.post("/{project_id}")
def crawl_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        return {
            "error": "Project not found"
        }

    # Create a versioned CrawlRun
    crawl_run = CrawlRun(
        project_id=project.id,
        started_at=datetime.datetime.now(datetime.timezone.utc),
        status="running"
    )
    db.add(crawl_run)
    db.flush()

    try:
        result = scan_page(
            project.url
        )

        new_page = Page(
            title=result["title"],
            url=result["url"],
            status_code=result["status_code"],
            crawl_date=datetime.datetime.now(datetime.timezone.utc),
            depth=0,
            project_id=project.id,
            crawl_run_id=crawl_run.id
        )

        db.add(new_page)
        db.flush()

        for item in result["elements"]:
            element = Element(
                page_id=new_page.id,
                element_type=item["type"],
                name=item["name"],
                locator=item["locator"],
                text=item["text"],
                placeholder=item.get("placeholder", ""),
                required=item.get("required", "false")
            )
            db.add(element)

        for link in result["links"]:
            db.add(
                PageLink(
                    from_page_id=new_page.id,
                    to_url=link
                )
            )

        for feature_type, feature_val in result.get("features", {}).items():
            db.add(
                PageFeature(
                    page_id=new_page.id,
                    feature_type=feature_type,
                    feature_value=str(feature_val)
                )
            )

        crawl_run.status = "completed"
        db.commit()
        db.refresh(new_page)

        return {
            "message": "Page saved",
            "crawl_run_id": crawl_run.id,
            "page_id": new_page.id,
            "title": new_page.title
        }
    except Exception as e:
        crawl_run.status = "failed"
        db.commit()
        raise e


@router.post("/test-recursive/{project_id}")
def test_recursive(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        return {
            "error": "Project not found"
        }

    # Create a versioned CrawlRun
    crawl_run = CrawlRun(
        project_id=project.id,
        started_at=datetime.datetime.now(datetime.timezone.utc),
        status="running"
    )
    db.add(crawl_run)
    db.flush()

    try:
        results = crawl_site(
            project.url,
            max_depth=2
        )

        url_to_page = {}
        saved_pages = []

        # First pass: Create Page entries
        for page_data in results:
            new_page = Page(
                title=page_data["title"],
                url=page_data["url"],
                status_code=page_data["status_code"],
                crawl_date=datetime.datetime.now(datetime.timezone.utc),
                depth=page_data["depth"],
                project_id=project.id,
                crawl_run_id=crawl_run.id
            )
            db.add(new_page)
            db.flush()
            url_to_page[page_data["url"]] = new_page

        # Second pass: Update parent_id, elements, page links, and features
        for page_data in results:
            new_page = url_to_page[page_data["url"]]
            
            parent_url = page_data.get("parent_url")
            if parent_url and parent_url in url_to_page:
                new_page.parent_id = url_to_page[parent_url].id

            for item in page_data["elements"]:
                element = Element(
                    page_id=new_page.id,
                    element_type=item["type"],
                    name=item["name"],
                    locator=item["locator"],
                    text=item["text"],
                    placeholder=item.get("placeholder", ""),
                    required=item.get("required", "false")
                )
                db.add(element)

            for link in page_data["links"]:
                db.add(
                    PageLink(
                        from_page_id=new_page.id,
                        to_url=link
                    )
                )

            for feature_type, feature_val in page_data.get("features", {}).items():
                db.add(
                    PageFeature(
                        page_id=new_page.id,
                        feature_type=feature_type,
                        feature_value=str(feature_val)
                    )
                )

            saved_pages.append({
                "page_id": new_page.id,
                "title": new_page.title,
                "url": new_page.url,
                "depth": new_page.depth,
                "parent_id": new_page.parent_id
            })

        crawl_run.status = "completed"
        db.commit()

        return {
            "message": "Recursive crawl completed",
            "crawl_run_id": crawl_run.id,
            "pages_found": len(results),
            "saved_pages": saved_pages
        }

    except Exception as e:
        crawl_run.status = "failed"
        db.commit()
        raise e


@router.get("/projects/{project_id}/graph")
def get_project_graph(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        return {"error": "Project not found"}

    crawl_run = (
        db.query(CrawlRun)
        .filter(CrawlRun.project_id == project_id)
        .order_by(CrawlRun.started_at.desc())
        .first()
    )
    if not crawl_run:
        return {"error": "No crawl runs found for this project"}

    pages = (
        db.query(Page)
        .filter(Page.crawl_run_id == crawl_run.id)
        .all()
    )

    page_map = {p.id: p for p in pages}
    
    # Build a map of page_id -> list of child titles
    from collections import defaultdict
    children_map = defaultdict(list)
    for p in pages:
        if p.parent_id and p.parent_id in page_map:
            children_map[p.parent_id].append(p.title)

    graph = []
    for p in pages:
        # Load features
        features_dict = {}
        for feature in p.features:
            try:
                features_dict[feature.feature_type] = int(feature.feature_value)
            except ValueError:
                features_dict[feature.feature_type] = feature.feature_value

        contains_form = features_dict.get("forms", 0) > 0
        contains_table = features_dict.get("tables", 0) > 0

        parent_title = page_map[p.parent_id].title if p.parent_id and p.parent_id in page_map else None

        graph.append({
            "page": p.title,
            "url": p.url,
            "parent": parent_title,
            "children": children_map[p.id],
            "contains_form": contains_form,
            "contains_table": contains_table,
            "features": features_dict
        })

    return {
        "project_id": project_id,
        "project_name": project.name,
        "crawl_run_id": crawl_run.id,
        "started_at": crawl_run.started_at,
        "status": crawl_run.status,
        "graph": graph
    }    