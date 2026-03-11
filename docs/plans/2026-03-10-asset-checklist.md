# Interactive Asset Checklist Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive asset checklist to the New Run form so users choose which assets to generate, including a new PR Releases category (press release + fact sheet).

**Architecture:** `enabled_outputs: list[str]` flows from the frontend checkbox state → POST body → `Run.enabled_outputs` DB column → `pipeline.py` which splits the list into copy sections vs asset types → each agent generates only the requested sections. Empty list = backwards-compatible "generate all".

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy (SQLite), Next.js 14 App Router, TypeScript, shadcn/ui Checkbox component.

---

### Task 1: Add `enabled_outputs` column to Run model + schema

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/schemas.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_runs_routes.py`:
```python
def test_create_run_stores_enabled_outputs(client, setup_db):
    bk = client.post("/api/brand-kit", json={"name": "X", "voice_tone": "bold"}).json()
    run = client.post("/api/runs", json={
        "brand_kit_id": bk["id"],
        "raw_input": "test",
        "enabled_outputs": ["email", "hero_image"],
    }).json()
    assert run["enabled_outputs"] == ["email", "hero_image"]
```

**Step 2: Run test to verify it fails**
```bash
cd backend && source venv/bin/activate
pytest tests/test_runs_routes.py::test_create_run_stores_enabled_outputs -v
```
Expected: FAIL — `enabled_outputs` key missing from response.

**Step 3: Add column to `models.py`**

In `Run` class, after the `progress` column:
```python
enabled_outputs = Column(JSON, default=list)
```

**Step 4: Update `schemas.py`**

In `RunCreatePaste`, add:
```python
enabled_outputs: List[str] = []
```

In `RunOut`, add:
```python
enabled_outputs: List[str] = []
```

**Step 5: Run test to verify it passes**
```bash
pytest tests/test_runs_routes.py::test_create_run_stores_enabled_outputs -v
```
Expected: PASS

**Step 6: Run full test suite to check for regressions**
```bash
pytest tests/ -v
```
Expected: all 23 tests pass + 1 new = 24 total

**Step 7: Commit**
```bash
git add backend/models.py backend/schemas.py backend/tests/test_runs_routes.py
git commit -m "feat: add enabled_outputs field to Run model and schema"
```

---

### Task 2: Pass `enabled_outputs` through the run creation routes

**Files:**
- Modify: `backend/routes/runs.py`

**Step 1: Write failing test**

Add to `backend/tests/test_runs_routes.py`:
```python
def test_enabled_outputs_defaults_to_empty(client, setup_db):
    bk = client.post("/api/brand-kit", json={"name": "Y", "voice_tone": "calm"}).json()
    run = client.post("/api/runs", json={
        "brand_kit_id": bk["id"],
        "raw_input": "test",
    }).json()
    assert run["enabled_outputs"] == []
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_runs_routes.py::test_enabled_outputs_defaults_to_empty -v
```

**Step 3: Update `routes/runs.py` paste route**

Replace the `create_run_paste` function body to include `enabled_outputs`:
```python
@router.post("/api/runs", response_model=schemas.RunOut)
async def create_run_paste(req: schemas.RunCreatePaste, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = models.Run(
        brand_kit_id=req.brand_kit_id,
        input_type="paste",
        raw_input=req.raw_input,
        enabled_outputs=req.enabled_outputs,
        status="processing",
        progress={"orchestrator": "pending", "copy_agent": "pending", "brief_agent": "pending"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(run_pipeline, run.id)
    return run
```

**Step 4: Update upload route — add `enabled_outputs` as JSON form field**

Replace `create_run_upload` signature and body:
```python
@router.post("/api/runs/upload", response_model=schemas.RunOut)
async def create_run_upload(
    background_tasks: BackgroundTasks,
    brand_kit_id: int = Form(...),
    enabled_outputs: str = Form(default="[]"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    import json as _json
    content = await file.read()
    raw_input = file_extractor.extract_text_from_bytes(content, file.filename)
    try:
        enabled_list = _json.loads(enabled_outputs)
    except Exception:
        enabled_list = []
    run = models.Run(
        brand_kit_id=brand_kit_id,
        input_type="file",
        raw_input=raw_input,
        filename=file.filename,
        enabled_outputs=enabled_list,
        status="processing",
        progress={"orchestrator": "pending", "copy_agent": "pending", "brief_agent": "pending"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(run_pipeline, run.id)
    return run
```

**Step 5: Run tests**
```bash
pytest tests/ -v
```
Expected: all pass

**Step 6: Commit**
```bash
git add backend/routes/runs.py backend/tests/test_runs_routes.py
git commit -m "feat: store enabled_outputs on run creation (paste + upload)"
```

---

### Task 3: Update `copy_agent.py` to accept `enabled_sections` + add PR outputs

**Files:**
- Modify: `backend/agents/copy_agent.py`
- Modify: `backend/tests/test_copy_agent.py`

**Step 1: Write failing test**

Add to `backend/tests/test_copy_agent.py`:
```python
@pytest.mark.asyncio
async def test_copy_agent_only_generates_selected_sections():
    brief = {"product_name": "TestProd", "launch_date": "2026-04-01",
             "key_features": [{"name": "F1", "benefit": "B1", "differentiator": "D1"}],
             "target_audience": "developers", "launch_goals": "signups", "tone_notes": ""}
    brand_kit = {"name": "TB", "voice_tone": "bold", "do_list": [], "dont_list": [],
                 "style_rules": "", "colors": {}, "typography": {}, "logo_url": ""}
    result = await run_copy_agent(brief, brand_kit, enabled_sections=["email"])
    assert "email" in result
    assert "landing_page" not in result
    assert "social" not in result

@pytest.mark.asyncio
async def test_copy_agent_generates_press_release():
    brief = {"product_name": "TestProd", "launch_date": "2026-04-01",
             "key_features": [{"name": "F1", "benefit": "B1", "differentiator": "D1"}],
             "target_audience": "developers", "launch_goals": "signups", "tone_notes": ""}
    brand_kit = {"name": "TB", "voice_tone": "bold", "do_list": [], "dont_list": [],
                 "style_rules": "", "colors": {}, "typography": {}, "logo_url": ""}
    result = await run_copy_agent(brief, brand_kit, enabled_sections=["press_release"])
    assert "press_release" in result
    assert "headline" in result["press_release"]
    assert "body" in result["press_release"]
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_copy_agent.py -v
```
Expected: FAIL — `run_copy_agent` doesn't accept `enabled_sections`

**Step 3: Rewrite `copy_agent.py`**

Replace the entire file content:
```python
import json
from anthropic import AsyncAnthropic

client = AsyncAnthropic()
MODEL = "claude-opus-4-6"

ALL_COPY_SECTIONS = {
    "email": {"subject": "Primary subject line", "body": "Full email body (3-4 paragraphs, CTA at end)", "alt_subjects": ["alt 1", "alt 2", "alt 3"]},
    "landing_page": {"headline": "Hero headline (under 10 words)", "subheadline": "Supporting subheadline (1-2 sentences)", "cta": "CTA button text"},
    "social": [{"platform": "LinkedIn", "copy": "..."}, {"platform": "Twitter/X", "copy": "..."}],
    "press_release": {"headline": "Press release headline", "body": "Full press release (400-600 words, inverted pyramid structure)", "boilerplate": "About [Company] boilerplate paragraph"},
    "fact_sheet": {"company": "Company name", "product": "Product name and one-line description", "key_facts": ["fact 1", "fact 2", "fact 3"], "contact": "Press contact name and email"},
    "compliance_flags": ["any brand violations, empty if none"],
}

# Which keys require a brand-kit compliance check (always included if any copy is requested)
ALWAYS_INCLUDE = {"compliance_flags"}

async def run_copy_agent(brief: dict, brand_kit: dict, feedback: str = "", enabled_sections: list = None) -> dict:
    # Default: generate all sections except PR ones (backwards compat)
    if enabled_sections is None:
        enabled_sections = ["email", "landing_page", "social", "compliance_flags"]

    # Always include compliance_flags if generating any copy
    sections_to_generate = list(set(enabled_sections) | ALWAYS_INCLUDE)

    schema = {k: ALL_COPY_SECTIONS[k] for k in sections_to_generate if k in ALL_COPY_SECTIONS}

    system = f"""You are a marketing copywriter. Write release-ready copy for this launch.
BRAND KIT — {brand_kit["name"]}
Voice & Tone: {brand_kit["voice_tone"]}
DO: {", ".join(brand_kit.get("do_list", []))}
DON'T: {", ".join(brand_kit.get("dont_list", []))}
Style: {brand_kit.get("style_rules", "")}
Return ONLY valid JSON matching the schema. No markdown."""

    user_prompt = f"""Generate marketing copy for this launch:
Product: {brief["product_name"]}
Launch Date: {brief.get("launch_date", "TBD")}
Target Audience: {brief["target_audience"]}
Key Features: {json.dumps(brief["key_features"], indent=2)}
Launch Goals: {brief["launch_goals"]}
Tone Notes: {brief.get("tone_notes", "")}
{f"Reviewer feedback to address: {feedback}" if feedback else ""}

Schema:
{json.dumps(schema, indent=2)}"""

    response = await client.messages.create(
        model=MODEL, max_tokens=10000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError("Copy agent response was truncated (max_tokens reached).")

    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
```

**Step 4: Run tests**
```bash
pytest tests/test_copy_agent.py -v
```
Expected: all pass (including the 2 new tests)

**Step 5: Commit**
```bash
git add backend/agents/copy_agent.py backend/tests/test_copy_agent.py
git commit -m "feat: copy_agent accepts enabled_sections, adds press_release and fact_sheet"
```

---

### Task 4: Update `brief_agent.py` to accept `enabled_asset_types`

**Files:**
- Modify: `backend/agents/brief_agent.py`
- Modify: `backend/tests/test_brief_agent.py`

**Step 1: Write failing test**

Add to `backend/tests/test_brief_agent.py`:
```python
@pytest.mark.asyncio
async def test_brief_agent_only_generates_selected_types():
    brief = {"product_name": "TestProd", "launch_date": "2026-04-01",
             "key_features": [{"name": "F1", "benefit": "B1", "differentiator": "D1"}],
             "target_audience": "developers", "launch_goals": "signups"}
    brand_kit = {"name": "TB", "voice_tone": "bold", "colors": {}, "typography": {}, "logo_url": ""}
    result = await run_brief_agent(brief, brand_kit, enabled_asset_types=["hero_image"])
    assets = result.get("assets", [])
    assert len(assets) >= 1
    # All returned assets should be hero_image type
    names = [a.get("name", "").lower() for a in assets]
    assert any("hero" in n for n in names)
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_brief_agent.py -v
```
Expected: FAIL — `run_brief_agent` doesn't accept `enabled_asset_types`

**Step 3: Update `brief_agent.py`** — add `enabled_asset_types` parameter

Replace the `run_brief_agent` function signature and the user_prompt construction:
```python
async def run_brief_agent(brief: dict, brand_kit: dict, feedback: str = "", enabled_asset_types: list = None) -> dict:
    asset_type_instruction = ""
    if enabled_asset_types:
        asset_type_instruction = f"\nOnly generate specs for these asset types: {', '.join(enabled_asset_types)}. Do not add other asset types."
```

Add `{asset_type_instruction}` to the user_prompt after the Schema section.

Full updated function signature (keep the rest of the function body the same, just add the parameter and inject the instruction):
```python
async def run_brief_agent(brief: dict, brand_kit: dict, feedback: str = "", enabled_asset_types: list = None) -> dict:
    asset_type_instruction = ""
    if enabled_asset_types:
        asset_type_instruction = f"\nOnly generate specs for these asset types: {', '.join(enabled_asset_types)}. Do not add other asset types."

    system = f"""You are a creative producer. Specify exactly what design assets a designer needs for this product launch.
Infer assets from the launch goals and channels mentioned. Be precise — designers act on these specs directly.
Brand colors: {json.dumps(brand_kit.get("colors", {}))}
Typography: {json.dumps(brand_kit.get("typography", {}))}
Logo: {brand_kit.get("logo_url", "not provided")}
Return ONLY valid JSON matching the schema. No markdown."""

    user_prompt = f"""Generate asset specs for this launch:
Product: {brief["product_name"]}
Target Audience: {brief["target_audience"]}
Launch Goals: {brief["launch_goals"]}
Key Features: {json.dumps(brief["key_features"], indent=2)}
{f"Reviewer feedback to address: {feedback}" if feedback else ""}
{asset_type_instruction}

Schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}"""

    response = await client.messages.create(
        model=MODEL, max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError("Brief agent response was truncated (max_tokens reached).")

    raw_text = next((b.text for b in response.content if b.type == "text"), "")
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw_text)
```

**Step 4: Run tests**
```bash
pytest tests/test_brief_agent.py -v
```
Expected: all pass

**Step 5: Commit**
```bash
git add backend/agents/brief_agent.py backend/tests/test_brief_agent.py
git commit -m "feat: brief_agent accepts enabled_asset_types to scope generated assets"
```

---

### Task 5: Update `pipeline.py` to route `enabled_outputs` to agents

**Files:**
- Modify: `backend/pipeline.py`
- Modify: `backend/tests/test_pipeline.py`

**Constants for splitting the list (add near top of pipeline.py):**
```python
COPY_SECTIONS = {"email", "landing_page", "social", "press_release", "fact_sheet", "compliance_flags"}
ASSET_TYPES = {"hero_image", "social_graphics", "email_header", "feature_illustrations", "media_kit_specs"}
```

**Step 1: Write failing test**

Add to `backend/tests/test_pipeline.py`:
```python
@pytest.mark.asyncio
async def test_pipeline_respects_enabled_outputs(db_session):
    from unittest.mock import AsyncMock, patch
    bk = models.BrandKit(name="T", voice_tone="bold")
    db_session.add(bk); db_session.commit(); db_session.refresh(bk)
    run = models.Run(brand_kit_id=bk.id, input_type="paste", raw_input="test",
                     enabled_outputs=["email"], status="processing",
                     progress={"orchestrator": "pending", "copy_agent": "pending", "brief_agent": "pending"})
    db_session.add(run); db_session.commit(); db_session.refresh(run)

    with patch("pipeline.run_orchestrator", new=AsyncMock(return_value={
        "product_name": "P", "launch_date": None, "key_features": [],
        "target_audience": "devs", "launch_goals": "signups", "tone_notes": ""
    })), patch("pipeline.run_copy_agent", new=AsyncMock(return_value={"email": {}})) as mock_copy, \
         patch("pipeline.run_brief_agent", new=AsyncMock(return_value={"assets": []})) as mock_brief:
        await run_pipeline(run.id)

    # copy_agent should be called with enabled_sections=["email", "compliance_flags"]
    call_kwargs = mock_copy.call_args.kwargs
    assert "email" in call_kwargs.get("enabled_sections", [])
    # brief_agent should be called with empty enabled_asset_types (no asset types selected)
    brief_kwargs = mock_brief.call_args.kwargs
    assert brief_kwargs.get("enabled_asset_types") == []
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_pipeline.py::test_pipeline_respects_enabled_outputs -v
```

**Step 3: Update `pipeline.py`**

Add the constants and update `run_pipeline` to split and pass the selections:
```python
import asyncio
import logging
from database import SessionLocal
import models
from agents.orchestrator import run_orchestrator
from agents.copy_agent import run_copy_agent
from agents.brief_agent import run_brief_agent

logger = logging.getLogger(__name__)

COPY_SECTIONS = {"email", "landing_page", "social", "press_release", "fact_sheet", "compliance_flags"}
ASSET_TYPES = {"hero_image", "social_graphics", "email_header", "feature_illustrations", "media_kit_specs"}

async def run_pipeline(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(models.Run).filter(models.Run.id == run_id).first()
        brand_kit = db.query(models.BrandKit).filter(models.BrandKit.id == run.brand_kit_id).first()

        enabled = run.enabled_outputs or []
        # Empty list = backwards compat = generate all defaults
        if not enabled:
            copy_sections = list(COPY_SECTIONS - {"press_release", "fact_sheet"})
            asset_types = list(ASSET_TYPES)
        else:
            copy_sections = [s for s in enabled if s in COPY_SECTIONS]
            asset_types = [s for s in enabled if s in ASSET_TYPES]
            # Always include compliance_flags if any copy is requested
            if copy_sections and "compliance_flags" not in copy_sections:
                copy_sections.append("compliance_flags")

        run.progress = {"orchestrator": "running", "copy_agent": "pending", "brief_agent": "pending"}
        db.commit()

        brief_data = await run_orchestrator(run.raw_input, brand_kit_name=brand_kit.name, voice_tone=brand_kit.voice_tone or "")

        db.add(models.StructuredBrief(run_id=run_id, **brief_data))
        run.progress = {"orchestrator": "done", "copy_agent": "running", "brief_agent": "running"}
        db.commit()

        brand_kit_dict = {
            "name": brand_kit.name, "voice_tone": brand_kit.voice_tone or "",
            "do_list": brand_kit.do_list or [], "dont_list": brand_kit.dont_list or [],
            "style_rules": brand_kit.style_rules or "", "colors": brand_kit.colors or {},
            "typography": brand_kit.typography or {}, "logo_url": brand_kit.logo_url or "",
        }

        tasks = []
        if copy_sections:
            tasks.append(run_copy_agent(brief_data, brand_kit_dict, enabled_sections=copy_sections))
        if asset_types:
            tasks.append(run_brief_agent(brief_data, brand_kit_dict, enabled_asset_types=asset_types))

        results = await asyncio.gather(*tasks)

        result_idx = 0
        if copy_sections:
            db.add(models.Output(run_id=run_id, output_type="marketing_copy", content=results[result_idx]))
            result_idx += 1
        if asset_types:
            db.add(models.Output(run_id=run_id, output_type="asset_specs", content=results[result_idx]))

        run.status = "review"
        run.progress = {"orchestrator": "done", "copy_agent": "done", "brief_agent": "done"}
        db.commit()

    except Exception as e:
        logger.error(f"Pipeline failed for run {run_id}: {e}")
        run = db.query(models.Run).filter(models.Run.id == run_id).first()
        if run:
            run.status = "rejected"
            run.progress = {**run.progress, "error": str(e)}
            db.commit()
    finally:
        db.close()


async def regenerate_output(output_id: int, feedback: str):
    db = SessionLocal()
    try:
        output = db.query(models.Output).filter(models.Output.id == output_id).first()
        run = db.query(models.Run).filter(models.Run.id == output.run_id).first()
        brief = db.query(models.StructuredBrief).filter(models.StructuredBrief.run_id == run.id).first()
        brand_kit = db.query(models.BrandKit).filter(models.BrandKit.id == run.brand_kit_id).first()

        enabled = run.enabled_outputs or []
        copy_sections = [s for s in enabled if s in COPY_SECTIONS] if enabled else None
        asset_types = [s for s in enabled if s in ASSET_TYPES] if enabled else None

        brand_kit_dict = {
            "name": brand_kit.name, "voice_tone": brand_kit.voice_tone or "",
            "do_list": brand_kit.do_list or [], "dont_list": brand_kit.dont_list or [],
            "style_rules": brand_kit.style_rules or "", "colors": brand_kit.colors or {},
            "typography": brand_kit.typography or {}, "logo_url": brand_kit.logo_url or "",
        }
        brief_data = {"product_name": brief.product_name, "launch_date": brief.launch_date,
                      "key_features": brief.key_features, "target_audience": brief.target_audience,
                      "launch_goals": brief.launch_goals, "tone_notes": brief.tone_notes}

        output.status = "draft"
        db.commit()

        if output.output_type == "marketing_copy":
            result = await run_copy_agent(brief_data, brand_kit_dict, feedback=feedback,
                                          enabled_sections=copy_sections)
        else:
            result = await run_brief_agent(brief_data, brand_kit_dict, feedback=feedback,
                                           enabled_asset_types=asset_types)

        output.content = result
        output.feedback = None
        db.commit()
    except Exception as e:
        logger.error(f"Regeneration failed for output {output_id}: {e}")
    finally:
        db.close()
```

**Step 4: Run full test suite**
```bash
pytest tests/ -v
```
Expected: all tests pass

**Step 5: Commit**
```bash
git add backend/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat: pipeline routes enabled_outputs to copy_agent and brief_agent"
```

---

### Task 6: Add `AssetChecklist` to `RunForm.tsx`

**Files:**
- Modify: `frontend/components/RunForm.tsx`

No new test file needed (UI component; tested visually via preview).

**Step 1: Install shadcn Checkbox** (if not already installed)
```bash
cd frontend && npx shadcn@latest add checkbox
```

**Step 2: Replace `RunForm.tsx` with the version below**

```tsx
"use client";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CHECKLIST = [
  {
    category: "PR Releases",
    items: [
      { key: "press_release", label: "Press release draft", defaultChecked: false },
      { key: "fact_sheet", label: "Fact sheet / media brief", defaultChecked: false },
      { key: "media_kit_specs", label: "Media kit asset specs", defaultChecked: false },
    ],
  },
  {
    category: "Marketing Copy",
    items: [
      { key: "email", label: "Email copy (subject + body)", defaultChecked: true },
      { key: "landing_page", label: "Landing page copy", defaultChecked: true },
      { key: "social", label: "Social posts (LinkedIn, Twitter/X)", defaultChecked: true },
    ],
  },
  {
    category: "Design Assets",
    items: [
      { key: "hero_image", label: "Hero image spec", defaultChecked: true },
      { key: "social_graphics", label: "Social media graphics spec", defaultChecked: true },
      { key: "email_header", label: "Email header graphic spec", defaultChecked: false },
      { key: "feature_illustrations", label: "Feature illustrations spec", defaultChecked: false },
    ],
  },
];

const DEFAULT_ENABLED = CHECKLIST.flatMap(c => c.items.filter(i => i.defaultChecked).map(i => i.key));

interface Props { brandKitId: number; onRunCreated: (id: number) => void; }

export function RunForm({ brandKitId, onRunCreated }: Props) {
  const [pasteText, setPasteText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [enabledOutputs, setEnabledOutputs] = useState<string[]>(DEFAULT_ENABLED);
  const fileRef = useRef<HTMLInputElement>(null);

  const toggleOutput = (key: string) => {
    setEnabledOutputs(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  const submitPaste = async () => {
    setSubmitting(true); setError("");
    try {
      const run = await apiFetch<{ id: number }>("/api/runs", {
        method: "POST",
        body: JSON.stringify({ brand_kit_id: brandKitId, raw_input: pasteText, enabled_outputs: enabledOutputs }),
      });
      onRunCreated(run.id);
    } catch (err: any) { setError(err.message); setSubmitting(false); }
  };

  const submitFile = async () => {
    if (!file) return;
    setSubmitting(true); setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("brand_kit_id", String(brandKitId));
      fd.append("enabled_outputs", JSON.stringify(enabledOutputs));
      const res = await fetch(`${API}/api/runs/upload`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Upload failed");
      const run = await res.json();
      onRunCreated(run.id);
    } catch (err: any) { setError(err.message); setSubmitting(false); }
  };

  return (
    <div className="space-y-8">
      <Tabs defaultValue="paste">
        <TabsList><TabsTrigger value="paste">Paste Text</TabsTrigger><TabsTrigger value="upload">Upload File</TabsTrigger></TabsList>
        <TabsContent value="paste" className="space-y-4">
          <p className="text-sm text-muted-foreground">Paste your PM launch notes, PRD, or any product document.</p>
          <Textarea value={pasteText} onChange={e => setPasteText(e.target.value)} rows={16} placeholder="# Feature Launch&#10;&#10;Paste your PM document here..." />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button onClick={submitPaste} disabled={submitting || !pasteText.trim() || enabledOutputs.length === 0}>
            {submitting ? "Submitting..." : "Generate Assets"}
          </Button>
        </TabsContent>
        <TabsContent value="upload" className="space-y-4">
          <p className="text-sm text-muted-foreground">Upload a PDF, Word doc (.docx), or Markdown file.</p>
          <div className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:bg-muted/50" onClick={() => fileRef.current?.click()}>
            {file ? <p className="font-medium">{file.name}</p> : <p className="text-muted-foreground">Drop a file or click to browse</p>}
            <input ref={fileRef} type="file" accept=".pdf,.docx,.md,.txt" className="hidden" onChange={e => setFile(e.target.files?.[0] ?? null)} />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button onClick={submitFile} disabled={submitting || !file || enabledOutputs.length === 0}>
            {submitting ? "Uploading..." : "Generate Assets"}
          </Button>
        </TabsContent>
      </Tabs>

      {/* Asset Checklist */}
      <div className="space-y-4">
        <div>
          <h2 className="text-base font-semibold">Select assets to generate</h2>
          <p className="text-sm text-muted-foreground">Only checked items will be generated by the AI pipeline.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {CHECKLIST.map(group => (
            <div key={group.category} className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{group.category}</h3>
              {group.items.map(item => (
                <div key={item.key} className="flex items-center gap-2">
                  <Checkbox
                    id={item.key}
                    checked={enabledOutputs.includes(item.key)}
                    onCheckedChange={() => toggleOutput(item.key)}
                  />
                  <Label htmlFor={item.key} className="text-sm font-normal cursor-pointer">{item.label}</Label>
                </div>
              ))}
            </div>
          ))}
        </div>
        {enabledOutputs.length === 0 && (
          <p className="text-sm text-red-500">Select at least one asset to generate.</p>
        )}
      </div>
    </div>
  );
}
```

**Step 3: Verify in browser**

Start servers if needed. Navigate to `http://localhost:3000/run`. Confirm:
- Checklist with 3 columns renders below the paste/upload tabs
- PR Releases items unchecked by default, Marketing + Design pre-checked
- Toggling a checkbox updates the checked state
- "Generate Assets" button is disabled when nothing is checked

**Step 4: Commit**
```bash
git add frontend/components/RunForm.tsx
git commit -m "feat: add interactive asset checklist to RunForm with 3 categories"
```

---

### Task 7: Update `MarketingCopyPanel.tsx` to render PR Releases sections

**Files:**
- Modify: `frontend/components/MarketingCopyPanel.tsx`

**Step 1: Add conditional sections for `press_release` and `fact_sheet`**

After the existing Social section, add:
```tsx
{c.press_release && (
  <section className="space-y-2">
    <h3 className="font-medium text-sm uppercase text-muted-foreground">Press Release</h3>
    <div className="border rounded-lg p-4 space-y-2">
      <p className="font-medium">{c.press_release.headline}</p>
      <p className="text-sm whitespace-pre-wrap">{c.press_release.body}</p>
      {c.press_release.boilerplate && (
        <p className="text-xs text-muted-foreground border-t pt-2 mt-2">{c.press_release.boilerplate}</p>
      )}
    </div>
  </section>
)}
{c.fact_sheet && (
  <section className="space-y-2">
    <h3 className="font-medium text-sm uppercase text-muted-foreground">Fact Sheet</h3>
    <div className="border rounded-lg p-4 space-y-2">
      <p><span className="font-medium">Company:</span> {c.fact_sheet.company}</p>
      <p><span className="font-medium">Product:</span> {c.fact_sheet.product}</p>
      {c.fact_sheet.key_facts?.length > 0 && (
        <ul className="text-sm list-disc list-inside space-y-1">
          {c.fact_sheet.key_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
        </ul>
      )}
      {c.fact_sheet.contact && <p className="text-sm text-muted-foreground">Contact: {c.fact_sheet.contact}</p>}
    </div>
  </section>
)}
```

**Step 2: Verify in browser**

Run a test with `press_release` and `fact_sheet` checked. Confirm the new sections appear on the review page after generation.

**Step 3: Commit**
```bash
git add frontend/components/MarketingCopyPanel.tsx
git commit -m "feat: render press_release and fact_sheet sections in MarketingCopyPanel"
```

---

### Task 8: Push to GitHub

```bash
git push origin main
```

Confirm push succeeds at `https://github.com/Rohitks00/pm-launch-agent`.

---

## Verification Checklist

- [ ] All 24+ backend tests pass: `pytest tests/ -v`
- [ ] New Run page shows 3-column checklist below the form
- [ ] PR Releases items unchecked by default; Marketing Copy + hero/social checked
- [ ] Submit with only "Email" checked → only email output on review page
- [ ] Submit with "Press release" checked → press release section appears on review page
- [ ] Existing runs without `enabled_outputs` still work (backwards compat)
- [ ] "Generate Assets" disabled when no items checked
