---
name: pdf
description: Process PDF files - extract text, create PDFs, merge documents. Use when user asks to read PDF, create PDF, or work with PDF files.
---

# PDF Processing Skill

You now have expertise in PDF manipulation. Follow these workflows:

## Reading PDFs

**Option 1: Quick text extraction (preferred)**
```bash
# Using pdftotext (poppler-utils)
pdftotext input.pdf -  # Output to stdout
pdftotext input.pdf output.txt  # Output to file

# If pdftotext not available, try:
python3 -c "
import fitz  # PyMuPDF
doc = fitz.open('input.pdf')
for page in doc:
    print(page.get_text())
"
```

**Option 2: Page-by-page with metadata**
```python
import fitz  # pip install pymupdf

doc = fitz.open("input.pdf")
print(f"Pages: {len(doc)}")
print(f"Metadata: {doc.metadata}")

for i, page in enumerate(doc):
    text = page.get_text()
    print(f"--- Page {i+1} ---")
    print(text)
```

## Creating PDFs (with Chinese support)

By default, PDF libraries do not include Chinese fonts. You must specify a font that supports CJK.

**Option 1: From Markdown using markdown-pdf (Easiest & Recommended)**
If you have a markdown file (e.g., `input.md`), you can convert it directly to PDF using the `markdown-pdf` CLI tool. This tool handles Chinese characters well on macOS.
```bash
# First, ensure the tool is installed (if not already)
npm install -g markdown-pdf

# Then convert the file
markdown-pdf input.md -o output.pdf
```

**Option 2: Programmatically with ReportLab (For custom layouts)**
```python
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 1. Use a system Chinese font (e.g., macOS Songti)
font_path = "/System/Library/Fonts/Supplemental/Songti.ttc"

# 2. Register the font
pdfmetrics.registerFont(TTFont("Songti", font_path))

# 3. Use the registered font
c = canvas.Canvas("output_chinese.pdf")
c.setFont("Songti", 12)
c.drawString(100, 750, "你好，PDF！这是中文测试。")
c.save()
```

## Reading PDFs

```python
import fitz

result = fitz.open()
for pdf_path in ["file1.pdf", "file2.pdf", "file3.pdf"]:
    doc = fitz.open(pdf_path)
    result.insert_pdf(doc)
result.save("merged.pdf")
```

## Splitting PDFs

```python
import fitz

doc = fitz.open("input.pdf")
for i in range(len(doc)):
    single = fitz.open()
    single.insert_pdf(doc, from_page=i, to_page=i)
    single.save(f"page_{i+1}.pdf")
```

## Key Libraries

| Task | Library | Install |
|------|---------|---------|
| Read/Write/Merge | PyMuPDF | `pip install pymupdf` |
| Create from scratch | ReportLab | `pip install reportlab` |
| HTML to PDF | pdfkit | `pip install pdfkit` + wkhtmltopdf |
| Text extraction | pdftotext | `brew install poppler` / `apt install poppler-utils` |

## Best Practices

1. **NEVER use `write_file` to create or edit a `.pdf` file directly.** PDFs are binary files. Always use a tool like `markdown-pdf` or a Python script (e.g., `reportlab`) to generate them.
2. **Always check if tools are installed** before using them (e.g., run `npm install -g markdown-pdf` if needed).
3. **Handle encoding issues** - PDFs may contain various character encodings.
4. **Large PDFs**: Process page by page to avoid memory issues.
5. **OCR for scanned PDFs**: Use `pytesseract` if text extraction returns empty.
