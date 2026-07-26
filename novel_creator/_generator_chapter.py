from .craft_prompts import (
    CHAPTER_CONTINUATION_CRAFT,
    CHAPTER_CONTINUATION_CRAFT_STYLE,
    CHAPTER_GENERATION_CRAFT,
    CHAPTER_GENERATION_CRAFT_STYLE,
    QUALITY_SCORE,
)
from .prompts import (
    CHAPTER_CONTINUATION,
    CHAPTER_CONTINUATION_STYLE,
    CHAPTER_GENERATION_NEXT,
    CHAPTER_GENERATION_NEXT_STYLE,
    CHAPTER_POLISH,
    format_prompt,
)


class _ChapterMixin:

    def generate_chapter(self, project_title, genre, chapter_number, chapter_title,
                         chapter_outline, continuation_point="", previous_chapter_summary="",
                         chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                         narrative_perspective="第三人称", style_profile=None, technique_focus="",
                         book_overview="", world_summary="", first_chapter_strategy="",
                         prev_chapter_hook=""):
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_NEXT_STYLE,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''),
                pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
                book_overview=book_overview or "（未填写全书总纲，按章节大纲自由发挥）"
            )
        else:
            prompt = format_prompt(
                CHAPTER_GENERATION_NEXT,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                book_overview=book_overview or "（未填写全书总纲，按章节大纲自由呈现）"
            )
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err

    def generate_chapter_stream(self, project_title, genre, chapter_number, chapter_title,
                                chapter_outline, continuation_point="", previous_chapter_summary="",
                                chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                                narrative_perspective="第三人称", style_profile=None, technique_focus="",
                                book_overview="", progress_content="", segment_chars=0,
                                world_summary="", first_chapter_strategy="",
                                prev_chapter_hook=""):
        if progress_content and progress_content.strip():
            actual_target = segment_chars if segment_chars > 0 else 800
            ctx_limit = getattr(self.client, 'max_tokens', 4000)
            max_progress_chars = min(len(progress_content), int(ctx_limit * 1.2))
            trimmed_progress = progress_content[-max_progress_chars:] if len(progress_content) > max_progress_chars else progress_content
            style_section = ''
            if style_profile:
                style_fmt = self._build_style_prompt_vars(style_profile)
                style_section = format_prompt(CHAPTER_CONTINUATION_STYLE,
                    tone=style_fmt.get('tone', ''),
                    pacing=style_fmt.get('pacing', ''),
                    sentence_structure=style_fmt.get('sentence_structure', ''),
                    dialogue_style=style_fmt.get('dialogue_style', ''),
                    description_style=style_fmt.get('description_style', ''),
                    emotional_intensity=style_fmt.get('emotional_intensity', ''),
                    writing_techniques=style_fmt.get('writing_techniques', ''),
                    foreshadowing_style=style_fmt.get('foreshadowing_style', ''),
                    overall_summary=style_fmt.get('overall_summary', ''),
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                )
            prompt = format_prompt(
                CHAPTER_CONTINUATION,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                progress_content=trimmed_progress,
                chapter_outline=chapter_outline or "（见总纲）",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                target_word_count=target_word_count,
                progress_chars=str(len(progress_content)),
                segment_chars=str(actual_target),
                style_section=style_section,
            )
            for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
                if isinstance(chunk, dict) and chunk.get('error'):
                    yield {'done': True, 'error': chunk['error']}
                    return
                yield chunk
            return

        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        chars_text = self._format_characters(chapter_characters)
        world_text = world_summary if world_summary else "（未设定世界观）"
        first_chapter_note = ""
        if first_chapter_strategy == "first_chapter":
            first_chapter_note = "\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。"

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_NEXT_STYLE,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(
                CHAPTER_GENERATION_NEXT,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def polish_chapter_stream(self, project_title, genre, chapter_number, chapter_title,
                               chapter_outline, original_content, polish_focus="整体优化",
                               style_profile=None):
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
        prompt = format_prompt(
            CHAPTER_POLISH,
            project_title=project_title,
            genre=genre,
            chapter_number=chapter_number,
            chapter_title=chapter_title or ('第' + str(chapter_number) + '章'),
            chapter_outline=chapter_outline or "（见大纲）",
            original_content=original_content,
            polish_focus=polish_focus,
            tone=fmt.get('tone', ''),
            pacing=fmt.get('pacing', ''),
            sentence_structure=fmt.get('sentence_structure', ''),
            description_style=fmt.get('description_style', ''),
        )
        for chunk in self.client.generate_stream(prompt, temperature=0.6, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def generate_chapter_craft(self, project_title, genre, chapter_number, chapter_title,
                               chapter_outline, continuation_point="", previous_chapter_summary="",
                               chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                               narrative_perspective="第三人称", style_profile=None, technique_focus="",
                               book_overview="", world_summary="", first_chapter_strategy="",
                               prev_chapter_hook=""):
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT_STYLE,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''),
                pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(
                CHAPTER_GENERATION_CRAFT,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err

    def generate_chapter_craft_stream(self, project_title, genre, chapter_number, chapter_title,
                                      chapter_outline, continuation_point="", previous_chapter_summary="",
                                      chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                                      narrative_perspective="第三人称", style_profile=None, technique_focus="",
                                      book_overview="", progress_content="", segment_chars=0,
                                      world_summary="", first_chapter_strategy="",
                                      prev_chapter_hook=""):
        if progress_content and progress_content.strip():
            actual_target = segment_chars if segment_chars > 0 else 800
            ctx_limit = getattr(self.client, 'max_tokens', 4000)
            max_progress_chars = min(len(progress_content), int(ctx_limit * 1.2))
            trimmed_progress = progress_content[-max_progress_chars:] if len(progress_content) > max_progress_chars else progress_content
            fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
            if style_profile:
                prompt = format_prompt(
                    CHAPTER_CONTINUATION_CRAFT_STYLE,
                    project_title=project_title, genre=genre,
                    chapter_number=chapter_number, chapter_title=chapter_title,
                    progress_content=trimmed_progress,
                    chapter_outline=chapter_outline or "（见总纲）",
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                    target_word_count=target_word_count,
                    progress_chars=str(len(progress_content)),
                    segment_chars=str(actual_target),
                    tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                    sentence_structure=fmt.get('sentence_structure', ''),
                    dialogue_style=fmt.get('dialogue_style', ''),
                    description_style=fmt.get('description_style', ''),
                    emotional_intensity=fmt.get('emotional_intensity', ''),
                    writing_techniques=fmt.get('writing_techniques', ''),
                    foreshadowing_style=fmt.get('foreshadowing_style', ''),
                    overall_summary=fmt.get('overall_summary', ''),
                )
            else:
                prompt = format_prompt(
                    CHAPTER_CONTINUATION_CRAFT,
                    project_title=project_title, genre=genre,
                    chapter_number=chapter_number, chapter_title=chapter_title,
                    progress_content=trimmed_progress,
                    chapter_outline=chapter_outline or "（见总纲）",
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                    target_word_count=target_word_count,
                    progress_chars=str(len(progress_content)),
                    segment_chars=str(actual_target),
                )
            for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
                if isinstance(chunk, dict) and chunk.get('error'):
                    yield {'done': True, 'error': chunk['error']}
                    return
                yield chunk
            return

        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
        chars_text = self._format_characters(chapter_characters)
        world_text = world_summary if world_summary else "（未设定世界观）"
        first_chapter_note = ""
        if first_chapter_strategy == "first_chapter":
            first_chapter_note = "\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。"

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT_STYLE,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def quality_score(self, content, title="", genre=""):
        prompt = format_prompt(QUALITY_SCORE, content=content[:6000], title=title or "未命名", genre=genre or "未知")
        result, err = self._generate_json(prompt)
        return result, err
