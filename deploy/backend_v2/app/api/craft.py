import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    CraftChapterRequest, CraftTitlesRequest, CraftDescriptionsRequest,
    CraftReportRequest
)
from app.services.novel_generator import get_generator, parse_style_profile
from app.services import validate_ai_config

router = APIRouter()





@router.post("/api/novel/craft/chapter")
async def craft_chapter(body: dict):
    if body.get('stream'):
        cfg = validate_ai_config(body)
        if not cfg:
            return {"error": "缺少AI配置参数"}
        gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
        style = parse_style_profile(body.get('styleProfile', ''))

        def event_stream():
            yield f"data: {json.dumps({'content': ''}, ensure_ascii=False)}\n\n"
            for chunk in gen.generate_chapter_craft_stream(
                project_title=body.get('projectTitle', ''),
                genre=body.get('genre', ''),
                chapter_number=body.get('chapterNumber', 1),
                chapter_title=body.get('chapterTitle', ''),
                chapter_outline=body.get('chapterOutline', ''),
                continuation_point=body.get('continuationPoint', ''),
                previous_chapter_summary=body.get('previousChapterSummary', ''),
                chapter_characters=body.get('chapterCharacters', ''),
                foreshadow_reminders=body.get('foreshadowReminders', ''),
                world_summary=body.get('worldSummary', ''),
                first_chapter_strategy=body.get('firstChapterStrategy', ''),
                target_word_count=body.get('targetWordCount', 3000),
                narrative_perspective=body.get('narrativePerspective', '第三人称'),
                style_profile=style,
                technique_focus=body.get("techniqueFocus", ""),
                book_overview=body.get("bookOverview", ""),
                progress_content=body.get('progressContent', ''),
                segment_chars=int(body.get('segmentChars', 0)),
                prev_chapter_hook=body.get('prevChapterHook', ''),
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "Connection": "close",
            "X-Accel-Buffering": "no"
        })

    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_chapter_craft(
        project_title=body.get('projectTitle', ''),
        genre=body.get('genre', ''),
        chapter_number=body.get('chapterNumber', 1),
        chapter_title=body.get('chapterTitle', ''),
        chapter_outline=body.get('chapterOutline', ''),
        continuation_point=body.get('continuationPoint', ''),
        previous_chapter_summary=body.get('previousChapterSummary', ''),
        chapter_characters=body.get('chapterCharacters', ''),
        foreshadow_reminders=body.get('foreshadowReminders', ''),
        world_summary=body.get('worldSummary', ''),
        first_chapter_strategy=body.get('firstChapterStrategy', ''),
        target_word_count=body.get('targetWordCount', 3000),
        narrative_perspective=body.get('narrativePerspective', '第三人称'),
        style_profile=style,
        technique_focus=body.get("techniqueFocus", ""),
        book_overview=body.get("bookOverview", ""),
        prev_chapter_hook=body.get('prevChapterHook', ''),
    )
    if err:
        return {"error": err}
    return {"content": result}


@router.post("/api/novel/craft/titles")
async def craft_titles(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.generate_titles_craft(body.get('userInput', ''))
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/craft/descriptions")
async def craft_descriptions(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.generate_descriptions_craft(body.get('title', ''), body.get('userInput', ''))
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/craft/report")
async def craft_report(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.generate_analysis_report(body.get('content', ''))
    if err:
        return {"error": err}
    return {"report": result}


@router.post("/api/novel/craft/detect-ai")
async def craft_detect_ai(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.detect_ai_flavor(body.get('content', ''))
    if err:
        return {"error": err}
    if result is None:
        return {"error": "生成结果为空，请重试"}
    return result


@router.post("/api/novel/craft/fix-ai")
async def craft_fix_ai(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.fix_ai_flavor(body.get('content', ''), body.get('issues', []))
    if err:
        return {"error": err}
    return {"content": result}


@router.post("/api/novel/craft/golden-three")
async def craft_golden_three(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.analyze_golden_three(body.get('content', ''))
    if err:
        return {"error": err}
    if result is None:
        return {"error": "生成结果为空，请重试"}
    return result


@router.post("/api/novel/craft/quality-score")
async def craft_quality_score(body: dict):
    cfg = validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    result, err = gen.quality_score(body.get('content', ''), body.get('title', ''), body.get('genre', ''))
    if err:
        return {"error": err}
    if result is None:
        return {"error": "生成结果为空，请重试"}
    return result
