---
name: docx
description: Use this skill whenever the user wants to create, edit, or work with Word documents (.docx files). This includes creating new documents, editing existing ones, converting between formats, applying styles and formatting, and extracting content from Word documents. If the user mentions .docx files, Word documents, or wants to create professional documents, use this skill.
---

# Word Document (DOCX) Processing Guide

## Overview

This guide covers creating, editing, and processing Word documents (.docx files) using Python libraries. The primary library used is `python-docx`.

## Quick Start

```python
from docx import Document
from docx.shared import Inches, Pt, Cm

# Create a new document
doc = Document()

# Add content
doc.add_heading('Document Title', level=1)
doc.add_paragraph('This is a paragraph with some text.')

# Save
doc.save('output.docx')
```

## Common Operations

### Creating Documents

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Title
title = doc.add_heading('Professional Report', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Subtitle
doc.add_paragraph('Prepared by: Claude').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('')

# Section heading
doc.add_heading('Executive Summary', level=1)

# Body text
p = doc.add_paragraph('This report covers...')
p.style = doc.styles['Normal']

# Bold and italic
p = doc.add_paragraph('')
run = p.add_run('Important: ')
run.bold = True
run.font.color.rgb = RGBColor(255, 0, 0)
p.add_run('This section requires attention.')

doc.save('report.docx')
```

### Adding Tables

```python
from docx import Document

doc = Document()
table = doc.add_table(rows=3, cols=3, style='Table Grid')

# Header row
for i, header in enumerate(['Name', 'Value', 'Notes']):
    cell = table.rows[0].cells[i]
    cell.text = header

# Data rows
data = [
    ['Item 1', '100', 'First item'],
    ['Item 2', '200', 'Second item']
]
for i, row_data in enumerate(data, 1):
    for j, value in enumerate(row_data):
        table.rows[i].cells[j].text = value

doc.save('table_example.docx')
```

### Adding Images

```python
from docx import Document
from docx.shared import Inches

doc = Document()
doc.add_heading('Document with Image', level=1)
doc.add_picture('image.png', width=Inches(4.0))
doc.save('with_image.docx')
```

### Reading Documents

```python
from docx import Document

doc = Document('input.docx')

# Read all paragraphs
for para in doc.paragraphs:
    print(para.text)

# Read tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)
```

### Working with Styles

```python
from docx import Document
from docx.shared import Pt

doc = Document()

# Heading levels
doc.add_heading('Heading 1', level=1)
doc.add_heading('Heading 2', level=2)
doc.add_heading('Heading 3', level=3)

# Custom style
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

doc.save('styled.docx')
```

### Adding Lists

```python
from docx import Document

doc = Document()

# Bullet list
doc.add_paragraph('First item', style='List Bullet')
doc.add_paragraph('Second item', style='List Bullet')
doc.add_paragraph('Third item', style='List Bullet')

# Numbered list
doc.add_paragraph('Step one', style='List Number')
doc.add_paragraph('Step two', style='List Number')

doc.save('lists.docx')
```

## Tips

- Use `python-docx` for basic to intermediate documents
- For advanced formatting, consider using templates
- Always close/save documents properly
- Use `Inches()` and `Cm()` for consistent measurements
