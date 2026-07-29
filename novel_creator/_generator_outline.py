import json
import logging

from .craft_prompts import CHAPTER_OUTLINE_CRAFT, CHAPTER_OUTLINE_CRAFT_STYLE
from .prompts import (
    BOOK_OVERVIEW_CREATE,
    BOOK_OVERVIEW_CREATE_STYLE,
    CHAPTER_OUTLINE_DETAIL,
    CHAPTER_OUTLINE_DETAIL_STYLE,
    OUTLINE_CREATE,
    OUTLINE_CREATE_STYLE,
    format_prompt,
    parse_json_response,
)

logger = logging.getLogger('novel_creator.generator')


class _OutlineMixin:

    def generate_book_overview(self, title, theme, genre, characters_info,
                               narrative_perspective="第三人称", style_profile=None,
                               world_summary="", inspiration_desc=""):
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        world_text = world_summary if world_summary else "（未设定世界观）"
        desc_text = inspiration_desc if inspiration_desc else "（未设定简介）"

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(BOOK_OVERVIEW_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                story_framework=fmt.get('story_framework', ''),
                core_drive=fmt.get('core_drive', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
                sub_genres=fmt.get('sub_genres', ''),
            )
        else:
            prompt = format_prompt(BOOK_OVERVIEW_CREATE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
            )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def generate_book_overview_stream(self, title, theme, genre, characters_info,
                                      narrative_perspective="第三人称", style_profile=None,
                                      world_summary="", inspiration_desc=""):
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        world_text = world_summary if world_summary else "（未设定世界观）"
        desc_text = inspiration_desc if inspiration_desc else "（未设定简介）"

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(BOOK_OVERVIEW_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
                story_framework=fmt.get('story_framework', ''),
                core_drive=fmt.get('core_drive', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
                sub_genres=fmt.get('sub_genres', ''),
            )
        else:
            prompt = format_prompt(BOOK_OVERVIEW_CREATE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
            )

        logger.info(f"generate_book_overview_stream called: title={title}, theme={theme}, genre={genre}, max_tokens={min(self.max_tokens * 2, 32000)}")
        full_text = ''
        overview_max_tokens = min(self.max_tokens * 2, 32000)
        for chunk in self.client.generate_stream(prompt, temperature=0.7, max_tokens=overview_max_tokens):
            if isinstance(chunk, dict):
                if chunk.get('error'):
                    logger.error(f"book-overview AI error: {chunk['error']}")
                    yield {'done': True, 'error': chunk['error']}
                    return
                text = chunk.get('content', '')
            else:
                text = str(chunk)
            if text:
                full_text += text
                yield {'content': text}
        logger.info(f"book-overview raw response: {len(full_text)} chars")
        if len(full_text) < 100:
            logger.warning(f"book-overview response too short: {full_text!r}")
        result = parse_json_response(full_text)
        if result is not None:
            logger.info(f"book-overview JSON parsed successfully: {len(json.dumps(result))} chars")
            yield {'done': True, 'result': result}
        else:
            logger.error(f"book-overview JSON parse failed: {full_text[:500]!r}")
            yield {'done': True, 'error': f'JSON解析失败: {full_text[:200]}'}

    def summarize_book_overview(self, overview_json):
        if isinstance(overview_json, str):
            try:
                ov = json.loads(overview_json)
            except (json.JSONDecodeError, TypeError):
                return {"raw_text": overview_json[:500]}
        elif isinstance(overview_json, dict):
            ov = overview_json
        else:
            return {"raw_text": str(overview_json)[:500]}

        cc = ov.get('core_conflict', {})
        acts = ov.get('acts', [])
        chars = ov.get('character_arcs', [])

        return {
            "central_conflict": cc.get('central_conflict', ''),
            "central_question": cc.get('central_question', ''),
            "thematic_statement": cc.get('thematic_statement', ''),
            "act_count": len(acts),
            "act_names": [a.get('name', '') for a in acts],
            "char_arc_count": len(chars),
            "char_names": [c.get('name', '') for c in chars[:8]],
            "foreshadow_count": len(ov.get('foreshadowing', [])),
            "subplot_count": len(ov.get('subplots', [])),
            "pacing_segments": len(ov.get('pacing', []))
        }

    # ── Outline ──

    def generate_outline(self, title, theme, genre, characters_info, chapter_count=3,
                         narrative_perspective="第三人称", style_profile=None, world_summary=""):
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(OUTLINE_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                chapter_count=chapter_count,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_summary or "（未设定世界观）",
                sub_genres=fmt.get('sub_genres', ''),
                core_drive=fmt.get('core_drive', ''),
                story_framework=fmt.get('story_framework', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
            )
        else:
            prompt = format_prompt(
                OUTLINE_CREATE,
                title=title, theme=theme, genre=genre,
                chapter_count=chapter_count,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_summary or "（未设定世界观）",
            )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ── Chapter Outline ──

    def _extract_characters_text(self, characters_info):
        if isinstance(characters_info, list):
            return "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        return str(characters_info)

    def _parse_overview(self, book_overview_json):
        overview_available = True
        try:
            overview = json.loads(book_overview_json) if isinstance(book_overview_json, str) else book_overview_json
            if not overview or not isinstance(overview, dict):
                overview = {}
                overview_available = False
        except (json.JSONDecodeError, TypeError):
            overview = {}
            overview_available = False
        degradation_warning = ""
        if not overview_available:
            degradation_warning = (
                "\n\u26a0\ufe0f 注意：全书总纲缺失或格式错误，本章细纲缺少上下文注入"
                "（幕信息、角色弧、支线、伏笔均不可用）。建议重新生成总纲后再次生成细纲。"
            )
        return overview, degradation_warning

    @staticmethod
    def _get_chapter_position(chapter_number, total_chapters):
        if total_chapters <= 1:
            return "这是唯一的一章，需要完整呈现故事。"
        elif chapter_number <= total_chapters * 0.1:
            return "属于开局阶段，需要建立世界观、引入主角、设置初始矛盾。"
        elif chapter_number <= total_chapters * 0.25:
            return "属于发展阶段，需要推进剧情、增加冲突复杂度、发展角色关系。"
        elif chapter_number <= total_chapters * 0.5:
            return "属于中期发展阶段，需要深化主线、设置伏笔、推动角色成长。"
        elif chapter_number <= total_chapters * 0.75:
            return "属于高潮铺垫期，需要加速节奏、激化矛盾、汇集线索。"
        elif chapter_number < total_chapters:
            return "属于高潮阶段，需要最激烈的冲突、关键转折、情感爆发。"
        return "属于结局阶段，需要收束所有线索、解决核心矛盾、给出情感满足。"

    def _build_act_context(self, overview, chapter_number, total_chapters):
        acts = overview.get('acts', [])
        current_act = None
        for act in acts:
            cr = act.get('chapter_range', '')
            parts = cr.split('-')
            if len(parts) == 2:
                try:
                    start, end = int(parts[0]), int(parts[1])
                    if start <= chapter_number <= end:
                        current_act = act
                        break
                except ValueError:
                    pass
        if not current_act and acts:
            idx = min(int(chapter_number / max(total_chapters, 1) * len(acts)), len(acts) - 1)
            current_act = acts[idx]

        act_context = "所属幕：" + (current_act.get('name', '未知') if current_act else '未知')
        if current_act:
            act_context += "\n本幕目标：" + current_act.get('goal', '')
            act_context += "\n本幕情感基调：" + current_act.get('emotional_tone', '')
            if current_act.get('key_turning_point'):
                act_context += "\n本幕关键转折：" + current_act['key_turning_point']
        return act_context

    def _extract_chapter_metadata(self, overview, chapter_number, total_chapters):
        char_arcs = overview.get('character_arcs', [])
        milestones_here = []
        for arc in char_arcs:
            for ms in arc.get('milestones', []):
                if ms.get('chapter') == chapter_number:
                    milestones_here.append({"name": arc.get('name', ''), "change": ms.get('change', '')})
        character_milestones = "本章无角色转变" if not milestones_here else "\n".join(
            [f"- {m['name']}: {m['change']}" for m in milestones_here]
        )

        subplots = overview.get('subplots', [])
        active_here = [sp for sp in subplots if chapter_number in sp.get('involved_chapters', [])]
        active_subplots = "无活跃支线" if not active_here else "\n".join(
            [f"- {sp['name']}（收束于第{sp.get('resolution_chapter', '?')}章）" for sp in active_here]
        )

        fores = overview.get('foreshadowing', [])
        plant_here = [f for f in fores if f.get('planted_chapter') == chapter_number]
        payoff_here = [f for f in fores if f.get('payoff_chapter') == chapter_number]
        foreshadow_to_plant = "无需埋设伏笔" if not plant_here else "\n".join(
            [f"- {f['hint']}（将于第{f.get('payoff_chapter', '?')}章回收）" for f in plant_here]
        )
        foreshadow_to_payoff = "无需回收伏笔" if not payoff_here else "\n".join(
            [f"- {f['hint']} → 揭示：{f.get('reveal', '')}" for f in payoff_here]
        )

        pacing = overview.get('pacing', [])
        pace_here = None
        for p in pacing:
            pc = p.get('chapters', '')
            parts = pc.split('-')
            if len(parts) == 2:
                try:
                    if int(parts[0]) <= chapter_number <= int(parts[1]):
                        pace_here = p
                        break
                except ValueError:
                    pass
        if not pace_here and pacing:
            pace_here = pacing[min(int(chapter_number / max(total_chapters, 1) * len(pacing)), len(pacing) - 1)]
        pacing_requirement = "节奏：" + (pace_here.get('rhythm', '正常') if pace_here else '正常')
        if pace_here:
            pacing_requirement += "\n爽点类型：" + pace_here.get('satisfaction_type', '无特殊要求')

        return {
            'character_milestones': character_milestones,
            'active_subplots': active_subplots,
            'foreshadow_to_plant': foreshadow_to_plant,
            'foreshadow_to_payoff': foreshadow_to_payoff,
            'pacing_requirement': pacing_requirement,
        }

    def _build_chapter_outline_prompt(self, project_title, genre, book_overview_json, chapter_number,
                                        total_chapters, characters_info, narrative_perspective="第三人称",
                                        style_profile=None, world_summary="", prev_chapter_title="",
                                        prev_chapter_tail="", use_craft=False):
        chars_text = self._extract_characters_text(characters_info)
        overview, degradation_warning = self._parse_overview(book_overview_json)
        act_context = self._build_act_context(overview, chapter_number, total_chapters)
        meta = self._extract_chapter_metadata(overview, chapter_number, total_chapters)
        position = self._get_chapter_position(chapter_number, total_chapters)

        world_ctx = world_summary[:300] if world_summary else "（未设定世界观）"
        prev_title = prev_chapter_title or "（无前章）"
        prev_tail = (prev_chapter_tail or "")[:300] if prev_chapter_tail else "（无前章结尾）"

        overview_json_str = book_overview_json if isinstance(book_overview_json, str) else json.dumps(book_overview_json, ensure_ascii=False, indent=2)

        prompt_kwargs = {
            'project_title': project_title, 'genre': genre,
            'book_overview_json': overview_json_str,
            'chapter_number': chapter_number,
            'total_chapters': total_chapters, 'characters_info': chars_text,
            'narrative_perspective': narrative_perspective,
            'my_position': position,
            'act_context': act_context,
            'character_milestones': meta['character_milestones'],
            'active_subplots': meta['active_subplots'],
            'foreshadow_to_plant': meta['foreshadow_to_plant'],
            'foreshadow_to_payoff': meta['foreshadow_to_payoff'],
            'pacing_requirement': meta['pacing_requirement'],
            'world_summary': world_ctx,
            'prev_chapter_title': prev_title,
            'prev_chapter_tail': prev_tail,
            'degradation_warning': degradation_warning,
        }

        if use_craft:
            if style_profile:
                fmt = self._build_style_prompt_vars(style_profile)
                prompt_kwargs.update(fmt)
                return format_prompt(CHAPTER_OUTLINE_CRAFT_STYLE, **prompt_kwargs)
            else:
                return format_prompt(CHAPTER_OUTLINE_CRAFT, **prompt_kwargs)
        elif style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt_kwargs.update({
                'story_framework': fmt.get('story_framework', ''),
                'satisfaction_pattern': fmt.get('satisfaction_pattern', ''),
                'hook_design': fmt.get('hook_design', ''),
                'transition_style': fmt.get('transition_style', ''),
                'foreshadowing_style': fmt.get('foreshadowing_style', ''),
                'writing_techniques': fmt.get('writing_techniques', ''),
                'pacing': fmt.get('pacing', ''),
                'emotional_beats': fmt.get('emotional_beats', ''),
            })
            return format_prompt(CHAPTER_OUTLINE_DETAIL_STYLE, **prompt_kwargs)
        else:
            return format_prompt(CHAPTER_OUTLINE_DETAIL, **prompt_kwargs)

    def generate_chapter_outline(self, project_title, genre, book_overview_json, chapter_number,
                                  total_chapters, characters_info, narrative_perspective="第三人称",
                                  style_profile=None, world_summary="", prev_chapter_title="", prev_chapter_tail="",
                                  use_craft=False):
        prompt = self._build_chapter_outline_prompt(
            project_title, genre, book_overview_json, chapter_number,
            total_chapters, characters_info, narrative_perspective,
            style_profile, world_summary, prev_chapter_title, prev_chapter_tail,
            use_craft,
        )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def generate_chapter_outline_stream(self, project_title, genre, book_overview_json, chapter_number,
                                         total_chapters, characters_info, narrative_perspective="第三人称",
                                         style_profile=None, world_summary="", prev_chapter_title="",
                                         prev_chapter_tail="", use_craft=False):
        prompt = self._build_chapter_outline_prompt(
            project_title, genre, book_overview_json, chapter_number,
            total_chapters, characters_info, narrative_perspective,
            style_profile, world_summary, prev_chapter_title, prev_chapter_tail,
            use_craft,
        )
        logger.info(f"generate_chapter_outline_stream called: chapter={chapter_number}, max_tokens={min(self.max_tokens, 16000)}")
        full_text = ''
        outline_max_tokens = min(self.max_tokens, 16000)
        for chunk in self.client.generate_stream(prompt, temperature=0.7, max_tokens=outline_max_tokens):
            if isinstance(chunk, dict):
                if chunk.get('error'):
                    logger.error(f"chapter-outline AI error: {chunk['error']}")
                    yield {'done': True, 'error': chunk['error']}
                    return
                text = chunk.get('content', '')
            else:
                text = str(chunk)
            if text:
                full_text += text
                yield {'content': text}
        logger.info(f"chapter-outline raw response: {len(full_text)} chars")
        result = parse_json_response(full_text)
        if result is not None:
            logger.info("chapter-outline JSON parsed OK")
            yield {'done': True, 'result': result}
        else:
            logger.error(f"chapter-outline JSON parse failed: {full_text[:500]!r}")
            yield {'done': True, 'error': f'JSON解析失败: {full_text[:200]}'}
