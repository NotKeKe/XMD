from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from .utils import STATIC, TEMPLATE

app = FastAPI()
app.mount("/static", STATIC, name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return TEMPLATE.TemplateResponse("index.html", {"request": request})