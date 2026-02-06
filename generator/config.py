"""Site configuration."""

from pathlib import Path

# Directory paths
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"

# Content section directories
BLOG_DIR = CONTENT_DIR / "blog"
PROJECTS_DIR = CONTENT_DIR / "projects"
PAGES_DIR = CONTENT_DIR / "pages"

# Site metadata
SITE_CONFIG = {
    "title": "dtupper.com",
    "description": "personal website, blog, projects",
    "author": "Tupper",
    "url": "https://dtupper.com",
    "language": "en",
    "locale": "en-US",
}

# Build settings
DEFAULT_DATE_FORMAT = "long"  # Babel date format: short, medium, long, full
POSTS_PER_PAGE = 10
GENERATE_RSS = True

# Content sections and their URL patterns
SECTIONS = {
    "blog": {
        "content_dir": BLOG_DIR,
        "url_pattern": "blog/{slug}",
        "template": "post.html",
        "index_template": "index.html",
        "date_in_url": True,
    },
    "projects": {
        "content_dir": PROJECTS_DIR,
        "url_pattern": "projects/{slug}",
        "template": "project.html",
        "index_template": "index.html",
        "date_in_url": False,
    },
    "pages": {
        "content_dir": PAGES_DIR,
        "url_pattern": "{slug}",
        "template": "page.html",
        "index_template": None,
        "date_in_url": False,
    },
}
