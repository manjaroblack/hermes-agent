---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
version: 1.0.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw]
---

# Architecture Diagram

role: technical diagram designer
do: produce one offline-capable dark, grid-backed architecture HTML with inline SVG/CSS
inputs: components, connections, technologies, boundaries, title/subtitle, summary data
outputs: standalone `.html` with SVG, three summary cards, metadata footer
¬: scientific/physical/narrative subjects when a specialist fits; hand-drawn diagrams → `excalidraw`; animation → animation skill

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT). If no specialist exists, use this as a general SVG fallback with the dark tech aesthetic.

## When to Use

- frontend/backend/database architecture
- VPC, regions, subnets, managed cloud services
- microservice/service-mesh topology
- database/API maps and deployment diagrams
- technical infrastructure that fits a dark grid-backed visual language

¬prefer: physics, chemistry, math, biology; vehicles/hardware/anatomy/cross-sections; floor plans, journeys, educational textbook visuals; hand-drawn whiteboard; animated explainers.

## Procedure

1. Gather components, links, technologies, boundaries, and requested output path.
2. Generate HTML with the design system below.
3. Save with `write_file` to user path (e.g. `~/architecture-diagram.html`) or default `./[project-name]-architecture.html`.
4. Open in any modern browser; offline except optional Google Fonts.

### Preview

```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Visual Contract

### Semantic palette

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

Typography: JetBrains Mono from Google Fonts; names 12px, sublabels 9px, annotations 8px, tiny labels 7px. Background: Slate-950 `#020617`; subtle 40px grid:

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

### SVG rules

- component = rounded rect `rx="6"`, 1.5px stroke
- mask translucent fills: opaque `#0f172a` rect first, styled semi-transparent rect second
- draw arrows after grid and before boxes; use SVG markers
- security flow = dashed rose `#fb7185`
- security-group boundary = dashed `4,4`, rose
- region boundary = dashed `8,4`, amber, `rx="12"`
- service height 60px; large components 80–120px; vertical gap ≥40px
- place message bus in gaps, never overlapping services
- legend outside every boundary; find lowest boundary Y, place legend ≥20px below it

### HTML layout

1. Header: title + pulsing dot + subtitle
2. Main SVG inside rounded border card
3. Three summary cards below diagram
4. Minimal metadata footer

```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Output Requirements

- one self-contained `.html`
- inline CSS + SVG; Google Fonts is the only permitted external dependency
- no JavaScript; CSS-only animation (e.g. pulsing dot)
- render correctly in modern browsers

## Template

Load exact structure, CSS, SVG component examples, arrow variants, security groups, region boundaries, and legend before generation:

```text
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

## Pitfalls

- do not let labels, arrows, or legend overlap the diagram or its boundaries
- do not add JavaScript or external assets beyond the permitted Google Fonts link
- avoid dense miniature nodes; reduce detail or split the diagram when readability fails

## Verification

- file exists at stated path and opens in a modern browser
- SVG contains requested components, arrows, boundaries, legend outside boundaries
- all CSS/SVG inline; no JS; offline behavior except Google Fonts
- output has header, rounded SVG card, three summary cards, footer
