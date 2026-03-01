from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from src.config import TEMPLATES_DIR, STATIC_DIR

TEMPLATE = Jinja2Templates(directory=TEMPLATES_DIR)

STATIC = StaticFiles(directory=STATIC_DIR)