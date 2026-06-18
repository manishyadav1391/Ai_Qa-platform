import datetime
import threading
from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Project, Page, Element, PageLink, CrawlRun, PageFeature

from app.crawler.crawler import scan_page
from app.crawler.site_crawler import crawl_site

from app.database.db import SessionLocal

router = APIRouter(
    prefix="/crawl",
    tags=["Crawler"]
)

# ── In-memory registry of active crawls ──────────────────────────
# Maps crawl_run_id → threading.Event (set the event to stop)
active_crawls: dict[int, threading.Event] = {}


def _save_page_results(db: Session, project_id: int, crawl_run_id: int, results: list):
    """Save crawled page results to the database."""
    url_to_page = {}

    # First pass: Create Page entries
    for page_data in results:
        new_page = Page(
            title=page_data["title"],
            url=page_data["url"],
            status_code=page_data["status_code"],
            crawl_date=datetime.datetime.now(datetime.timezone.utc),
            depth=page_data["depth"],
            project_id=project_id,
            crawl_run_id=crawl_run_id
        )
        db.add(new_page)
        db.flush()
        url_to_page[page_data["url"]] = new_page

    # Second pass: elements, links, features, parent_id
    for page_data in results:
        new_page = url_to_page[page_data["url"]]

        parent_url = page_data.get("parent_url")
        if parent_url and parent_url in url_to_page:
            new_page.parent_id = url_to_page[parent_url].id

        for item in page_data["elements"]:
            element = Element(
                page_id=new_page.id,
                element_type=item["type"],
                tag_name=item.get("tag", ""),
                name=item["name"],
                locator=item.get("locator", ""),
                element_id=item.get("element_id", ""),
                text=item.get("text", ""),
                placeholder=item.get("placeholder", ""),
                input_type=item.get("input_type", ""),
                href=item.get("href", ""),
                visible=item.get("visible", "true"),
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

    db.commit()
    return url_to_page


# ── Single page crawl (synchronous, unchanged behavior) ─────────

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
        status="running",
        pages_found=0,
        max_pages=1
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
                tag_name=item.get("tag", ""),
                name=item["name"],
                locator=item.get("locator", ""),
                element_id=item.get("element_id", ""),
                text=item.get("text", ""),
                placeholder=item.get("placeholder", ""),
                input_type=item.get("input_type", ""),
                href=item.get("href", ""),
                visible=item.get("visible", "true"),
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
        crawl_run.pages_found = 1
        crawl_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
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
        crawl_run.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        raise e


# ── Recursive crawl (background thread) ─────────────────────────

def _run_recursive_crawl(
    project_id: int,
    project_url: str,
    crawl_run_id: int,
    max_pages: int,
    stop_event: threading.Event,
):
    """Background worker for recursive crawling."""
    db = SessionLocal()

    try:
        def on_progress(pages_crawled, current_url):
            """Update crawl_run progress in DB."""
            try:
                run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
                if run:
                    run.pages_found = pages_crawled
                    run.current_url = current_url
                    db.commit()
            except Exception:
                db.rollback()

        results = crawl_site(
            project_url,
            max_depth=2,
            max_pages=max_pages,
            page_timeout=30000,
            stop_event=stop_event,
            on_progress=on_progress,
        )

        # Save all crawled pages to DB
        _save_page_results(db, project_id, crawl_run_id, results)

        # Update final status
        run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
        if run:
            was_stopped = stop_event.is_set()
            run.status = "stopped" if was_stopped else "completed"
            run.pages_found = len(results)
            run.current_url = None
            run.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

    except Exception as e:
        try:
            run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
            if run:
                run.status = "failed"
                run.current_url = None
                run.completed_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
        except Exception:
            db.rollback()
        print(f"Crawl error: {e}")

    finally:
        # Clean up active crawl registry
        active_crawls.pop(crawl_run_id, None)
        db.close()


@router.post("/test-recursive/{project_id}")
def test_recursive(
    project_id: int,
    max_pages: int = 50,
    db: Session = Depends(get_db)
):
    """
    Start a recursive crawl in the background.
    Returns immediately with crawl_run_id for polling.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        return {
            "error": "Project not found"
        }

    # Check if there's already an active crawl for this project
    for run_id, event in active_crawls.items():
        if not event.is_set():
            run = db.query(CrawlRun).filter(CrawlRun.id == run_id).first()
            if run and run.project_id == project_id and run.status == "running":
                return {
                    "error": "A crawl is already running for this project",
                    "crawl_run_id": run_id
                }

    # Create a versioned CrawlRun
    crawl_run = CrawlRun(
        project_id=project.id,
        started_at=datetime.datetime.now(datetime.timezone.utc),
        status="running",
        pages_found=0,
        current_url=project.url,
        max_pages=max_pages
    )
    db.add(crawl_run)
    db.commit()
    db.refresh(crawl_run)

    # Create stop signal
    stop_event = threading.Event()
    active_crawls[crawl_run.id] = stop_event

    # Launch background thread
    thread = threading.Thread(
        target=_run_recursive_crawl,
        args=(project.id, project.url, crawl_run.id, max_pages, stop_event),
        daemon=True
    )
    thread.start()

    return {
        "message": "Crawl started in background",
        "crawl_run_id": crawl_run.id,
        "max_pages": max_pages,
        "status": "running"
    }


# ── Status polling endpoint ─────────────────────────────────────

@router.get("/status/{crawl_run_id}")
def get_crawl_status(
    crawl_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Get real-time crawl progress.
    Frontend polls this every 2 seconds.
    """
    run = (
        db.query(CrawlRun)
        .filter(CrawlRun.id == crawl_run_id)
        .first()
    )

    if not run:
        return {"error": "Crawl run not found"}

    return {
        "crawl_run_id": run.id,
        "status": run.status,
        "pages_found": run.pages_found or 0,
        "current_url": run.current_url,
        "max_pages": run.max_pages,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "is_active": crawl_run_id in active_crawls,
    }


# ── Stop crawl endpoint ─────────────────────────────────────────

@router.post("/stop/{crawl_run_id}")
def stop_crawl(
    crawl_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Gracefully stop a running crawl.
    Pages already crawled are saved.
    """
    if crawl_run_id not in active_crawls:
        # Check if it already finished
        run = db.query(CrawlRun).filter(CrawlRun.id == crawl_run_id).first()
        if run and run.status in ("completed", "stopped", "failed"):
            return {
                "message": f"Crawl already {run.status}",
                "status": run.status,
                "pages_found": run.pages_found or 0
            }
        return {"error": "Crawl run not found or not active"}

    # Signal the crawler to stop
    stop_event = active_crawls[crawl_run_id]
    stop_event.set()

    return {
        "message": "Stop signal sent. Crawl will stop after finishing current page.",
        "crawl_run_id": crawl_run_id
    }


# ── Graph endpoint (unchanged) ──────────────────────────────────

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