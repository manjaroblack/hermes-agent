---
name: concept-diagrams
description: Generate flat, minimal educational SVG visuals as HTML.
version: 0.1.0
author: v1k22 (original PR), ported into hermes-agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [diagrams, svg, visualization, education, physics, chemistry, engineering]
    related_skills: [architecture-diagram, excalidraw]
---

# Concept Diagrams

role: self-contained educational SVG/HTML diagram operator
do: classify subject/layout; load template/reference; map semantic colors; size/layer SVG; write standalone HTML; optionally serve loopback gallery; validate geometry/text/contrast; report file/URL
inputs: subject/facts, diagram type, labels/data, output path, optional gallery request
outputs: single offline `.html` with embedded SVG/CSS, optional loopback gallery, validation evidence
¬: gradients/shadows/glow/neon; rainbow color cycling; unclassed text; crossed arrows; cramped labels; `0.0.0.0` preview; hardcode gallery port; claim validity without checklist

Generate production-quality SVG diagrams inside a single self-contained HTML file. The template supplies the flat/minimal CSS system, semantic colors, typography, arrows, and automatic light/dark mode; no server/dependency is needed for the default output.

## When to Use

- physics/chemistry/math/biology mechanisms and charts
- physical objects, anatomy, cross-sections, exploded views, floor plans
- lifecycle/process journeys, hub-spoke systems, IoT/grids
- textbook educational visuals and general clean SVG fallback

Prefer `architecture-diagram` for dark tech architecture, `excalidraw` for hand-drawn whiteboards, and animation/video skills for motion. If no specialized skill fits, use this general educational aesthetic.

## Prerequisites

- load `templates/template.html`:

  ```
  skill_view(name="concept-diagrams", file_path="templates/template.html")
  ```

- optional type-specific reference: `references/physical-shape-cookbook.md`, `infrastructure-patterns.md`, or `dashboard-patterns.md`
- SVG/HTML output path

## Procedure

1. Decide type/layout from the tables below.
2. Load template/reference; use its `c-*`, `.t/.ts/.th`, `.box/.arr/.leader/.node` classes.
3. Lay out at `viewBox="0 0 680 H"`, safe area x=40..640, with 40px bottom buffer.
4. Write the complete HTML, replacing `<!-- PASTE SVG HERE -->`.
5. Save as standalone `.html`; optionally serve a loopback gallery only when requested.
6. Run the validation checklist; open the file or report loopback URL.

## Design System

### Philosophy

Flat (no gradients, drop shadows, blur, glow, neon); minimal (essential content, no decorative box icons); consistent (colors/spacing/type/strokes); dark-mode ready (classes, no per-mode SVG).

### Color ramps

Put one class on a `<g>`/shape; template maps light/dark stops:

| Class      | 50 (lightest) | 100     | 200     | 400     | 600     | 800     | 900 (darkest) |
|------------|---------------|---------|---------|---------|---------|---------|---------------|
| `c-purple` | #EEEDFE | #CECBF6 | #AFA9EC | #7F77DD | #534AB7 | #3C3489 | #26215C |
| `c-teal`   | #E1F5EE | #9FE1CB | #5DCAA5 | #1D9E75 | #0F6E56 | #085041 | #04342C |
| `c-coral`  | #FAECE7 | #F5C4B3 | #F0997B | #D85A30 | #993C1D | #712B13 | #4A1B0C |
| `c-pink`   | #FBEAF0 | #F4C0D1 | #ED93B1 | #D4537E | #993556 | #72243E | #4B1528 |
| `c-gray`   | #F1EFE8 | #D3D1C7 | #B4B2A9 | #888780 | #5F5E5A | #444441 | #2C2C2A |
| `c-blue`   | #E6F1FB | #B5D4F4 | #85B7EB | #378ADD | #185FA5 | #0C447C | #042C53 |
| `c-green`  | #EAF3DE | #C0DD97 | #97C459 | #639922 | #3B6D11 | #27500A | #173404 |
| `c-amber`  | #FAEEDA | #FAC775 | #EF9F27 | #BA7517 | #854F0B | #633806 | #412402 |
| `c-red`    | #FCEBEB | #F7C1C1 | #F09595 | #E24B4A | #A32D2D | #791F1F | #501313 |

Color encodes meaning, not sequence: group same categories; `c-gray` neutral/structural; use 2-3 colors, not 6+; prefer purple/teal/coral/pink for general categories; reserve blue/green/amber/red for info/success/warning/error. Template mapping: light=50 fill + 600 stroke + 800 title/600 subtitle; dark=800 fill + 200 stroke + 100 title/200 subtitle.

### Typography

Only these sizes/classes:

| Class | Size | Weight | Use |
|-------|------|--------|-----|
| `th`  | 14px | 500    | Node titles, region labels |
| `ts`  | 12px | 400    | Subtitles, descriptions, arrow labels |
| `t`   | 14px | 400    | General text |

Sentence case; no Title Case/ALL CAPS. Every `<text>` has a class; boxed text uses `dominant-baseline="central"`; centered box text uses `text-anchor="middle"`. Width estimate: 14px≈8px/char, 12px≈6.5px/char; `box_width >= char_count × px_per_char + 48`.

### Geometry

- viewBox width=680; safe x=40..640; H=bottom-most content + 40px
- box gap >=60px; inside padding=24px horizontal/12px vertical; container padding>=20px
- arrowhead gap=10px; single line height=44px; two lines=56px with 18px baseline gap
- rect radius: node 8, inner 12, outer 16-20
- node border stroke=0.5px; connector paths `fill="none"`
- max nesting=2-3 levels; max 4-5 flow nodes/row

Every SVG includes:

```xml
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
          stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>
```

Use `marker-end="url(#arrow)"`; `context-stroke` inherits connector color.

## SVG Patterns

```xml
<svg width="100%" viewBox="0 0 680 {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>

  <!-- Diagram content here -->

</svg>
```

Single-line node:

```xml
<g class="node c-blue">
  <rect x="100" y="20" width="180" height="44" rx="8" stroke-width="0.5"/>
  <text class="th" x="190" y="42" text-anchor="middle" dominant-baseline="central">Service name</text>
</g>
```

Two-line node:

```xml
<g class="node c-teal">
  <rect x="100" y="20" width="200" height="56" rx="8" stroke-width="0.5"/>
  <text class="th" x="200" y="38" text-anchor="middle" dominant-baseline="central">Service name</text>
  <text class="ts" x="200" y="56" text-anchor="middle" dominant-baseline="central">Short description</text>
</g>
```

Connector:

```xml
<line x1="200" y1="76" x2="200" y2="120" class="arr" marker-end="url(#arrow)"/>
```

Container:

```xml
<g class="c-purple">
  <rect x="40" y="92" width="600" height="300" rx="16" stroke-width="0.5"/>
  <text class="th" x="66" y="116">Container label</text>
  <text class="ts" x="66" y="134">Subtitle info</text>
</g>
```

## Diagram Types

| Type | Layout/use |
|---|---|
| flowchart | CI/CD, requests, approvals; one direction |
| structural/containment | layers/nesting; large outer + inner regions; dashed logical groups |
| API/endpoint map | root → resource groups → endpoints |
| microservice topology | services + communication arrows/queues |
| data flow | left-to-right source → process → sink |
| physical/structural | aircraft, hardware, anatomy; path/polygon/ellipse/rect shapes |
| infrastructure integration | hub-spoke smart city/IoT/grid; semantic lines |
| UI/dashboard mockup | screen frame + charts/gauges/indicators |

Load type-specific refs before physical/infrastructure/dashboard work.

## Validation Checklist

1. Every `<text>` has `t`, `ts`, or `th`; boxed text has `dominant-baseline="central"`.
2. Arrow connectors have `fill="none"`; no line crosses an unrelated box.
3. Width meets 14px `longest_chars×8+48` and 12px `longest_chars×6.5+48`.
4. ViewBox H=bottom-most element + 40; content x stays 40..640.
5. `c-*` classes are on groups/shapes, not connector paths; arrow defs exists.
6. No gradients/shadows/blur/glow; node border stroke=0.5px.

## Output and Preview

Default: fill title/subtitle/SVG in `templates/template.html`, then write one HTML:

```python
# 1. Load the template
template = skill_view("concept-diagrams", "templates/template.html")

# 2. Fill in title, subtitle, and paste your SVG
html = template.replace(
    "<!-- DIAGRAM TITLE HERE -->", "SN2 reaction mechanism"
).replace(
    "<!-- OPTIONAL SUBTITLE HERE -->", "Bimolecular nucleophilic substitution"
).replace(
    "<!-- PASTE SVG HERE -->", svg_content
)

# 3. Write to a user-chosen path (or ./ by default)
write_file("./sn2-mechanism.html", html)
```

Open without a server/dependency:

```
# macOS
open ./sn2-mechanism.html
# Linux
xdg-open ./sn2-mechanism.html
```

Optional multi-diagram gallery only when requested:

```bash
# Put each diagram in its own folder under .diagrams/
mkdir -p .diagrams/sn2-mechanism
# ...write .diagrams/sn2-mechanism/index.html...

# Serve on loopback only, free port
cd .diagrams && python -c "
import http.server, socketserver
with socketserver.TCPServer(('127.0.0.1', 0), http.server.SimpleHTTPRequestHandler) as s:
    print(f'Serving at http://127.0.0.1:{s.server_address[1]}/')
    s.serve_forever()
" &
```

Use loopback only, OS-selected free port, and report chosen URL. Fixed port still uses `127.0.0.1:<port>`, never `0.0.0.0`; stop with `kill %1`/`pkill -f "http.server"`.

## Examples and Routing

Examples in `examples/` include hospital/film/password-reset/LLM flows, UML, aircraft, turbine, smartphone, floor plan, banana journey, CPU, SN2, smart city, grid, and grouped bar chart. Load with:

```
skill_view(name="concept-diagrams", file_path="examples/<filename>")
```

Reference inventory:

| File | Type | Demonstrates |
|------|------|--------------|
| `hospital-emergency-department-flow.md` | Flowchart | Priority routing with semantic colors |
| `feature-film-production-pipeline.md` | Flowchart | Phased workflow, horizontal sub-flows |
| `automated-password-reset-flow.md` | Flowchart | Auth flow with error branches |
| `autonomous-llm-research-agent-flow.md` | Flowchart | Loop-back arrows, decision branches |
| `place-order-uml-sequence.md` | Sequence | UML sequence diagram style |
| `commercial-aircraft-structure.md` | Physical | Paths, polygons, ellipses for realistic shapes |
| `wind-turbine-structure.md` | Physical cross-section | Underground/above-ground separation, color coding |
| `smartphone-layer-anatomy.md` | Exploded view | Alternating left/right labels, layered components |
| `apartment-floor-plan-conversion.md` | Floor plan | Walls, doors, proposed changes in dotted red |
| `banana-journey-tree-to-smoothie.md` | Narrative journey | Winding path, progressive state changes |
| `cpu-ooo-microarchitecture.md` | Hardware pipeline | Fan-out, memory hierarchy sidebar |
| `sn2-reaction-mechanism.md` | Chemistry | Molecules, curved arrows, energy profile |
| `smart-city-infrastructure.md` | Hub-spoke | Semantic line styles per system |
| `electricity-grid-flow.md` | Multi-stage flow | Voltage hierarchy, flow markers |
| `ml-benchmark-grouped-bar-chart.md` | Chart | Grouped bars, dual axis |

| User says | Diagram type | Suggested colors |
|-----------|--------------|------------------|
| "show the pipeline" | Flowchart | gray start/end, purple steps, red errors, teal deploy |
| "draw the data flow" | Data pipeline (left-right) | gray sources, purple processing, teal sinks |
| "visualize the system" | Structural (containment) | purple container, teal services, coral data |
| "map the endpoints" | API tree | purple root, one ramp per resource group |
| "show the services" | Microservice topology | gray ingress, teal services, purple bus, coral workers |
| "draw the aircraft/vehicle" | Physical | paths, polygons, ellipses for realistic shapes |
| "smart city / IoT" | Hub-spoke integration | semantic line styles per subsystem |
| "show the dashboard" | UI mockup | dark screen, chart colors: teal, purple, coral for alerts |
| "power grid / electricity" | Multi-stage flow | voltage hierarchy (HV/MV/LV line weights) |
| "wind turbine / turbine" | Physical cross-section | foundation + tower cutaway + nacelle color-coded |
| "journey of X / lifecycle" | Narrative journey | winding path, progressive state changes |
| "layers of X / exploded" | Exploded layer view | vertical stack, alternating labels |
| "CPU / pipeline" | Hardware pipeline | vertical stages, fan-out to execution ports |
| "floor plan / apartment" | Floor plan | walls, doors, proposed changes in dotted red |
| "reaction mechanism" | Chemistry | atoms, bonds, curved arrows, transition state, energy profile |

## Pitfalls

- specialized skill wins when available; this is fallback, not forced routing
- `c-*` colors mean categories/semantics; do not cycle rainbow colors
- labels need width/padding; keep nesting shallow at 680px
- missing `fill="none"` makes SVG paths fill black
- standalone HTML first; gallery is explicit opt-in
- loopback-only gallery; never expose diagrams with `0.0.0.0`

## Verification

- template loaded and SVG has arrow `<defs>`
- HTML opens offline with automatic light/dark styles
- checklist 1-6 passes; no overflow/crossed arrows
- standalone file exists and is non-empty
- optional gallery binds loopback + ephemeral/fixed approved port and is stoppable
