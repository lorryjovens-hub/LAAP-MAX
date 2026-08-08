---
name: pptx
description: Use this skill whenever the user wants to create, edit, or work with PowerPoint presentations (.pptx files). This includes creating slides with text and images, applying themes and layouts, adding charts and tables, and formatting presentations professionally. If the user mentions presentations, slides, PowerPoint, or .pptx files, use this skill.
---

# PowerPoint (PPTX) Creation Guide

## Overview

This guide covers creating PowerPoint presentations using the `python-pptx` library. Use this for generating professional slide decks programmatically.

## Quick Start

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Add a title slide
slide = prs.slides.add_slide(prs.slide_layouts[0])
title = slide.shapes.title
subtitle = slide.placeholders[1]
title.text = "My Presentation"
subtitle.text = "Created with Claude"

prs.save('presentation.pptx')
```

## Common Operations

### Creating Content Slides

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

prs = Presentation()

# Bullet slide
slide = prs.slides.add_slide(prs.slide_layouts[1])
slide.shapes.title.text = "Key Points"

body = slide.placeholders[1]
tf = body.text_frame
tf.text = "First point"
p = tf.add_paragraph()
p.text = "Second point"
p.level = 1  # Sub-point
p = tf.add_paragraph()
p.text = "Third point"

prs.save('bullets.pptx')
```

### Adding Tables

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])

rows, cols = 4, 3
table_shape = slide.shapes.add_table(rows, cols, 
    Inches(1), Inches(2), Inches(8), Inches(4))
table = table_shape.table

# Header
for i, header in enumerate(['Name', 'Value', 'Notes']):
    table.cell(0, i).text = header

prs.save('table.pptx')
```

### Adding Images

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])

img_path = 'image.png'
slide.shapes.add_picture(img_path, Inches(1), Inches(1), Inches(8), Inches(5))

prs.save('image.pptx')
```

### Adding Charts

```python
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])

chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Revenue', (100, 200, 300, 400))

chart = slide.shapes.add_chart(
    1,  # Bar chart
    Inches(1), Inches(1), Inches(8), Inches(5),
    chart_data
).chart

prs.save('chart.pptx')
```

## Design Tips

- Use consistent fonts and colors
- Keep text concise - slides supplement, not replace, the speaker
- Use high-contrast colors for readability
- Add slide numbers for navigation
- Use the standard layouts when possible
- For widescreen: 13.333" x 7.5" (16:9)
- For standard: 10" x 7.5" (4:3)
