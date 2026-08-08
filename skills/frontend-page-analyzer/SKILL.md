---
name: frontend-page-analyzer
description: Analyze and learn custom webpage frontend code, provide learning feedback, and implement frontend patterns from reference pages. Use when user asks to learn a webpage frontend, analyze frontend code, or extract frontend patterns into reusable workflows.
---

# Frontend Page Analyzer Skill

## Purpose
This skill helps analyze custom webpage frontend code, extract design patterns, component structures, and implementation best practices, then provide structured learning feedback and reusable workflows.

## Workflow
1. Retrieve the target frontend code (HTML/CSS/JS or framework source)
2. Analyze tech stack, component structure, styling approach, and interactive logic
3. Document key learnings, strengths, and areas for improvement
4. Create reusable code snippets/templates for common patterns found
5. Generate structured learning feedback report

## Analysis Result - GitBox Frontend
### Tech Stack Identification
- **Build Tool**: Vite (from asset naming pattern `index-[hash].js/css`)
- **Framework**: React (single root div `<div id="root"></div>` typical for React/Vue SPA, module script entry)
- **Integrated Services**: Kimi LLM SDK (included `https://www.kimi.com/sdk-seed.js` for AI capabilities)
- **Project Name**: GitBox (likely a Git repository/code management frontend application)

### Architecture Features
✅ **Advantages**:
- Modern SPA architecture with separated JS/CSS assets for efficient caching
- CDN loaded third-party SDK for reduced bundle size
- Responsive viewport configured for mobile compatibility
- Cross-origin resource loading enabled for assets

🔍 **Key Patterns**:
- Standard Vite + React project structure that can be reused for similar AI-integrated web applications
- Minimal HTML entry point that delegates all rendering to client-side JS
- Deferred loading of third-party SDK to avoid blocking page render

## Lorry Personal Site Style Reference Library
### Analyzed Sites (14 valid, 1 404)
| Category | Count | Examples |
| --- | --- | --- |
| AI Application | 6 | BioNeural AI, Memoradb, AI Applicantion, AI Shop, Jarvis PM, GitBox |
| ClawLink Series | 4 | ClawLink main, Edge, Dashboard, TriLayer |
| Creative Project | 2 | Zhiyingsheng Music, Zhiyingsheng 3D Mapping |
| Tool/System | 3 | ESP32 Agent, Quantitative Trading, Dev Tools Guide |

### Design Style Guidelines for Imitation
1. **Tech Stack Default**: Use React + Vite + Tailwind CSS for all new projects matching Lorry's style
2. **Deployment**: Netlify static deployment standard
3. **Structure**: SPA single-page application with `<div id="root"></div>` entry point
4. **Naming**: Consistent naming convention for projects: [project-name]-lorry.netlify.app
5. **Theme**: Modern tech/sci-fi style for AI/tech projects, creative visual style for art projects
6. **Mandatory Element**: All websites must include a link to Lorry's personal blog: https://lorryjovens.netlify.app/ (typically in footer or about section)

Full analysis details: `/references/lorry_sites_analysis.md`

## External Design Reference Library
- **land-book.com**: Global top landing page design inspiration platform, contains massive high-quality frontend design cases for reference when creating new websites. Covers various styles: tech/AI, creative, e-commerce, portfolio, SaaS product landing pages. Can be used for layout, interaction, color matching reference.

## Resources
- `/references/analysis-template.md`: Standard analysis report template
- `/scripts/extract-components.py`: Script to extract component structures from HTML/React code
