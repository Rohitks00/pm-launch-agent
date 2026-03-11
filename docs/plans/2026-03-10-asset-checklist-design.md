# Design: Interactive Asset Checklist on New Run Page

**Date:** 2026-03-10
**Status:** Approved

---

## Problem

Users currently have no control over which assets are generated. Every run produces all outputs (email, landing page, social posts, design asset specs). There is no PR releases output type. Users can't skip categories they don't need, which wastes API calls and clutters the review page.

## Solution

Add an interactive asset checklist to the New Run form. Users select which asset categories to generate before submitting. The selection is sent to the backend; agents only generate what was requested. A new **PR Releases** category is added as a first-class output type.

---

## Checklist Layout (3 columns)

```
┌─────────────────────┬─────────────────────┬──────────────────────┐
│ PR RELEASES         │ MARKETING COPY       │ DESIGN ASSETS        │
│ ☐ Press release     │ ☑ Email copy         │ ☑ Hero image spec    │
│ ☐ Fact sheet        │ ☑ Landing page copy  │ ☑ Social graphics    │
│ ☐ Media kit specs   │ ☑ Social posts       │ ☐ Email header spec  │
│                     │                      │ ☐ Feature illus.     │
└─────────────────────┴─────────────────────┴──────────────────────┘
```

Defaults: Marketing Copy + Hero image + Social graphics pre-checked. PR Releases unchecked.

---

## Asset Key Names

| Key | Category | Label | Default |
|-----|----------|-------|---------|
| `press_release` | PR Releases | Press release draft | off |
| `fact_sheet` | PR Releases | Fact sheet / media brief | off |
| `media_kit_specs` | PR Releases | Media kit asset specs | off |
| `email` | Marketing Copy | Email copy (subject + body) | **on** |
| `landing_page` | Marketing Copy | Landing page copy | **on** |
| `social_posts` | Marketing Copy | Social posts (LinkedIn, Twitter/X) | **on** |
| `hero_image` | Design Assets | Hero image spec | **on** |
| `social_graphics` | Design Assets | Social media graphics spec | **on** |
| `email_header` | Design Assets | Email header graphic spec | off |
| `feature_illustrations` | Design Assets | Feature illustrations spec | off |

---

## Data Flow

```
New Run form
  → user checks/unchecks items
  → POST /api/runs { raw_input, brand_kit_id, enabled_outputs: [...keys] }
  → backend stores enabled_outputs on Run record
  → pipeline.py reads enabled_outputs
    → copy_agent gets enabled_copy_sections (email, landing_page, social_posts, press_release, fact_sheet)
    → brief_agent gets enabled_asset_types (hero_image, social_graphics, email_header, feature_illustrations, media_kit_specs)
  → agents generate ONLY the requested sections
  → review page shows only panels for output types that were generated
```

---

## Backend Changes

### 1. Database – `runs` table
Add column: `enabled_outputs TEXT` (JSON array, nullable — existing rows default to all outputs).

### 2. `POST /api/runs` request schema
Add optional field: `enabled_outputs: list[str] = []` (empty list = generate all, for backwards compatibility).

### 3. `copy_agent.py`
- Accept `enabled_sections: list[str]` parameter
- Build output schema dynamically: only include email/landing_page/social/press_release/fact_sheet keys that are in `enabled_sections`
- Press release schema: `{"headline": "...", "body": "...", "boilerplate": "..."}`
- Fact sheet schema: `{"company": "...", "product": "...", "key_facts": [...], "contact": "..."}`

### 4. `brief_agent.py`
- Accept `enabled_asset_types: list[str]` parameter
- Prompt instructs agent to only generate specs for the requested asset types

### 5. `pipeline.py`
- Split `enabled_outputs` into copy sections vs asset types
- Pass to respective agents

---

## Frontend Changes

### 1. `RunForm.tsx`
- Add `AssetChecklist` section below the document input
- Each item is a `<Checkbox>` with label, grouped under a category header
- State: `enabledOutputs: string[]` initialized from defaults
- On submit: include `enabled_outputs` in POST body

### 2. `MarketingCopyPanel.tsx`
- Only render Email/Landing Page/Social/Press Release/Fact Sheet sections if that key exists in the output content

### 3. `AssetSpecsPanel.tsx`
- No change needed — already renders whatever assets the agent returned

### 4. `review/[id]/page.tsx`
- No change needed — already renders whichever output panels exist

---

## Backwards Compatibility

- Existing runs with `enabled_outputs = null` → treat as "all outputs enabled"
- `POST /api/runs` with no `enabled_outputs` field → generate all (same as before)

---

## Out of Scope

- Per-run re-selection of outputs after generation (would require new UI)
- Saving checklist preferences as user defaults (no auth system yet)
