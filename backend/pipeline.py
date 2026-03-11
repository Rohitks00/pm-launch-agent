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
        # Empty list = backwards compat = generate all defaults (no PR sections)
        if not enabled:
            copy_sections = ["email", "landing_page", "social"]
            asset_types = list(ASSET_TYPES)
        else:
            copy_sections = [s for s in enabled if s in COPY_SECTIONS]
            asset_types = [s for s in enabled if s in ASSET_TYPES]
            # Always include compliance_flags when generating any copy
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
