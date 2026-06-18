# 6 tables (the knowledge graph)
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import Text
from sqlalchemy import Float

from sqlalchemy.orm import relationship

from app.database.db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    url = Column(String, nullable=False)

    pages = relationship(
        "Page",
        back_populates="project"
    )

    crawl_runs = relationship(
        "CrawlRun",
        back_populates="project"
    )


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id")
    )

    started_at = Column(DateTime)

    completed_at = Column(DateTime, nullable=True)

    status = Column(String)

    # Live progress fields
    pages_found = Column(Integer, default=0)

    current_url = Column(String, nullable=True)

    max_pages = Column(Integer, nullable=True)

    project = relationship(
        "Project",
        back_populates="crawl_runs"
    )

    pages = relationship(
        "Page",
        back_populates="crawl_run"
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)

    url = Column(String)

    status_code = Column(Integer)

    crawl_date = Column(DateTime)

    depth = Column(Integer)

    project_id = Column(
        Integer,
        ForeignKey("projects.id")
    )

    crawl_run_id = Column(
        Integer,
        ForeignKey("crawl_runs.id"),
        nullable=True
    )

    parent_id = Column(
        Integer,
        ForeignKey("pages.id"),
        nullable=True
    )

    project = relationship(
        "Project",
        back_populates="pages"
    )

    crawl_run = relationship(
        "CrawlRun",
        back_populates="pages"
    )

    parent = relationship(
        "Page",
        remote_side=[id],
        back_populates="children"
    )

    children = relationship(
        "Page",
        back_populates="parent"
    )

    elements = relationship(
        "Element",
        back_populates="page"
    )

    features = relationship(
        "PageFeature",
        back_populates="page"
    )


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, index=True)

    page_id = Column(
        Integer,
        ForeignKey("pages.id")
    )

    # Semantic role: input, link, button, checkbox, radio, textarea, dropdown, form, table
    element_type = Column(String)

    # Actual HTML tag: a, button, input, select, textarea, form, table
    tag_name = Column(String, nullable=True)

    name = Column(String)

    locator = Column(String)

    # The HTML id attribute — best locator source
    element_id = Column(String, nullable=True)

    text = Column(String)

    placeholder = Column(String, nullable=True)

    # The HTML type attribute for inputs: text, email, password, hidden, checkbox, radio, etc.
    input_type = Column(String, nullable=True)

    # The href attribute for links
    href = Column(String, nullable=True)

    # Whether the element is visible on screen
    visible = Column(String, nullable=True, default="true")

    required = Column(String, nullable=True)

    page = relationship(
        "Page",
        back_populates="elements"
    )


class PageFeature(Base):
    __tablename__ = "page_features"

    id = Column(Integer, primary_key=True, index=True)

    page_id = Column(
        Integer,
        ForeignKey("pages.id")
    )

    feature_type = Column(String)

    feature_value = Column(String)

    page = relationship(
        "Page",
        back_populates="features"
    )


class PageLink(Base):
    __tablename__ = "page_links"

    id = Column(Integer, primary_key=True)

    from_page_id = Column(
        Integer,
        ForeignKey("pages.id")
    )

    to_url = Column(String)    


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True)

    page_id = Column(
        Integer,
        ForeignKey("pages.id")
    )

    title = Column(String)

    category = Column(String)

    priority = Column(String)

    expected_result = Column(String)

    source = Column(String, nullable=True)

    generated_by = Column(String, nullable=True)    

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True)

    page_id = Column(Integer)

    model = Column(String)

    recommendation = Column(Text)

    created_at = Column(DateTime)    


class AutomationScript(Base):
    __tablename__ = "automation_scripts"

    id = Column(Integer, primary_key=True)

    page_id = Column(
        Integer,
        ForeignKey("pages.id")
    )

    framework = Column(String)

    script_name = Column(String)

    script_content = Column(Text)

    generation_type = Column(String)

    model_name = Column(String, nullable=True)

    version = Column(Integer)

    script_path = Column(String, nullable=True)


class TestExecution(Base):
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True)

    page_id = Column(Integer)

    script_id = Column(Integer)

    status = Column(String)

    started_at = Column(DateTime)

    completed_at = Column(DateTime)

    duration = Column(Float)

    error_message = Column(Text)

    screenshot_path = Column(String)

    execution_log = Column(Text)
