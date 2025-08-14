# app/routers/content.py
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from ..services.html_cleaner import clean_html_main

router = APIRouter()

class CleanHtmlRequest(BaseModel):
    html: str

@router.post("/clean_html")
def clean_html(req: CleanHtmlRequest):
    return clean_html_main(req.html)

@router.post("/clean_html_file")
async def clean_html_file(file: UploadFile = File(...)):
    raw = await file.read()
    out = clean_html_main(raw.decode(errors="ignore"))
    return out
