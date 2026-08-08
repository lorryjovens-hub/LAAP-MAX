"""Extract text from downloaded Anthropic paper HTML and Dehaene PDF."""
from pathlib import Path
import json

lit = Path("d:/LAAP/experiments/jspace_laap/literature")

# HTML -> text
html_path = lit / "anthropic_paper.html"
print(f"HTML size: {html_path.stat().st_size}")

try:
    from bs4 import BeautifulSoup
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts and styles
    for tag in soup(["script", "style", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    (lit / "anthropic_paper_extracted.txt").write_text(text, encoding="utf-8")
    print(f"Extracted HTML text length: {len(text)}")
except Exception as e:
    print(f"HTML extraction failed: {e}")

# PDF -> text
pdf_path = lit / "dehaene_commentary.pdf"
print(f"PDF size: {pdf_path.stat().st_size}")

errors = []
for lib in ["pdfplumber", "pypdf"]:
    try:
        if lib == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
            (lit / "dehaene_commentary_extracted.txt").write_text(text, encoding="utf-8")
            print(f"Extracted PDF text length with pdfplumber: {len(text)}")
            break
        else:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            (lit / "dehaene_commentary_extracted.txt").write_text(text, encoding="utf-8")
            print(f"Extracted PDF text length with pypdf: {len(text)}")
            break
    except Exception as e:
        errors.append(f"{lib}: {e}")
else:
    print("All PDF extraction failed:", errors)
