# PM Launch Agent — Design Document
**Date:** 2026-03-04
**Status:** Approved

---

## Overview

A standalone web app that takes raw PM launch notes and PRDs (pasted text or file uploads) and uses a multi-agent pipeline to produce release-ready marketing copy and visual asset specs. A human review and approve step gates all outputs before they are considered final.

Sits alongside the existing `gtm-asset-app/` but is a clean-slate rebuild with a focused scope.

---

## Architecture

### Approach: Orchestrator + Parallel Agents

```
PM Doc (paste or upload) + Brand Kit
           ↓
  [Orchestrator Agent]
  Extracts structured brief
           ↓          ↓
  [Copy Agent]   [Brief Agent]   ← run in parallel
  Marketing copy  Asset specs
           ↓          ↓
      Merged Review UI → Approve / Request Changes
```

**Tech stack:** FastAPI (Python) + Next.js (TypeScript) — same as existing app.
**AI model:** `claude-opus-4-6` with extended thinking for all three agents.
**Parallelism:** Copy Agent and Brief Agent triggered concurrently via Python `asyncio` after the Orchestrator completes.

### Directory Structure

```
pm-launch-agent/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py   # Extracts structured brief from PM doc
│   │   ├── copy_agent.py     # Generates marketing copy
│   │   └── brief_agent.py    # Generates visual asset specs
│   ├── routes/
│   │   ├── brand_kit.py      # CRUD for brand kit
│   │   ├── runs.py           # Start run, list runs, get run output
│   │   └── approve.py        # Approve / reject / request changes
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── main.py
└── frontend/
    ├── app/
    │   ├── setup/            # Brand kit configuration
    │   ├── run/              # New run: paste or upload
    │   └── review/[id]/      # Review + approve outputs
    └── components/
```

---

## Data Model

### `brand_kits`
Configured once, reused across all runs.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `name` | string | e.g. "Acme Corp v2" |
| `voice_tone` | text | Free-text voice and tone description |
| `do_list` | JSON array | Rules to always follow |
| `dont_list` | JSON array | Rules to never break |
| `style_rules` | text | Sentence length, Oxford comma, capitalization, etc. |
| `colors` | JSON | `{"primary": "#1A1A2E", "accent": "#E94560"}` |
| `typography` | JSON | `{"heading": "Söhne", "body": "Inter"}` |
| `logo_url` | string | Path or URL to logo file |
| `created_at` | datetime | — |
| `updated_at` | datetime | — |

### `runs`
One row per PM doc submitted.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `brand_kit_id` | int | FK → brand_kits |
| `input_type` | string | `paste` or `file` |
| `raw_input` | text | Full extracted text of the PM doc |
| `filename` | string | Original filename if uploaded, null if pasted |
| `status` | string | `processing` → `review` → `approved` / `rejected` |
| `created_at` | datetime | — |

### `structured_briefs`
Output of the Orchestrator Agent. One per run. Shown to user before generation begins.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `run_id` | int | FK → runs |
| `product_name` | string | Name of the feature/product |
| `launch_date` | string | Extracted or inferred, null if not found |
| `key_features` | JSON array | `[{"name": "...", "benefit": "...", "differentiator": "..."}]` |
| `target_audience` | text | Who this launch is for |
| `launch_goals` | text | Awareness, signups, upsell, etc. |
| `tone_notes` | text | Launch-specific tone guidance from the doc |
| `created_at` | datetime | — |

### `outputs`
One row per agent output. Two rows per run (copy + brief). Each independently approvable.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `run_id` | int | FK → runs |
| `output_type` | string | `marketing_copy` or `asset_specs` |
| `content` | JSON | See schemas below |
| `status` | string | `draft` → `approved` / `rejected` |
| `feedback` | text | Reviewer's change request notes |
| `created_at` | datetime | — |
| `updated_at` | datetime | — |

**`marketing_copy` content schema:**
```json
{
  "email": {
    "subject": "...",
    "body": "...",
    "alt_subjects": ["...", "...", "..."]
  },
  "landing_page": {
    "headline": "...",
    "subheadline": "...",
    "cta": "..."
  },
  "social": [
    {"platform": "LinkedIn", "copy": "..."},
    {"platform": "Twitter/X", "copy": "..."}
  ],
  "compliance_flags": []
}
```

**`asset_specs` content schema:**
```json
{
  "assets": [
    {
      "name": "Launch Hero Banner",
      "format": "PNG",
      "dimensions": "1920x1080",
      "placement": "Website homepage",
      "notes": "Use primary blue (#1A1A2E), include product screenshot, headline: '...'"
    },
    {
      "name": "LinkedIn Social Card",
      "format": "PNG",
      "dimensions": "1200x627",
      "placement": "LinkedIn post",
      "notes": "Logo top-left, accent color background, short headline only"
    }
  ]
}
```

---

## Agent Designs

### Orchestrator Agent
- **Input:** raw PM doc text + brand kit (for tone reference)
- **Job:** Extract a structured brief. Conservative — marks fields `null` if not clearly stated rather than hallucinating.
- **Output:** populates `structured_briefs`
- **UX note:** output is surfaced to the user as an editable panel before generation begins, so bad extractions can be caught early

### Copy Agent
- **Input:** `structured_brief` + `brand_kit`
- **Job:** Generate all marketing copy variants in one pass — email (subject, body, alt subjects), landing page (headline, subheadline, CTA), social posts per platform
- **Constraints:** must adhere to brand kit voice, do/don't, style rules; surfaces compliance flags for any violations
- **Output:** `marketing_copy` output row

### Brief Agent
- **Input:** `structured_brief` + `brand_kit`
- **Job:** Infer what design assets are needed for this launch (from launch context, goals, and channels mentioned in doc), then specify each asset with name, format, dimensions, placement, and designer notes referencing brand colors, typography, and logo
- **Output:** `asset_specs` output row

---

## UI Flows

### Flow 1: First-Time Setup
```
App home → "No brand kit configured" empty state
  → "Set up brand kit" → form → save → home with "New Run" CTA
```

### Flow 2: Starting a Run
```
"New Run" → toggle [Paste] / [Upload]
  Paste: textarea → Submit
  Upload: drag-and-drop (PDF, DOCX, MD) → Submit

→ Progress screen:
  [1. Reading document ✓] [2. Generating copy...] [3. Generating specs...]
  Steps 2+3 run in parallel and update independently.
  Extracted brief surfaces as editable collapsible panel after step 1.

→ Auto-navigate to Review page when both complete
```

### Flow 3: Review — Happy Path
```
Review page (two panels: Marketing Copy | Asset Specs)
  → Review each section → "Approve"
  → Run status → "Approved"
  → Export: copy to clipboard per section, or download as PDF/MD
```

### Flow 4: Review — Request Changes
```
"Request Changes" on a section → text field appears
  → Type feedback: "Make subject line more urgent, shorten body to 3 paragraphs"
  → Submit → only that section regenerates (agent reruns with brief + feedback)
  → Updated copy replaces old copy inline
  → Approve or request changes again
```
Only the affected output section regenerates. Other outputs are untouched.

### Flow 5: Run History
```
Home → "Past Runs" list
  → Columns: filename/snippet, date, status (Processing / Review / Approved / Rejected)
  → Click row → opens that run's Review page
```

### Flow 6: Brand Kit Edit
```
Settings → Edit brand kit → same form → save
  → Existing approved runs unaffected (used kit at time of run)
  → Future runs use updated kit
```

---

## Key Design Decisions

- **Orchestrator output is user-editable** before generation starts — prevents bad extractions from polluting all downstream copy
- **Parallel generation** — Copy Agent and Brief Agent run concurrently; progress shown independently
- **Surgical regeneration** — "Request Changes" reruns only the affected agent/section, not the whole run
- **Per-output approval** — Marketing copy and asset specs are approved independently; run is fully approved only when both are
- **Single brand kit** — one active brand kit for now; versioning/multiple kits deferred
