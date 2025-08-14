# app/services/html_cleaner.py
from bs4 import BeautifulSoup
from readability import Document

def clean_html_main(html: str) -> dict:
    """
    Return best-effort title + main text from noisy HTML.
    """
    # 1) Run Readability to isolate main article-ish content
    doc = Document(html)
    title = (doc.short_title() or "").strip()
    article_html = doc.summary() or ""

    # 2) Strip tags / scripts / styles
    soup = BeautifulSoup(article_html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 3) Normalize whitespace and join paragraphs
    text = "\n".join(s.strip() for s in soup.get_text("\n").splitlines())
    text = "\n".join(line for line in (l.strip() for l in text.splitlines()) if line)

    return {"title": title, "text": text}
