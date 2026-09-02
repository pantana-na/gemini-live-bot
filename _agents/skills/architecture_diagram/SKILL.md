---
name: architecture-diagram
description: "Creates professional, dark-themed technical architecture/cloud/infra diagrams and documentation as markdown (.md) files in the 'docs' folder inside the project folder (with companion standalone HTML/SVG assets). Use when the user asks to create, generate, draw or visualize a technical system architecture, cloud infrastructure, microservice topology, or api/database deployment map. Don't use for physical objects, whiteboard sketches, scientific diagrams, or narrative journeys."
---

# Architecture Diagram Skill

Generate professional, dark-themed technical architecture diagrams and documentation as markdown (`.md`) files in the `docs/` folder inside the project folder, with accompanying standalone HTML/inline SVG graphics. No external tools, no API keys, no rendering libraries — just write the files and review in markdown viewers or browsers.

## Scope

**Best suited for:** - Software system architecture (frontend / backend /
database layers) - Cloud infrastructure (VPC, regions, subnets, managed
services) - Microservice / service-mesh topology - Database + API map,
deployment diagrams - Anything with a tech-infra subject that fits a dark,
grid-backed aesthetic

**Look elsewhere first for:** - Physics, chemistry, math, biology, or other
scientific subjects - Physical objects (vehicles, hardware, anatomy,
cross-sections) - Floor plans, narrative journeys, educational / textbook-style
visuals - Hand-drawn whiteboard sketches (consider `excalidraw`) - Animated
explainers (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none
fits, this skill can also serve as a general SVG diagram fallback — the output
will just carry the dark tech aesthetic described below.

Based on
[Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator)
(MIT).

## Workflow

1.  User describes their system architecture (components, connections, technologies).
2.  Generate the architecture documentation and diagram following the design system below.
3.  Save the markdown document with `write_to_file` to `docs/[project-name]-architecture.md` (or `docs/architecture.md`) inside the project folder. Ensure the `docs/` directory is created if it does not already exist.
4.  (Optional / Recommended) Save the standalone interactive HTML diagram file to `docs/[project-name]-architecture.html` inside the project folder, and link to it from the markdown document.
5.  User can view the markdown file or open the HTML file in any browser.

### Output Location

**CRITICAL**: Always output the architecture document as a markdown (`.md`) file in the `docs/` folder inside the project root:
- **Primary Markdown Document**: `docs/[project-name]-architecture.md` (or `docs/architecture.md`)
- **Companion HTML Diagram Asset**: `docs/[project-name]-architecture.html`

Ensure the `docs/` directory inside the project folder exists before writing.

### Preview

After saving, suggest the user review the markdown file in `docs/` or open the HTML file:
```bash
# macOS
open ./docs/my-architecture.html

# Linux
xdg-open ./docs/my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

Component Type  | Fill (rgba)               | Stroke (Hex)
:-------------- | :------------------------ | :----------------------
**Frontend**    | `rgba(8, 51, 68, 0.4)`    | `#22d3ee` (cyan-400)
**Backend**     | `rgba(6, 78, 59, 0.4)`    | `#34d399` (emerald-400)
**Database**    | `rgba(76, 29, 149, 0.4)`  | `#a78bfa` (violet-400)
**AWS/Cloud**   | `rgba(120, 53, 15, 0.3)`  | `#fbbf24` (amber-400)
**Security**    | `rgba(136, 19, 55, 0.4)`  | `#fb7185` (rose-400)
**Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400)
**External**    | `rgba(30, 41, 59, 0.5)`   | `#94a3b8` (slate-400)

### Typography & Background

-   **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
-   **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny
    labels)
-   **Background:** Slate-950 (`#020617`) with a subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering

Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent
arrows from showing through semi-transparent fills, use a **double-rect masking
technique**: 1. Draw an opaque background rect (`#0f172a`) 2. Draw the
semi-transparent styled rect on top

### Connection Rules

-   **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render
    behind component boxes
-   *Arrowheads:* Defined via SVG markers
-   *Security Flows:* Use dashed lines in rose color (`#fb7185`)
-   *Boundaries:*
    -   *VPC / Subnets:* Dashed (`4,4`), custom colors (e.g., rose for SG,
        cyan/amber for VPC/subnets)
    -   *Security Groups:* Dashed (`4,4`), rose color
    -   *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic

-   **Standard Height:** 60px (Services); 80-120px (Large components)
-   **Vertical Gap:** Minimum 40px between components
-   **Message Buses:** Must be placed *in the gap* between services, not
    overlapping them
-   **Legend Placement:** **CRITICAL.** Must be placed outside all boundary
    boxes. Calculate the lowest Y-coordinate of all boundaries and place the
    legend at least 20px below it.

## Document Structure

The generated HTML file follows a four-part layout: 1. **Header:** Title with a
pulsing dot indicator and subtitle 2. **Main SVG:** The diagram contained within
a rounded border card 3. **Summary Cards:** A grid of three cards below the
diagram for high-level details 4. **Footer:** Minimal metadata

### Info Card Pattern

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

## Template Reference

Copy and customize the template at `resources/template.html`. Key customization
points:

*   Update the `<title>` and header text
*   Modify SVG `viewBox` dimensions if needed (default: 1000 x 820)
*   Add/remove/reposition component boxes
*   Draw connection arrows between components
*   Update the three summary cards
*   Update footer metadata

## Output Requirements

-   **Markdown Document in `docs/`:** Always output the primary architecture document as a `.md` file inside the `docs/` folder of the project directory.
-   **Standalone HTML in `docs/`:** One self-contained `.html` diagram file saved in `docs/` alongside the markdown report.
-   **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts).
-   **No JavaScript:** Use pure CSS for any animations (like pulsing dots).
-   **Compatibility:** Must render correctly in any modern web browser and markdown previewer.
