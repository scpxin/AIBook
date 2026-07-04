from fastapi import APIRouter
from app.models.schemas import StepSummarySaveRequest, StepSummaryGetRequest
from app.database import novel_db

router = APIRouter()


@router.post("/api/step-summary/save")
async def step_summary_save(body: StepSummarySaveRequest):
    summary = body.summary if isinstance(body.summary, dict) else body.summary
    novel_db.save_step_summary(body.projectId, body.step, summary)
    return {"ok": True}


@router.post("/api/step-summary/get")
async def step_summary_get(body: dict):
    project_id = body.get('projectId', '')
    step = body.get('step')
    if not project_id:
        return {"error": "缺少 projectId"}
    if step:
        summary = novel_db.get_step_summary(project_id, step)
        return {"summaries": {step: summary or {}}}
    else:
        summaries = novel_db.get_all_step_summaries(project_id)
        result = {}
        for s in summaries:
            result[s['step']] = s.get('summary_json', {})
        return {"summaries": result}
