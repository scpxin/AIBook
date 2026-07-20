"""V2 数据库 DDL Schema - 从 database_v2.py 拆分
Schema Version: 1
"""

V2_SCHEMA_DDL = """            /* ========================================
             * V2 数据库 — 18模块创作流水线
             * Schema Version: 1
             * ======================================== */

            /* 0. 全局设置（模型配置等） */
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 0b. 灵感离线模板 */
            CREATE TABLE IF NOT EXISTS idea_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '💡',
                genre TEXT NOT NULL,
                prompt TEXT NOT NULL,
                reference TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_idea_templates_project ON idea_templates(project_id);

            /* 1. 灵感 (模块1) */
            CREATE TABLE IF NOT EXISTS v2_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                user_input TEXT DEFAULT '',
                genre_hint TEXT DEFAULT '',
                reference_works TEXT DEFAULT '[]',
                candidates TEXT DEFAULT '[]',
                selected_concept TEXT DEFAULT '',
                core_selling_points TEXT DEFAULT '[]',
                target_audience TEXT DEFAULT '{}',
                risks TEXT DEFAULT '[]',
                sustainability_estimate TEXT DEFAULT '',
                total_score REAL DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 2. 项目定位 (模块2) */
            CREATE TABLE IF NOT EXISTS v2_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                idea_id INTEGER DEFAULT 0,
                platform_choice TEXT DEFAULT 'tomato',
                project_overview TEXT DEFAULT '',
                novel_position TEXT DEFAULT '{}',
                platform_config TEXT DEFAULT '{}',
                audience TEXT DEFAULT '{}',
                commercial TEXT DEFAULT '{}',
                style TEXT DEFAULT '{}',
                pace TEXT DEFAULT '{}',
                innovation TEXT DEFAULT '[]',
                content_boundary TEXT DEFAULT '[]',
                wordcount_plan TEXT DEFAULT '{}',
                update_plan TEXT DEFAULT '{}',
                risks TEXT DEFAULT '[]',
                derived_fields TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 3. 世界观 (模块3) */
            CREATE TABLE IF NOT EXISTS v2_world_buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                origin TEXT DEFAULT '{}',
                rules TEXT DEFAULT '[]',
                structure TEXT DEFAULT '{}',
                civilization TEXT DEFAULT '{}',
                history TEXT DEFAULT '[]',
                doc_path TEXT DEFAULT '',
                world_foreshadows TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 4. 角色 (模块4) */
            CREATE TABLE IF NOT EXISTS v2_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                char_id TEXT NOT NULL,
                role_type TEXT DEFAULT 'supporting',
                name TEXT DEFAULT '',
                doc_path TEXT DEFAULT '',
                profile TEXT DEFAULT '{}',
                appearance TEXT DEFAULT '{}',
                personality TEXT DEFAULT '{}',
                abilities TEXT DEFAULT '{}',
                growth_route TEXT DEFAULT '[]',
                initial_relations TEXT DEFAULT '[]',
                initial_psychology TEXT DEFAULT '{}',
                initial_state TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, char_id)
            );

            CREATE TABLE IF NOT EXISTS v2_relation_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                nodes TEXT DEFAULT '[]',
                edges TEXT DEFAULT '[]',
                role_groups TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (project_id) REFERENCES v2_projects(project_id)
            );

            /* 5. 故事体系 (模块5) */
            CREATE TABLE IF NOT EXISTS v2_story_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                summary TEXT DEFAULT '',
                conflict_layers TEXT DEFAULT '[]',
                theme TEXT DEFAULT '',
                volume_cliffhangers TEXT DEFAULT '[]',
                volumes_detail TEXT DEFAULT '[]',
                total_plot_events TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 6. 力量体系 (模块6) */
            CREATE TABLE IF NOT EXISTS v2_power_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                tiers TEXT DEFAULT '[]',
                combat_categories TEXT DEFAULT '[]',
                growth_method TEXT DEFAULT '',
                limits TEXT DEFAULT '[]',
                bottlenecks TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 7. 势力体系 (模块7) */
            CREATE TABLE IF NOT EXISTS v2_factions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                faction_id TEXT NOT NULL,
                name TEXT DEFAULT '',
                faction_type TEXT DEFAULT '',
                territory TEXT DEFAULT '',
                leader_char_id TEXT DEFAULT '',
                military_strength TEXT DEFAULT '',
                core_value TEXT DEFAULT '',
                relations TEXT DEFAULT '[]',
                protagonist_status TEXT DEFAULT '',
                members TEXT DEFAULT '[]',
                internal_conflicts TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, faction_id)
            );

            /* 8. 时间线 (模块8) */
            CREATE TABLE IF NOT EXISTS v2_timelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                events TEXT DEFAULT '[]',
                consistency_status TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 9. 卷纲 (模块9) */
            CREATE TABLE IF NOT EXISTS v2_volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                volume_no INTEGER NOT NULL,
                name TEXT DEFAULT '',
                target_words INTEGER DEFAULT 250000,
                chapter_count INTEGER DEFAULT 100,
                protagonist_start TEXT DEFAULT '{}',
                protagonist_end TEXT DEFAULT '{}',
                key_events TEXT DEFAULT '[]',
                volume_foreshadows TEXT DEFAULT '[]',
                cliffhanger TEXT DEFAULT '',
                consistency_status TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, volume_no)
            );

            /* 10. 剧情节点 (模块10) */
            CREATE TABLE IF NOT EXISTS v2_plot_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                title TEXT DEFAULT '',
                trigger TEXT DEFAULT '',
                scene_location TEXT DEFAULT '',
                characters TEXT DEFAULT '[]',
                action_purpose TEXT DEFAULT '',
                dialogue_points TEXT DEFAULT '[]',
                climax TEXT DEFAULT '',
                consequence TEXT DEFAULT '',
                next_events TEXT DEFAULT '[]',
                word_count_min INTEGER DEFAULT 1500,
                word_count_max INTEGER DEFAULT 3000,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, event_id)
            );

            /* 11. 章节扩展 (模块11-12) */
            CREATE TABLE IF NOT EXISTS v2_chapter_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT NOT NULL,
                title TEXT DEFAULT '',
                target_words INTEGER DEFAULT 2000,
                plot_nodes_covered TEXT DEFAULT '[]',
                timeline_events TEXT DEFAULT '[]',
                hook_type TEXT DEFAULT '',
                cliffhanger TEXT DEFAULT '',
                protagonist_level TEXT DEFAULT '',
                locations TEXT DEFAULT '[]',
                dialogue_ratio REAL DEFAULT 0.4,
                pacing TEXT DEFAULT 'normal',
                foreshadows_to_add TEXT DEFAULT '[]',
                foreshadows_to_recycle TEXT DEFAULT '[]',
                emotion_curve TEXT DEFAULT '[]',
                scenes TEXT DEFAULT '[]',
                knowledge_update TEXT DEFAULT '{}',
                status TEXT DEFAULT 'planned',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, chapter_no)
            );

            /* 12. 场景设计 (模块14) */
            CREATE TABLE IF NOT EXISTS v2_scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                scene_id TEXT NOT NULL,
                chapter_no TEXT DEFAULT '',
                setting TEXT DEFAULT '{}',
                plot_purpose TEXT DEFAULT '',
                core_conflict TEXT DEFAULT '',
                combat_strategy TEXT DEFAULT '',
                foreshadow_integration TEXT DEFAULT '',
                atmosphere TEXT DEFAULT '',
                reader_reaction TEXT DEFAULT '',
                expected_emotion TEXT DEFAULT '{}',
                scene_hooks TEXT DEFAULT '{}',
                word_count_actual INTEGER DEFAULT 0,
                content_path TEXT DEFAULT '',
                state_diff TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, scene_id)
            );

            /* 13. 伏笔管理 (M2+M9+M12+M17共享) */
            CREATE TABLE IF NOT EXISTS v2_foreshadowings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                foreshadow_id TEXT NOT NULL,
                source_type TEXT DEFAULT '',
                source_id TEXT DEFAULT '',
                foreshadow_type TEXT DEFAULT '',
                description TEXT DEFAULT '',
                trigger_text TEXT DEFAULT '',
                target_volume INTEGER DEFAULT 0,
                target_chapter INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                resolved_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, foreshadow_id)
            );

            /* 14. 知识库 (模块17-18) */
            CREATE TABLE IF NOT EXISTS v2_knowledge_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                character_states TEXT DEFAULT '{}',
                world_state TEXT DEFAULT '{}',
                plot_state TEXT DEFAULT '{}',
                consistency_status TEXT DEFAULT '{}',
                last_check_at TEXT DEFAULT '',
                last_chapter_no TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 15. AI生成日志 (全流程共享) */
            CREATE TABLE IF NOT EXISTS v2_ai_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                entity_type TEXT DEFAULT '',
                entity_id TEXT DEFAULT '',
                prompt_hash TEXT DEFAULT '',
                prompt_text TEXT DEFAULT '',
                response_text TEXT DEFAULT '',
                model_used TEXT DEFAULT '',
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 16. 一致性检查日志 (模块18) */
            CREATE TABLE IF NOT EXISTS v2_consistency_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT DEFAULT '',
                score REAL DEFAULT 1.0,
                items TEXT DEFAULT '[]',
                summary TEXT DEFAULT '',
                fixes TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 17. 正文草稿 (模块15) */
            CREATE TABLE IF NOT EXISTS v2_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT NOT NULL,
                scene_id TEXT DEFAULT '',
                content TEXT DEFAULT '',
                content_raw TEXT DEFAULT '',
                word_count_raw INTEGER DEFAULT 0,
                word_count_final INTEGER DEFAULT 0,
                polish_status TEXT DEFAULT 'draft',
                foreshadow_added TEXT DEFAULT '[]',
                continuity_check TEXT DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* === V2 索引 === */
            CREATE INDEX IF NOT EXISTS idx_v2_ideas_project ON v2_ideas(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_projects_project ON v2_projects(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_world_project ON v2_world_buildings(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_chars_project ON v2_characters(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_story_project ON v2_story_systems(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_power_project ON v2_power_systems(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_factions_project ON v2_factions(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_timeline_project ON v2_timelines(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_volumes_project ON v2_volumes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_plot_project ON v2_plot_nodes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_chapters_project ON v2_chapter_plans(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_scenes_project ON v2_scenes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_foreshadow_project ON v2_foreshadowings(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_knowledge_project ON v2_knowledge_states(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_ai_gen_project ON v2_ai_generations(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_consistency_project ON v2_consistency_reports(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_drafts_project ON v2_drafts(project_id);

            /* 18. 流水线状态 (持久化) */
            CREATE TABLE IF NOT EXISTS v2_pipeline_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                consistency_score REAL DEFAULT 0,
                started_at TEXT DEFAULT '',
                completed_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                data_json TEXT DEFAULT '{}',
                UNIQUE(project_id, module_name)
            );
            CREATE INDEX IF NOT EXISTS idx_v2_pipeline_project ON v2_pipeline_states(project_id);

            /* 19. 生成模板库 — AI生成结果存为可复用模板 */
            CREATE TABLE IF NOT EXISTS v2_generation_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                module_key TEXT NOT NULL,
                genre TEXT DEFAULT '',
                sub_genre TEXT DEFAULT '',
                tone TEXT DEFAULT '',
                world_type TEXT DEFAULT '',
                target_audience TEXT DEFAULT '',
                source_project_id TEXT DEFAULT '',
                input_fingerprint TEXT DEFAULT '',
                output_data TEXT DEFAULT '{}',
                input_context TEXT DEFAULT '{}',
                entity_refs TEXT DEFAULT '{}',
                compatibility_group TEXT DEFAULT '',
                usage_count INTEGER DEFAULT 0,
                quality_rating REAL DEFAULT 0,
                is_public INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_v2_gen_tpl_module ON v2_generation_templates(module_key);
            CREATE INDEX IF NOT EXISTS idx_v2_gen_tpl_genre ON v2_generation_templates(genre);
            CREATE INDEX IF NOT EXISTS idx_v2_gen_tpl_world ON v2_generation_templates(world_type);
            CREATE INDEX IF NOT EXISTS idx_v2_gen_tpl_compat ON v2_generation_templates(compatibility_group);
        """
