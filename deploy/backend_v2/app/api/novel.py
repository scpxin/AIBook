import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    NovelInspirationRequest, WorldbuildingRequest, CharactersRequest,
    OutlineRequest, BookOverviewRequest, ChapterOutlineRequest,
    ChapterRequest, ChapterPolishRequest, ChapterSummarizeRequest,
    WorldbuildingReparseRequest, CharactersReparseRequest
)
from app.services.novel_generator import get_generator, parse_style_profile, send_gen_result
from app.database import novel_db

router = APIRouter()


def _validate_ai_config(body: dict):
    endpoint = body.get('endpoint', '')
    api_key = body.get('apiKey', '')
    model = body.get('model', '')
    if not all([endpoint, api_key, model]):
        return None
    return {'endpoint': endpoint, 'api_key': api_key, 'model': model}


@router.post("/api/novel/inspiration/title")
async def inspiration_title(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_titles(user_input=body.get('userInput', ''), style_profile=style)
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/inspiration/description")
async def inspiration_description(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_descriptions(body.get('title', ''), user_input=body.get('userInput', ''), style_profile=style)
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/inspiration/theme")
async def inspiration_theme(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_themes(body.get('title', ''), body.get('description', ''), user_input=body.get('userInput', ''), style_profile=style)
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/inspiration/genre")
async def inspiration_genre(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_genres(body.get('title', ''), body.get('description', ''), user_input=body.get('userInput', ''), style_profile=style)
    if err:
        return {"error": err}
    return {"options": result}


@router.post("/api/novel/worldbuilding")
async def worldbuilding(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_world_building(
        title=body.get('title', ''), theme=body.get('theme', ''),
        genre=body.get('genre', ''), description=body.get('description', ''),
        style_profile=style
    )
    if err:
        return {"error": err}
    for k in ['time_period', 'location', 'atmosphere', 'rules']:
        if k in result and not isinstance(result[k], str):
            result[k] = json.dumps(result[k], ensure_ascii=False) if isinstance(result[k], dict) else str(result[k])
    return {"world": result}


@router.post("/api/novel/characters")
async def characters(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    count = min(int(body.get('count', 6)), 50)
    world_data = body.get('worldData', {})
    if isinstance(world_data, str):
        try:
            world_data = json.loads(world_data)
        except:
            world_data = {'summary': world_data}
    if count > 10:
        result, err = gen.generate_characters_batch(
            world_data=world_data, theme=body.get('theme', ''),
            genre=body.get('genre', ''), count=count,
            requirements=body.get('requirements', ''), style_profile=style,
            description=body.get('novelDescription', '')
        )
        if err:
            return {"error": err}
        return {"characters": result}
    else:
        result, err = gen.generate_characters(
            world_data=world_data, theme=body.get('theme', ''),
            genre=body.get('genre', ''), count=count,
            requirements=body.get('requirements', ''), style_profile=style,
            description=body.get('novelDescription', '')
        )
        if err:
            return {"error": err}
        return {"characters": result}


@router.post("/api/novel/worldbuilding/reparse")
async def worldbuilding_reparse(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.reparse_world_building(world_text=body.get('worldText', ''), style_profile=style)
    if err:
        return {"error": err}
    for k in ['time_period', 'location', 'atmosphere', 'rules']:
        if k in result and not isinstance(result[k], str):
            result[k] = json.dumps(result[k], ensure_ascii=False) if isinstance(result[k], dict) else str(result[k])
    return {"worldJson": result}


@router.post("/api/novel/characters/reparse")
async def characters_reparse(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.reparse_characters(characters_text=body.get('charactersText', ''), style_profile=style)
    if err:
        return {"error": err}
    return {"charactersRaw": result}


@router.post("/api/novel/outline")
async def novel_outline(body: dict):
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    chapter_count = max(1, min(int(body.get('chapterCount', 3)), 200))
    world_summary = body.get('worldSummary', '')
    if not world_summary and body.get('projectId'):
        summaries = novel_db.get_all_step_summaries(body['projectId'])
        summary_map = {s['step']: s.get('summary_json', {}) for s in summaries}
        world = summary_map.get('world', {})
        if world:
            world_summary = world.get('summary_text', '')
    result, err = gen.generate_outline(
        title=body.get('title', ''), theme=body.get('theme', ''),
        genre=body.get('genre', ''), characters_info=body.get('charactersInfo', []),
        chapter_count=chapter_count,
        narrative_perspective=body.get('narrativePerspective', '第三人称'),
        style_profile=style,
        world_summary=world_summary
    )
    if err:
        return {"error": err}
    return {"outline": result}


@router.post("/api/novel/book-overview")
async def book_overview(body: dict):
    if body.get('stream'):
        cfg = _validate_ai_config(body)
        if not cfg:
            return {"error": "缺少AI配置参数"}
        gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
        style = parse_style_profile(body.get('styleProfile', ''))

        def event_stream():
            yield f"data: {json.dumps({'content': ''}, ensure_ascii=False)}\n\n"
            for chunk in gen.generate_book_overview_stream(
                title=body.get('title', ''), theme=body.get('theme', ''),
                genre=body.get('genre', ''),
                characters_info=body.get('charactersInfo', ''),
                narrative_perspective=body.get('narrativePerspective', '第三人称'),
                style_profile=style,
                world_summary=body.get('worldSummary', ''),
                inspiration_desc=body.get('inspirationDesc', '') or body.get('description', '')
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "Connection": "close",
            "X-Accel-Buffering": "no"
        })

    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    project_id = body.get('projectId', '')
    world_summary = body.get('worldSummary', '')
    inspiration_desc = body.get('description', '')
    characters_info = body.get('charactersInfo', '')
    missing_steps = []
    if project_id:
        summaries = novel_db.get_all_step_summaries(project_id)
        summary_map = {s['step']: s.get('summary_json', {}) for s in summaries}
        insp = summary_map.get('inspiration', {})
        world = summary_map.get('world', {})
        chars = summary_map.get('characters', {})
        if not inspiration_desc and insp:
            inspiration_desc = insp.get('description', insp.get('core_premise', ''))
        elif not inspiration_desc:
            missing_steps.append('灵感')
        if not world_summary and world:
            world_summary = world.get('summary_text', '')
            if not world_summary:
                parts = []
                if world.get('key_locations'):
                    parts.append("关键地点: " + ", ".join(world.get('key_locations', [])[:5]))
                if world.get('power_system'):
                    parts.append("体系: " + world.get('power_system', ''))
                world_summary = "; ".join(parts)
        elif not world_summary:
            missing_steps.append('世界观')
        if not characters_info and chars:
            char_names = chars.get('char_names', [])
            if char_names:
                characters_info = ", ".join(char_names)
        elif not characters_info:
            missing_steps.append('角色')
    if missing_steps:
        world_summary = f"[注意：缺少以下步骤的数据：{'/'.join(missing_steps)}，总纲可能不够完整]\n" + world_summary
    result, err = gen.generate_book_overview(
        title=body.get('title', ''), theme=body.get('theme', ''),
        genre=body.get('genre', ''), characters_info=characters_info,
        narrative_perspective=body.get('narrativePerspective', '第三人称'),
        style_profile=style,
        world_summary=world_summary,
        inspiration_desc=inspiration_desc
    )
    if err:
        return {"error": err}
    return {"result": result}


@router.post("/api/novel/chapter-outline")
async def chapter_outline(body: dict):
    if body.get('stream'):
        cfg = _validate_ai_config(body)
        if not cfg:
            return {"error": "缺少AI配置参数"}
        gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
        style = parse_style_profile(body.get('styleProfile', ''))

        def event_stream():
            yield f"data: {json.dumps({'content': ''}, ensure_ascii=False)}\n\n"
            for chunk in gen.generate_chapter_outline_stream(
                project_title=body.get('projectTitle', ''),
                genre=body.get('genre', ''),
                book_overview_json=body.get('bookOverview', ''),
                chapter_number=int(body.get('chapterNumber', 1)),
                total_chapters=int(body.get('totalChapters', 1)),
                characters_info=body.get('charactersInfo', ''),
                narrative_perspective=body.get('narrativePerspective', '第三人称'),
                style_profile=style,
                world_summary=body.get('worldSummary', ''),
                prev_chapter_title=body.get('prevChapterTitle', ''),
                prev_chapter_tail=body.get('prevChapterTail', ''),
                use_craft=body.get('useCraft', False)
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "Connection": "close",
            "X-Accel-Buffering": "no"
        })

    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    chapter_number = max(1, min(int(body.get('chapterNumber', 1)), 1000))
    total_chapters = max(1, min(int(body.get('totalChapters', 1)), 1000))
    if chapter_number > total_chapters:
        chapter_number = total_chapters
    result, err = gen.generate_chapter_outline(
        project_title=body.get('projectTitle', ''),
        genre=body.get('genre', ''),
        book_overview_json=body.get('bookOverview', ''),
        chapter_number=chapter_number,
        total_chapters=total_chapters,
        characters_info=body.get('charactersInfo', ''),
        narrative_perspective=body.get('narrativePerspective', '第三人称'),
        style_profile=style,
        world_summary=body.get('worldSummary', ''),
        prev_chapter_title=body.get('prevChapterTitle', ''),
        prev_chapter_tail=body.get('prevChapterTail', ''),
        use_craft=body.get('useCraft', False)
    )
    if err:
        return {"error": err}
    return {"result": result}


@router.post("/api/novel/chapter")
async def novel_chapter(body: dict):
    if body.get('stream'):
        cfg = _validate_ai_config(body)
        if not cfg:
            return {"error": "缺少AI配置参数"}
        gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
        style = parse_style_profile(body.get('styleProfile', ''))

        def event_stream():
            yield f"data: {json.dumps({'content': ''}, ensure_ascii=False)}\n\n"
            for chunk in gen.generate_chapter_stream(
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
                technique_focus=body.get('techniqueFocus', ''),
                book_overview=body.get('bookOverview', ''),
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

    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))
    result, err = gen.generate_chapter(
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
        technique_focus=body.get('techniqueFocus', ''),
        book_overview=body.get('bookOverview', ''),
        prev_chapter_hook=body.get('prevChapterHook', ''),
    )
    if err:
        return {"error": err}
    return {"content": result}


@router.post("/api/novel/chapter/polish")
async def chapter_polish(body: dict):
    if not body.get('stream'):
        return {"error": "仅支持流式调用"}
    cfg = _validate_ai_config(body)
    if not cfg:
        return {"error": "缺少AI配置参数"}
    gen = get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'], body.get('temperature', 0.7), body.get('maxTokens', 4000))
    style = parse_style_profile(body.get('styleProfile', ''))

    def event_stream():
        for chunk in gen.polish_chapter_stream(
            project_title=body.get('projectTitle', ''),
            genre=body.get('genre', ''),
            chapter_number=body.get('chapterNumber', 1),
            chapter_title=body.get('chapterTitle', ''),
            chapter_outline=body.get('chapterOutline', ''),
            original_content=body.get('originalContent', ''),
            polish_focus=body.get('polishFocus', '整体优化'),
            style_profile=style,
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "close",
        "X-Accel-Buffering": "no"
    })


@router.post("/api/novel/chapter/summarize")
async def chapter_summarize(body: ChapterSummarizeRequest):
    endpoint = body.endpoint
    api_key = body.api_key
    model = body.model
    chapter_title = body.chapterTitle
    chapter_number = body.chapterNumber
    content = body.content
    if not all([endpoint, api_key, model]):
        return {"error": "缺少 endpoint/apiKey/model"}
    if not content:
        return {"summary": ""}
    from app.services.download_service import UA, HTTP_TIMEOUT
    messages = [
        {'role': 'system', 'content': '你是小说编辑。请将以下章节正文压缩为100字以内的摘要，保留核心事件和关键转折。只输出摘要文字，不要任何格式或说明。'},
        {'role': 'user', 'content': f'第{chapter_number}章《{chapter_title}》正文：\n{content[:6000]}'}
    ]
    req_body = {
        'model': model,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 200,
    }
    import urllib.request
    data = json.dumps(req_body).encode('utf-8')
    ep = endpoint.rstrip("/")
    if ep.endswith("/chat/completions"):
        url = ep
    elif ep.endswith("/v1"):
        url = f"{ep}/chat/completions"
    else:
        url = f"{ep}/v1/chat/completions"
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
        choices = result.get('choices', [])
        text = choices[0].get('message', {}).get('content', '') if choices else ''
        return {"summary": text.strip()}
    except Exception as e:
        return {"summary": ""}
