
// Error handler to display JS errors on page
window.onerror = function(msg, url, line, col, err) {
    let el = document.getElementById('js-error-display');
    if (!el) {
        el = document.createElement('div');
        el.id = 'js-error-display';
        el.style.cssText = 'position:fixed;top:0;left:0;width:100%;max-height:200px;overflow:auto;background:#e74c3c;color:#fff;padding:10px;z-index:99999;font-size:12px;font-family:monospace;white-space:pre-wrap;';
        document.body.appendChild(el);
    }
    el.textContent += 'Line ' + line + ': ' + msg + '\n';
};
const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;

createApp({
    setup() {
        const BASE = '/fanqie';
        const activeTab = ref(0);

        // ====== Models ======
        const models = ref([]);
        const activeModelId = ref('');
        const showSettings = ref(false);
        const showAddForm = ref(false);
        const editingId = ref('');
        const formValidation = ref('');
        const form = reactive({ name: '', endpoint: '', apiKey: '', model: '' });

        function loadModels() {
            try { models.value = JSON.parse(localStorage.getItem('fanqie_models') || '[]'); } catch(e) { models.value = []; }
            activeModelId.value = localStorage.getItem('fanqie_active_model') || (models.value.length ? models.value[0].id : '');
            novelModelId.value = activeModelId.value;
        }
        function saveModels() { localStorage.setItem('fanqie_models', JSON.stringify(models.value)); }

        function setActiveModel(id) {
            activeModelId.value = id;
            novelModelId.value = id;
            localStorage.setItem('fanqie_active_model', id);
        }

        function getActiveModel() {
            return models.value.find(m => m.id === activeModelId.value) || models.value[0] || null;
        }

        function closeSettings() {
            showSettings.value = false;
            showAddForm.value = false;
            resetForm();
        }

        function resetForm() {
            editingId.value = '';
            form.name = ''; form.endpoint = ''; form.apiKey = ''; form.model = '';
            formValidation.value = '';
        }

        function startAddModel() {
            resetForm();
            showAddForm.value = true;
        }

        function cancelEdit() {
            if (editingId.value && (form.name || form.apiKey || form.endpoint || form.model)) {
                if (!confirm('放弃当前编辑？')) return;
            }
            resetForm();
            showAddForm.value = false;
        }

        function editModel(m) {
            editingId.value = m.id;
            form.name = m.name;
            form.endpoint = m.endpoint;
            form.apiKey = m.apiKey;
            form.model = m.model;
            formValidation.value = '';
            showAddForm.value = true;
        }

        function deleteModel(id) {
            if (!confirm('确定删除此模型配置？')) return;
            const wasActive = activeModelId.value === id;
            models.value = models.value.filter(m => m.id !== id);
            if (wasActive) setActiveModel(models.value.length ? models.value[0].id : '');
            saveModels();
        }

        function saveModel() {
            const name = form.name.trim();
            if (!name) {
                formValidation.value = '请填写模型名称';
                return;
            }

            const dup = models.value.find(m => m.name === name && m.id !== editingId.value);
            if (dup) {
                formValidation.value = '已存在同名模型 "' + name + '"';
                return;
            }

            formValidation.value = '';

            const modelData = {
                name: name,
                endpoint: form.endpoint.trim(),
                apiKey: form.apiKey.trim(),
                model: form.model.trim()
            };

            if (editingId.value) {
                const idx = models.value.findIndex(m => m.id === editingId.value);
                if (idx >= 0) {
                    models.value[idx] = { id: editingId.value, ...modelData };
                }
            } else {
                models.value.push({ id: 'm' + Date.now(), ...modelData });
            }

            saveModels();
            if (!activeModelId.value && models.value.length) {
                setActiveModel(models.value[models.value.length - 1].id);
            }
            resetForm();
            showAddForm.value = false;
        }

        function addPresetModel(name, endpoint, model) {
            const dup = models.value.find(m => m.name === name);
            if (dup) {
                setActiveModel(dup.id);
                return;
            }
            const id = 'm' + Date.now();
            models.value.push({ id, name, endpoint, apiKey: '', model });
            saveModels();
            setActiveModel(id);
        }

        function fillPreset(name, endpoint, model) {
            editingId.value = '';
            form.name = name;
            form.endpoint = endpoint;
            form.model = model;
            form.apiKey = '';
            formValidation.value = '';
            showAddForm.value = true;
        }

        // ====== Search & Download ======
        const searchQuery = ref('');
        const searchLoading = ref(false);
        const searchResults = ref([]);
        const searchError = ref('');
        const bookCounts = ref({});
        const book = ref(null);
        const dlState = ref('idle');
        const dlCurrent = ref(0);
        const dlTotal = ref(0);
        const dlSessionId = ref(null);
        const dlPct = computed(() => dlTotal.value > 0 ? Math.round(dlCurrent.value / dlTotal.value * 100) : 0);
        const dlStatusText = computed(() => {
            if (dlState.value === 'running') return '下载中 ' + dlPct.value + '%';
            if (dlState.value === 'paused') return '已暂停 ' + dlPct.value + '%';
            if (dlState.value === 'done') return '下载完成!';
            if (dlState.value === 'error') return '下载失败';
            return '点击下方按钮开始';
        });

        const API_TIMEOUT = 600000; // 10 minutes for AI calls

        async function api(path, params) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
            let url = BASE + path;
            if (params) {
                const qs = Object.keys(params).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&');
                url += (url.indexOf('?') === -1 ? '?' : '&') + qs;
            }
            try {
                const r = await fetch(url, { signal: controller.signal });
                clearTimeout(timeoutId);
                if (!r.ok) {
                    const text = await r.text();
                    let d = {};
                    try { d = JSON.parse(text); } catch {}
                    throw new Error(d.error || `服务器错误 (${r.status})`);
                }
                return r.json();
            } catch (e) {
                clearTimeout(timeoutId);
                if (e.name === 'AbortError') throw new Error('请求超时，请检查网络或服务器状态');
                throw e;
            }
        }

        async function apiPost(path, body) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
            try {
                const r = await fetch(BASE + path, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (!r.ok) {
                    let msg;
                    const text = await r.text();
                    try {
                        const d = JSON.parse(text);
                        msg = d.error || `服务器错误 (${r.status})`;
                    } catch {
                        msg = `服务器错误 (${r.status}): ${text.slice(0, 200)}`;
                    }
                    throw new Error(msg);
                }
                return r.json();
            } catch (e) {
                clearTimeout(timeoutId);
                if (e.name === 'AbortError') throw new Error('请求超时，请检查网络或服务器状态');
                throw e;
            }
        }

        async function apiPostStream(path, body, onChunk) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
            try {
                const r = await fetch(BASE + path, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (!r.ok) {
                    const text = await r.text();
                    let d = {};
                    try { d = JSON.parse(text); } catch {}
                    throw new Error(d.error || `服务器错误 (${r.status})`);
                }
                const reader = r.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            try {
                                const obj = JSON.parse(data);
                                onChunk(obj);
                            } catch {}
                        }
                    }
                }
            } catch (e) {
                clearTimeout(timeoutId);
                if (e.name === 'AbortError') throw new Error('请求超时，请检查网络或服务器状态');
                throw e;
            }
        }

        async function doSearch() {
            if (!searchQuery.value.trim()) return;
            searchLoading.value = true;
            searchError.value = '';
            searchResults.value = [];
            book.value = null;
            bookCounts.value = {};

            try {
                const idMatch = searchQuery.value.match(/(\d{16,20})/);
                if (idMatch) {
                    const info = await api('/api/resolve', { q: searchQuery.value });
                    if (info && info.book_id) { book.value = info; searchLoading.value = false; return; }
                }
                const data = await api('/api/search', { q: searchQuery.value });
                searchResults.value = data.books || [];
                searchResults.value.forEach(b => {
                    api('/api/directory', { book_id: b.book_id }).then(d => { bookCounts.value[b.book_id] = d.total + ' 章'; }).catch(() => {});
                });
            } catch(e) {
                searchError.value = e.message;
            }
            searchLoading.value = false;
        }

        function selectBook(b) {
            book.value = { book_id: b.book_id, title: b.title || b.book_name, author: b.author, count: bookCounts.value[b.book_id] };
            dlState.value = 'idle';
            dlCurrent.value = 0;
            dlTotal.value = 0;
        }

        function resetSearch() {
            book.value = null;
            searchResults.value = [];
            searchQuery.value = '';
            dlState.value = 'idle';
        }

        async function startDownload() {
            if (!book.value || dlState.value === 'running') return;
            if (dlState.value === 'paused' && dlSessionId.value) { doResume(); return; }
            dlState.value = 'running';
            dlCurrent.value = 0;
            try {
                const d = await api('/api/download/start', { book_id: book.value.book_id, title: book.value.title });
                dlSessionId.value = d.session_id;
                pollDownload();
            } catch(e) {
                dlState.value = 'idle';
                alert('启动下载失败: ' + e.message);
            }
        }

        let pollRetries = 0;
        async function pollDownload() {
            if (!dlSessionId.value || dlState.value === 'idle') return;
            try {
                const d = await api('/api/download/status', { session_id: dlSessionId.value });
                dlCurrent.value = d.current;
                dlTotal.value = d.total;
                pollRetries = 0;
                if (d.status === 'done') { dlState.value = 'done'; }
                else if (d.status === 'downloading') { setTimeout(pollDownload, 1000); }
                else if (d.status === 'paused') { dlState.value = 'paused'; }
                else if (d.status === 'error') { dlState.value = 'error'; }
            } catch(e) {
                pollRetries++;
                if (pollRetries < 10) { setTimeout(pollDownload, 2000); }
                else { dlState.value = 'error'; }
            }
        }

        async function doPause() {
            if (!dlSessionId.value) return;
            await api('/api/download/pause', { session_id: dlSessionId.value });
            dlState.value = 'paused';
        }

        async function doResume() {
            if (!dlSessionId.value) return;
            await api('/api/download/resume', { session_id: dlSessionId.value });
            dlState.value = 'running';
            pollDownload();
        }

        function saveFile() {
            if (dlSessionId.value) window.location.href = BASE + '/api/download/file?session_id=' + dlSessionId.value;
        }

        // ====== Novel Creation ======
        const stepLabels = ['1.灵感', '2.世界观', '3.角色', '4.总纲+细纲', '5.章节正文'];
        const novel = reactive({
            step: 0, title: '', description: '', theme: '', genre: '',
            world: '', characters: '', bookOverview: '', outlineText: '', outline: [],
            chapters: [], currentChapter: 0, charCount: 10, chapterCount: 3,
            perspective: '第三人称', targetWords: 3000, styleProfile: '', useCraft: true
        });
        const novelModelId = ref('');
        const inspireLoading = ref(false);
        const inspireError = ref('');
        const inspireTitleOptions = ref([]);
        const customPrompt = ref('');
        const inspireDescOptions = ref([]);
        const charsLoading = ref(false);
        const outlineLoading = ref(false);
        const chapterLoading = ref(false);
        const chapterProgress = ref('');
        // stopGeneration removed - using genStopFlag / outlineStopFlag instead
        const storyContext = reactive({ summaries: [], unresolvedForeshadowing: [] });
        const genProgress = reactive({
            show: false, title: '', subtitle: '', timeText: '', pct: 0,
            startTime: 0, timer: null,
            // 用于基于历史预估耗时（毫秒），按类型
            estimates: { world: 35000, chars: 60000, outline: 45000, chapter: 60000 }
        });

        // ===== 项目管理 =====
        const currentProjectId = ref('');
        const currentProjectName = ref('');
        const projects = ref([]);
        const showProjectModal = ref(false);
        const saveNameInput = ref('');
        const saveStatus = ref(''); // '', 'saving', 'saved', 'error'
        const autoSaveTimer = ref(null);

        async function loadProjectList() {
            try {
                const d = await apiPost('/api/projects/list', {});
                projects.value = d.projects || [];
            } catch(e) {
                console.error('加载项目列表失败:', e);
            }
        }

        async function saveProject() {
            if (saveStatus.value === 'saving') return;
            saveStatus.value = 'saving';
            const name = saveNameInput.value.trim() || novel.title || '未命名项目';
            try {
                await apiPost('/api/projects/save', {
                    id: currentProjectId.value || undefined,
                    name: name,
                    step: novel.step,
                    data: {
                        title: novel.title,
                        description: novel.description,
                        theme: novel.theme,
                        genre: novel.genre,
                        world: novel.world,
                        characters: novel.characters,
                        bookOverview: novel.bookOverview,
                        outlineText: novel.outlineText,
                        outline: novel.outline,
                        chapters: novel.chapters,
                        charCount: novel.charCount,
                        chapterCount: novel.chapterCount,
                        perspective: novel.perspective,
                        targetWords: novel.targetWords,
                        styleProfile: novel.styleProfile,
                        useCraft: novel.useCraft,
                        storyContext: {
                            summaries: storyContext.summaries,
                            unresolvedForeshadowing: storyContext.unresolvedForeshadowing,
                        },
                    }
                });
                saveStatus.value = 'saved';
                currentProjectName.value = name;
                setTimeout(() => { saveStatus.value = ''; }, 2000);
                loadProjectList();
            } catch(e) {
                saveStatus.value = 'error';
                console.error('保存失败:', e);
                setTimeout(() => { saveStatus.value = ''; }, 3000);
            }
        }

        async function openLoadModal() {
            await loadProjectList();
            showProjectModal.value = true;
        }

        async function loadProject(id) {
            try {
                const p = await apiPost('/api/projects/load', { id });
                if (p.error) { alert(p.error); return; }

                // 恢复项目数据到 novel 状态
                const d = p.data || {};
                novel.title = d.title || '';
                novel.description = d.description || '';
                novel.theme = d.theme || '';
                novel.genre = d.genre || '';
                novel.world = d.world || '';
                novel.characters = d.characters || '';
                novel.bookOverview = d.bookOverview || '';
                novel.outlineText = d.outlineText || '';
                novel.outline = d.outline || [];
                novel.chapters = d.chapters || [];
                novel.charCount = d.charCount || 10;
                novel.chapterCount = d.chapterCount || 3;
                novel.perspective = d.perspective || '第三人称';
                novel.targetWords = d.targetWords || 3000;
                novel.styleProfile = d.styleProfile || '';
                novel.useCraft = d.useCraft !== undefined ? d.useCraft : true;
                novel.step = p.step || 0;

                currentProjectId.value = p.id;
                currentProjectName.value = p.name || '';

                // 恢复 storyContext
                if (d.storyContext) {
                    storyContext.summaries = d.storyContext.summaries || [];
                    storyContext.unresolvedForeshadowing = d.storyContext.unresolvedForeshadowing || [];
                } else {
                    storyContext.summaries = [];
                    storyContext.unresolvedForeshadowing = [];
                    if (novel.chapters.length > 0) {
                        for (let i = 0; i < novel.chapters.length; i++) {
                            const o = novel.outline[i];
                            storyContext.summaries.push(
                                '第' + (i + 1) + '章 ' + (o ? o.title : '') + ': ' + (o && o.summary ? o.summary.slice(0, 150) : '')
                            );
                        }
                    }
                }

                showProjectModal.value = false;
                saveStatus.value = 'saved';
                setTimeout(() => { saveStatus.value = ''; }, 2000);

                // 从数据库加载章节和大纲
                await loadChaptersFromDb();
                await loadOutlinesFromDb();
                // 加载步骤摘要，若无则从项目数据重建
                const summaries = await loadStepSummaries();
                if (!summaries.inspiration && novel.title) {
                    await saveStepSummary('inspiration', {
                        title: novel.title, description: novel.description,
                        theme: novel.theme, genre: novel.genre,
                        core_premise: (novel.description || '').slice(0, 100)
                    });
                }
                if (!summaries.world && novel.world) {
                    await saveStepSummary('world', {
                        key_locations: [], power_system: '',
                        summary_text: (novel.world || '').slice(0, 500)
                    });
                }
                if (!summaries.characters && novel.characters) {
                    await saveStepSummary('characters', { char_names: [], char_count: 0 });
                }
                // 加载总纲
                const overviewOl = dbOutlines.value.find(o => o.chapter_number === 0);
                if (overviewOl && overviewOl.book_overview) {
                    bookOverview.value = overviewOl.book_overview;
                }
            } catch(e) {
                alert('加载失败: ' + e.message);
            }
        }

        async function deleteProject(id) {
            if (!confirm('确定要删除这个项目吗？此操作不可恢复。')) return;
            try {
                await apiPost('/api/projects/delete', { id });
                if (currentProjectId.value === id) {
                    currentProjectId.value = '';
                    currentProjectName.value = '';
                }
                loadProjectList();
            } catch(e) {
                alert('删除失败: ' + e.message);
            }
        }

        async function newProject() {
            if (novel.title && !confirm('当前有未保存的内容，确定要新建项目吗？')) return;
            currentProjectId.value = '';
            currentProjectName.value = '';
            novel.step = 0; novel.title = ''; novel.description = ''; novel.theme = ''; novel.genre = '';
            novel.world = ''; novel.characters = ''; novel.bookOverview = ''; novel.outlineText = '';
            novel.outline = []; novel.chapters = []; novel.currentChapter = 0;
            novel.charCount = 10; novel.chapterCount = 3;
            storyContext.summaries = [];
            storyContext.unresolvedForeshadowing = [];
        }

        // 自动保存：当 novel 内容变化时延迟保存
        function scheduleAutoSave() {
            if (autoSaveTimer.value) clearTimeout(autoSaveTimer.value);
            autoSaveTimer.value = setTimeout(() => {
                if (currentProjectId.value && novel.title) {
                    saveProject();
                }
            }, 30000); // 30秒自动保存
        }

        // 自动保存：标记 setup 完成后才启用 watch
        let setupDone = false;
        setTimeout(() => { setupDone = true; }, 100);
        // Debounce utility for textarea DB saves
        const _debounceTimers = {};
        function _debounced(key, fn, delay) {
            clearTimeout(_debounceTimers[key]);
            _debounceTimers[key] = setTimeout(fn, delay);
        }
        watch(() => [novel.title, novel.description, novel.theme, novel.genre, novel.world, novel.characters, novel.outlineText, novel.outline.length, novel.chapters.length, novel.bookOverview], () => {
            if (setupDone) scheduleAutoSave();
        });

        const genStats = ref({ startTime: 0, chapterTimes: {} });

        function genStart(title, subtitle, estMs) {
            genProgress.show = true;
            genProgress.title = title;
            genProgress.subtitle = subtitle || '';
            genProgress.startTime = Date.now();
            genProgress.pct = 0;
            genStats.value.startTime = Date.now();
            if (genProgress.timer) clearInterval(genProgress.timer);
            const start = Date.now();
            genProgress.timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - start) / 1000);
                const mm = String(Math.floor(elapsed / 60)).padStart(1, '0');
                const ss = String(elapsed % 60).padStart(2, '0');
                const est = estMs || 60000;
                const remaining = Math.max(0, Math.floor((est - (Date.now() - start)) / 1000));
                const rm = String(Math.floor(remaining / 60)).padStart(1, '0');
                const rs = String(remaining % 60).padStart(2, '0');
                genProgress.timeText = mm + ':' + ss + ' / ~' + rm + ':' + rs;
            }, 500);
        }

        function genUpdate(msg) {
            genProgress.subtitle = msg;
        }

        function genEnd() {
            if (genProgress.timer) clearInterval(genProgress.timer);
            genProgress.timer = null;
            genProgress.show = false;
        }

        function _fmtTime(s) {
            if (s < 60) return s + '秒';
            if (s < 3600) return Math.floor(s / 60) + '分' + (s % 60) + '秒';
            return Math.floor(s / 3600) + '时' + Math.floor((s % 3600) / 60) + '分';
        }

        // Style analysis
        const styleExpanded = ref(false);
        const styleTab = ref('paste');
        const styleText = ref('');
        const styleLoading = ref(false);
        const savedBooks = ref([]);
        const selectedSavedBook = ref('');
        const savedBookAnalyzing = ref(false);

        const styleProfileSummary = computed(() => {
            if (!novel.styleProfile) return '';
            try {
                const obj = JSON.parse(novel.styleProfile);
                return obj.overall_summary || obj.summary || novel.styleProfile.slice(0, 200);
            } catch(e) {
                return novel.styleProfile.slice(0, 200);
            }
        });

        function showStep(n) {
            novel.step = n;
        }

        function hasStepContent(i) {
            if (i === 0) return !!(novel.title && novel.description && novel.theme && novel.genre);
            if (i === 1) return !!novel.world;
            if (i === 2) return !!novel.characters;
            if (i === 3) return !!novel.outlineText;
            if (i === 4) return novel.chapters.length > 0;
            return false;
        }

        function canGoToStep(n) {
            if (n <= 1) return !!novel.title;
            if (n === 2) return !!novel.title && !!novel.world;
            if (n === 3) return !!novel.title && !!novel.world && !!novel.characters;
            if (n === 4) return !!novel.title && !!novel.world && !!novel.characters && novel.outline.length > 0;
            return false;
        }

        function getNovelModel() {
            return models.value.find(m => m.id === novelModelId.value) || models.value[0] || null;
        }

        // Inspiration - 并行优化：3轮代替4轮串行
        async function generateInspire() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            inspireLoading.value = true;
            inspireError.value = '';
            inspireTitleOptions.value = [];
            inspireDescOptions.value = [];
            genStart('正在生成灵感', '书名 → 简介 → 主题+类型', 90000);

            const hasStyle = !!novel.styleProfile;
            const userInput = hasStyle ? '' : (customPrompt.value || '');
            const titleInput = hasStyle ? '[风格参考]\n' + novel.styleProfile + '\n\n[用户输入]\n' : (customPrompt.value || '');
            const descInput = hasStyle ? '[风格参考]\n' + novel.styleProfile + '\n\n' : (customPrompt.value || '');
            const base = { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, styleProfile: novel.styleProfile };

            try {
                genUpdate('正在生成书名...');
                const d1 = await apiPost('/api/novel/inspiration/title', { ...base, userInput: titleInput });
                inspireTitleOptions.value = (d1.options || []).map((opt, i) => ({
                    idx: i, text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || JSON.stringify(opt)) : opt, selected: i === 0
                }));
                if (d1.options && d1.options[0]) {
                    const first = d1.options[0];
                    novel.title = typeof first === 'object' ? (first.name || first.title || first.text || JSON.stringify(first)) : first;
                }

                // 第2轮：简介（依赖书名）
                genUpdate('正在生成简介...');
                const d2 = await apiPost('/api/novel/inspiration/description', { ...base, title: novel.title, userInput: descInput });
                inspireDescOptions.value = (d2.options || []).map((opt, i) => ({
                    idx: i, text: typeof opt === 'object' ? (opt.name || opt.title || opt.text || opt.description || JSON.stringify(opt)) : opt, selected: i === 0
                }));
                if (d2.options && d2.options[0]) {
                    const first = d2.options[0];
                    novel.description = typeof first === 'object' ? (first.name || first.title || first.text || first.description || JSON.stringify(first)) : first;
                }

                // 第3轮：主题 + 类型 并行（都依赖书名+简介）
                genUpdate('正在生成主题和类型...');
                const themeInput = hasStyle ? '[风格参考]\n' + novel.styleProfile : userInput;
                const [d3, d4] = await Promise.all([
                    apiPost('/api/novel/inspiration/theme', { ...base, title: novel.title, description: novel.description, userInput: themeInput }),
                    apiPost('/api/novel/inspiration/genre', { ...base, title: novel.title, description: novel.description, userInput: themeInput }),
                ]);
                if (d3.options && d3.options[0]) {
                    const first = d3.options[0];
                    novel.theme = typeof first === 'object' ? (first.name || first.title || first.text || first.theme || JSON.stringify(first)) : first;
                }
                if (d4.options && d4.options[0]) {
                    const first = d4.options[0];
                    novel.genre = typeof first === 'object' ? (first.name || first.title || first.text || first.genre || JSON.stringify(first)) : first;
                }
                // 保存灵感步骤摘要
                await saveStepSummary('inspiration', {
                    title: novel.title, description: novel.description,
                    theme: novel.theme, genre: novel.genre,
                    core_premise: (novel.description || '').slice(0, 100)
                });
            } catch(e) {
                inspireError.value = e.message;
            }
            genEnd();
            inspireLoading.value = false;
        }

        function selectInspireTitle(opt) {
            inspireTitleOptions.value.forEach(o => o.selected = false);
            opt.selected = true;
            novel.title = opt.text;
        }
        function selectInspireDesc(opt) {
            inspireDescOptions.value.forEach(o => o.selected = false);
            opt.selected = true;
            novel.description = opt.text;
        }

        // ===== 步骤摘要管理 =====
        async function saveStepSummary(step, summary) {
            if (!currentProjectId.value) return;
            try {
                await apiPost('/api/step-summary/save', {
                    projectId: currentProjectId.value, step, summary: summary || {}
                });
            } catch(e) { console.error('保存步骤摘要失败:', e); }
        }

        async function loadStepSummaries() {
            if (!currentProjectId.value) return {};
            try {
                const d = await apiPost('/api/step-summary/get', { projectId: currentProjectId.value });
                return d.summaries || {};
            } catch(e) { return {}; }
        }

        // World
        async function generateWorld() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            novel.world = '正在生成世界观，请稍候...';
            genStart('正在生成世界观', '时间背景 / 空间环境 / 情感基调 / 世界规则', genProgress.estimates.world);
            try {
                const d = await apiPost('/api/novel/worldbuilding', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, title: novel.title, theme: novel.theme, genre: novel.genre, description: novel.description, styleProfile: novel.styleProfile });
                let text = '';
                const labels = { time_period: '【时间背景】', location: '【空间环境】', atmosphere: '【情感基调】', rules: '【世界规则】' };
                ['time_period', 'location', 'atmosphere', 'rules'].forEach(k => {
                    if (d[k]) {
                        let val = d[k];
                        if (typeof val === 'object') {
                            val = val.description || val.detail || val.content || val.name || JSON.stringify(val);
                        }
                        text += labels[k] + '\n' + val + '\n\n';
                    }
                });
                novel.world = text.trim();
            } catch(e) {
                novel.world = '生成失败: ' + e.message;
            }
            genEnd();
            // 保存世界观步骤摘要
            await saveStepSummary('world', {
                key_locations: [],
                power_system: '',
                summary_text: (novel.world || '').slice(0, 500)
            });
        }

        // Characters
        async function generateChars() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            charsLoading.value = true;
            novel.characters = '正在生成角色，请稍候...';
            const charEst = genProgress.estimates.chars + Math.max(0, novel.charCount - 6) * 5000;
            genStart('正在生成角色', novel.charCount + ' 个角色', charEst);
            let chars = [];
            try {
                const d = await apiPost('/api/novel/characters', {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    worldData: { time_period: novel.world, location: '', atmosphere: '', rules: novel.world },
                    theme: novel.theme, genre: novel.genre, count: novel.charCount, styleProfile: novel.styleProfile
                });
                chars = d.characters || [];
                let text = '';
                chars.forEach(c => {
                    if (c.is_organization) {
                        text += (c.name || '') + ' - 组织 - ' + (c.organization_purpose || '') + '\n';
                    } else {
                        text += (c.name || '') + ' - ' + (c.role_type || '角色') + ' - ' + (c.personality || '') + '\n';
                    }
                });
                novel.characters = text.trim();
                // 保存角色步骤摘要
                await saveStepSummary('characters', {
                    protagonist: chars[0] ? { name: chars[0].name, role: chars[0].role_type, personality: chars[0].personality } : {},
                    char_count: chars.length,
                    char_names: chars.map(c => c.name || '').filter(Boolean).slice(0, 8)
                });
            } catch(e) {
                novel.characters = '生成失败: ' + e.message;
                await saveStepSummary('characters', { char_names: [], char_count: 0 });
            }
            genEnd();
            charsLoading.value = false;
        }

        // Outline
        // ===== 大纲管理 =====
        const dbOutlines = ref([]);
        const outlineGenStatus = ref(null);
        const outlineStopFlag = ref(false);
        const outlinePauseFlag = ref(false);
        const outlineGenStats = ref({ startTime: 0, chapterTimes: {} });
        const bookOverview = ref(''); // 总纲文本

        async function loadOutlinesFromDb() {
            if (!currentProjectId.value) { dbOutlines.value = []; return; }
            try {
                const d = await apiPost('/api/outline/get', { projectId: currentProjectId.value });
                dbOutlines.value = (d.outlines || []).map(o => ({ ...o, expanded: false }));
                outlineGenStatus.value = d.status;
                // 同步到 novel.outline 和 novel.outlineText
                syncOutlineToNovel();
            } catch(e) { console.error('加载大纲失败:', e); }
        }

        function syncOutlineToNovel() {
            if (!dbOutlines.value.length) { novel.outline = []; novel.outlineText = ''; return; }
            const sorted = [...dbOutlines.value].sort((a, b) => a.chapter_number - b.chapter_number);
            novel.outline = sorted.map(o => ({
                chapter_number: String(o.chapter_number),
                title: o.title || ('第' + o.chapter_number + '章'),
                summary: o.summary || '',
            }));
            novel.outlineText = sorted.map(o =>
                '第' + o.chapter_number + '章 ' + (o.title || '') + ' - ' + (o.summary || '')
            ).join('\n');
        }

        async function saveOutlineToDb(chapterNumber, outlineData, status) {
            if (!currentProjectId.value) return;
            try {
                await apiPost('/api/outline/save', {
                    projectId: currentProjectId.value,
                    chapterNumber,
                    title: outlineData.title || '',
                    summary: outlineData.summary || '',
                    scenes: outlineData.scenes || [],
                    characters: outlineData.characters || [],
                    keyPoints: outlineData.key_points || [],
                    emotion: outlineData.emotion || '',
                    goal: outlineData.goal || '',
                    techniqueFocus: outlineData.technique_focus || '',
                    bookOverview: bookOverview.value || '',
                    acts: outlineData.acts || [],
                    status: status || 'done',
                });
                await loadOutlinesFromDb();
            } catch(e) { console.error('保存大纲失败:', e); }
        }

        async function deleteOutlineFromDb(chapterNumber) {
            if (!currentProjectId.value) return;
            if (!confirm('确定删除第' + chapterNumber + '章大纲？')) return;
            try {
                await apiPost('/api/outline/delete', { projectId: currentProjectId.value, chapterNumber });
                await loadOutlinesFromDb();
            } catch(e) { console.error('删除大纲失败:', e); }
        }

        // 生成总纲
        async function generateBookOverview() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            outlineLoading.value = true;
            genStart('正在生成全书总纲', '故事脉络、核心矛盾、关键转折', genProgress.estimates.outline * 0.4);
            try {
                const d = await apiPost('/api/novel/book-overview', {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    projectId: currentProjectId.value,
                    title: novel.title, theme: novel.theme, genre: novel.genre,
                    description: novel.description || '',
                    charactersInfo: novel.characters, narrativePerspective: novel.perspective,
                    styleProfile: novel.styleProfile,
                    worldSummary: novel.world || ''
                });
                const result = d.result || {};
                bookOverview.value = JSON.stringify(result, null, 2);
                novel.bookOverview = result.core_conflict?.central_conflict || result.story_arc || '';
                // 保存总纲到 DB（chapter_number=0 表示总纲）
                await apiPost('/api/outline/save', {
                    projectId: currentProjectId.value, chapterNumber: 0,
                    title: '全书总纲',
                    summary: JSON.stringify(result.core_conflict || {}),
                    acts: result.acts || [],
                    scenes: result.foreshadowing || [],
                    characters: result.character_arcs || [],
                    keyPoints: result.subplots || [],
                    emotion: JSON.stringify(result.pacing || []),
                    goal: result.core_conflict?.central_conflict || '',
                    techniqueFocus: '',
                    bookOverview: bookOverview.value,
                    status: 'done',
                });
                genProgress.subtitle = '总纲生成完成！';
                // 保存总纲步骤摘要
                await saveStepSummary('book_overview', {
                    central_conflict: result.core_conflict?.central_conflict || '',
                    central_question: result.core_conflict?.central_question || '',
                    thematic_statement: result.core_conflict?.thematic_statement || '',
                    act_count: (result.acts || []).length,
                    act_names: (result.acts || []).map(a => a.name || ''),
                    char_arc_count: (result.character_arcs || []).length,
                    char_names: (result.character_arcs || []).map(c => c.name || '').slice(0, 8),
                    foreshadow_count: (result.foreshadowing || []).length,
                    subplot_count: (result.subplots || []).length,
                    pacing_segments: (result.pacing || []).length
                });
            } catch(e) {
                alert('总纲生成失败: ' + e.message);
            }
            genEnd();
            outlineLoading.value = false;
        }

        // 生成单章细纲
        async function generateChapterOutline(chapterNumber) {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!bookOverview.value) { alert('请先生成全书总纲'); return; }
            outlineLoading.value = true;
            genStart('正在生成第' + chapterNumber + '章细纲', '', genProgress.estimates.outline * 0.6);
            // 获取前一章信息
            const prevOutline = dbOutlines.value.find(o => o.chapter_number === chapterNumber - 1);
            const prevChapter = dbChapters.value.find(c => c.chapter_number === chapterNumber - 1);
            const prevTitle = prevOutline ? prevOutline.title : '';
            const prevTail = prevChapter ? (prevChapter.content || '').slice(-300) : '';
            try {
                const d = await apiPost('/api/novel/chapter-outline', {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    projectTitle: novel.title, genre: novel.genre,
                    bookOverview: bookOverview.value,
                    chapterNumber: chapterNumber,
                    totalChapters: novel.chapterCount,
                    charactersInfo: novel.characters,
                    narrativePerspective: novel.perspective,
                    styleProfile: novel.styleProfile,
                    prevChapterTitle: prevTitle,
                    prevChapterTail: prevTail,
                });
                const result = d.result || {};
                await saveOutlineToDb(chapterNumber, {
                    title: result.title || ('第' + chapterNumber + '章'),
                    summary: result.summary || '',
                    scenes: result.scenes || [],
                    characters: result.characters || [],
                    key_points: result.key_points || [],
                    emotion: result.emotion || '',
                    goal: result.goal || '',
                    technique_focus: result.technique_focus || '',
                }, 'done');
                genProgress.subtitle = '第' + chapterNumber + '章细纲完成';
            } catch(e) {
                await saveOutlineToDb(chapterNumber, { title: '第' + chapterNumber + '章' }, 'error');
                alert('第' + chapterNumber + '章细纲生成失败: ' + e.message);
            }
            genEnd();
            outlineLoading.value = false;
        }

        // 批量生成全部细纲
        async function generateAllChapterOutlines() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!bookOverview.value) { alert('请先生成全书总纲'); return; }
            outlineStopFlag.value = false;
            outlinePauseFlag.value = false;
            outlineLoading.value = true;
            const totalChapters = novel.chapterCount;
            outlineGenStats.value = { startTime: Date.now(), chapterTimes: {} };
            // 记录生成开始
            await apiPost('/api/outline/generation/start', {
                projectId: currentProjectId.value,
                totalChapters: totalChapters,
                endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                projectTitle: novel.title, genre: novel.genre,
                styleProfile: novel.styleProfile, bookOverview: bookOverview.value,
                targetWords: novel.targetWords, narrativePerspective: novel.perspective,
                chapterCharacters: novel.characters.slice(0, 500),
            });
            let completed = 0, failed = 0;
            genStart('正在生成章节细纲', '0 / ' + totalChapters + ' 章', genProgress.estimates.outline * totalChapters);
            for (let i = 1; i <= totalChapters; i++) {
                if (outlineStopFlag.value) break;
                while (outlinePauseFlag.value && !outlineStopFlag.value) {
                    await new Promise(r => setTimeout(r, 500));
                }
                if (outlineStopFlag.value) break;
                // 跳过已完成的大纲
                const existingOutline = dbOutlines.value.find(o => Number(o.chapter_number) === i && o.status === 'done');
                if (existingOutline) {
                    completed++;
                    outlineGenStats.value.chapterTimes[i] = 0;
                    continue;
                }
                const chapStart = Date.now();
                const elapsed = (chapStart - outlineGenStats.value.startTime) / 1000;
                const avgPerChap = completed > 0 ? elapsed / completed : genProgress.estimates.outline / 1000;
                const doneCount = completed + failed;
                const remaining = Math.max(0, Math.floor(avgPerChap * (totalChapters - doneCount)));
                genUpdate('第 ' + i + ' / ' + totalChapters + ' 章（✓' + completed + ' ✗' + failed + '，已用 ' + _fmtTime(Math.floor(elapsed)) + '，预计还需 ' + _fmtTime(remaining) + '）');
                await apiPost('/api/outline/generation/update', {
                    projectId: currentProjectId.value, currentChapter: i,
                    completedChapters: completed, failedChapters: failed
                });
                // 获取前一章信息用于衔接
                const prevOl = dbOutlines.value.find(o => o.chapter_number === i - 1);
                const prevCh = dbChapters.value.find(c => c.chapter_number === i - 1);
                // 生成单章细纲
                try {
                    const d = await apiPost('/api/novel/chapter-outline', {
                        endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                        projectTitle: novel.title, genre: novel.genre,
                        bookOverview: bookOverview.value,
                        chapterNumber: i, totalChapters: totalChapters,
                        charactersInfo: novel.characters,
                        narrativePerspective: novel.perspective,
                        styleProfile: novel.styleProfile,
                        prevChapterTitle: prevOl ? prevOl.title : '',
                        prevChapterTail: prevCh ? (prevCh.content || '').slice(-200) : '',
                    });
                    const result = d.result || {};
                    await saveOutlineToDb(i, {
                        title: result.title || ('第' + i + '章'),
                        summary: result.summary || '',
                        scenes: result.scenes || [],
                        characters: result.characters || [],
                        key_points: result.key_points || [],
                        emotion: result.emotion || '',
                        goal: result.goal || '',
                        technique_focus: result.technique_focus || '',
                    }, 'done');
                    completed++;
                } catch(e) {
                    await saveOutlineToDb(i, { title: '第' + i + '章' }, 'error');
                    failed++;
                }
                outlineGenStats.value.chapterTimes[i] = Math.round((Date.now() - chapStart) / 1000);
                if (!outlineStopFlag.value && !outlinePauseFlag.value && i < totalChapters) {
                    await new Promise(r => setTimeout(r, 300));
                }
            }
            await apiPost('/api/outline/generation/stop', { projectId: currentProjectId.value });
            const totalEl = Math.round((Date.now() - outlineGenStats.value.startTime) / 1000);
            genProgress.subtitle = '全部完成！共 ' + completed + ' 章成功' + (failed > 0 ? '，' + failed + ' 章失败' : '') + '，耗时 ' + _fmtTime(totalEl);
            setTimeout(() => genEnd(), 3000);
            outlineLoading.value = false;
            outlineStopFlag.value = false;
            outlinePauseFlag.value = false;
        }

        function pauseOutlineGeneration() {
            outlinePauseFlag.value = true;
        }

        function resumeOutlineGeneration() {
            // 仅清除暂停标志，已运行的循环会自动继续（while循环检测到flag=false后退出等待）
            outlinePauseFlag.value = false;
        }

        function stopOutlineGenerationBtn() {
            outlineStopFlag.value = true;
        }

        // 兼容旧接口
        async function generateOutline() {
            await generateBookOverview();
            if (bookOverview.value) {
                await generateAllChapterOutlines();
            }
        }

        function cnNumToArabic(s) {
            const map = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10','百':'100','千':'1000','万':'10000'};
            if (/^\d+$/.test(s)) return s;
            let result = 0, temp = 0;
            for (const ch of s) {
                if (map[ch] >= 10) { if (temp === 0) temp = 1; result += temp * map[ch]; temp = 0; }
                else { temp = map[ch]; }
            }
            return String(result + temp);
        }

        function parseOutline() {
            const text = novel.outlineText.trim();
            if (!text) { novel.outline = []; return; }
            const lines = text.split('\n').filter(l => l.trim());
            novel.outline = lines.map((line, i) => {
                const m = line.match(/第\s*([一二三四五六七八九十百千万\d]+)\s*章\s*(.*?)\s*[-\s]\s*(.*)/);
                if (m) return { chapter_number: cnNumToArabic(m[1]), title: m[2] || ('第' + m[1] + '章'), summary: m[3] || m[2] || '' };
                const m2 = line.match(/第\s*([一二三四五六七八九十百千万\d]+)\s*章\s*(.*)/);
                if (m2) return { chapter_number: cnNumToArabic(m2[1]), title: m2[2] || ('第' + m2[1] + '章'), summary: m2[2] || '' };
                return { chapter_number: String(i + 1), title: line.slice(0, 30), summary: line };
            });
        }

        // Chapters
        function _getElapsed() {
            if (!genStats.value.startTime) return '';
            return _fmtTime(Math.floor((Date.now() - genStats.value.startTime) / 1000));
        }

        function _getTotalTime() {
            if (!genStats.value.startTime) return '';
            const times = Object.values(genStats.value.chapterTimes || {});
            const total = times.reduce((a, b) => a + b, 0);
            return _fmtTime(total || Math.floor((Date.now() - genStats.value.startTime) / 1000));
        }

        function _getAvgTime() {
            const times = Object.values(genStats.value.chapterTimes || {});
            if (!times.length) return '';
            return _fmtTime(Math.round(times.reduce((a, b) => a + b, 0) / times.length));
        }

        function _formatWordCount(ch) {
            const wc = ch.word_count || (ch.content ? ch.content.length : 0);
            if (wc >= 10000) return (wc / 10000).toFixed(1) + '万字';
            if (wc >= 1000) return (wc / 1000).toFixed(1) + '千字';
            return wc + '字';
        }

        // ===== 大纲计时 =====
        function _getOutlineElapsed() {
            if (!outlineGenStats.value.startTime) return '';
            return _fmtTime(Math.floor((Date.now() - outlineGenStats.value.startTime) / 1000));
        }

        function _getOutlineTotalTime() {
            if (!outlineGenStats.value.startTime) return '';
            const times = Object.values(outlineGenStats.value.chapterTimes || {});
            const total = times.reduce((a, b) => a + b, 0);
            return _fmtTime(total || Math.floor((Date.now() - outlineGenStats.value.startTime) / 1000));
        }

        function _getOutlineAvgTime() {
            const times = Object.values(outlineGenStats.value.chapterTimes || {});
            if (!times.length) return '';
            return _fmtTime(Math.round(times.reduce((a, b) => a + b, 0) / times.length));
        }

        // ===== 章节数据库管理 =====
        const dbChapters = ref([]);
        const genStatus = ref(null);
        const genStopFlag = ref(false);
        const genPauseFlag = ref(false);

        async function loadChaptersFromDb() {
            if (!currentProjectId.value) { dbChapters.value = []; novel.chapters = []; return; }
            try {
                const d = await apiPost('/api/chapters/get', { projectId: currentProjectId.value });
                dbChapters.value = (d.chapters || []).map(c => ({ ...c, expanded: false }));
                genStatus.value = d.status;
                // 同步到 novel.chapters 保持兼容性
                novel.chapters = dbChapters.value.map(c => c.content || '');
            } catch(e) { console.error('加载章节失败:', e); }
        }

        async function saveChapterToDb(chapterNumber, title, content, status) {
            if (!currentProjectId.value) return;
            try {
                await apiPost('/api/chapters/save', {
                    projectId: currentProjectId.value,
                    chapterNumber, title, content, status
                });
                await loadChaptersFromDb();
            } catch(e) { console.error('保存章节失败:', e); }
        }

        async function deleteChapterFromDb(chapterNumber) {
            if (!currentProjectId.value) return;
            if (!confirm('确定删除第' + chapterNumber + '章？')) return;
            try {
                await apiPost('/api/chapters/delete', { projectId: currentProjectId.value, chapterNumber });
                await loadChaptersFromDb();
            } catch(e) { console.error('删除失败:', e); }
        }

        async function regenerateChapter(chapterNumber) {
            if (!currentProjectId.value) return;
            const idx = chapterNumber - 1;
            const o = novel.outline[idx];
            if (!o) { alert('请先确保大纲中有第' + chapterNumber + '章'); return; }
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            genStopFlag.value = false;
            genPauseFlag.value = false;
            chapterLoading.value = true;
            genStart('正在生成第' + chapterNumber + '章', o.title || '', genProgress.estimates.chapter);
            await _doGenerateChapter(idx, o, m, true);
            chapterLoading.value = false;
            genEnd();
        }

        async function generateNextChapter() {
            parseOutline();
            if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return; }
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            // 找到第一个未生成的章节（统一转为整数比较）
            const doneNumbers = new Set(dbChapters.value.filter(c => c.status === 'done').map(c => Number(c.chapter_number)));
            let idx = 0;
            for (let i = 0; i < novel.outline.length; i++) {
                if (!doneNumbers.has(Number(novel.outline[i].chapter_number))) { idx = i; break; }
                if (i === novel.outline.length - 1) { alert('所有章节已生成完毕'); return; }
            }
            genStopFlag.value = false;
            genPauseFlag.value = false;
            chapterLoading.value = true;
            const o = novel.outline[idx];
            genStart('正在生成第' + (idx + 1) + '章', o.title || '', genProgress.estimates.chapter);
            await _doGenerateChapter(idx, o, m, true);
            chapterLoading.value = false;
            genEnd();
        }

        async function generateAllChapters() {
            parseOutline();
            if (!novel.outline.length) { alert('请先在「大纲」步骤中输入或生成大纲'); return; }
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            genStopFlag.value = false;
            genPauseFlag.value = false;
            chapterLoading.value = true;
            // 记录生成开始
            await apiPost('/api/chapters/generation/start', {
                projectId: currentProjectId.value,
                totalChapters: novel.outline.length,
                endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                projectTitle: novel.title, genre: novel.genre,
                styleProfile: novel.styleProfile, bookOverview: novel.bookOverview || '',
                targetWords: novel.targetWords, narrativePerspective: novel.perspective,
                chapterCharacters: novel.characters.slice(0, 500),
            });
            const totalChapters = novel.outline.length;
            genStats.value = { startTime: Date.now(), chapterTimes: {} };
            let completed = 0, failed = 0;
            genStart('正在生成章节', '0 / ' + totalChapters + ' 章', genProgress.estimates.chapter * totalChapters);
            for (let i = 0; i < totalChapters; i++) {
                if (genStopFlag.value) break;
                while (genPauseFlag.value && !genStopFlag.value) {
                    await new Promise(r => setTimeout(r, 500));
                }
                if (genStopFlag.value) break;
                const o = novel.outline[i];
                const chapNum = Number(o.chapter_number || (i + 1));
                // 跳过已完成的章节
                const existingCh = dbChapters.value.find(c => Number(c.chapter_number) === chapNum && c.status === 'done');
                if (existingCh) {
                    completed++;
                    genStats.value.chapterTimes[chapNum] = 0;
                    continue;
                }
                const chapStart = Date.now();
                const elapsed = (chapStart - genStats.value.startTime) / 1000;
                const avgPerChapter = completed > 0 ? elapsed / completed : genProgress.estimates.chapter / 1000;
                const doneCount = completed + failed;
                const remainingChapters = totalChapters - doneCount;
                const remaining = Math.max(0, Math.floor(avgPerChapter * remainingChapters));
                const rm = Math.floor(remaining / 60), rs = remaining % 60;
                genUpdate('第 ' + chapNum + ' / ' + totalChapters + ' 章（✓' + completed + ' ✗' + failed + '，已用 ' + _fmtTime(Math.floor(elapsed)) + '，预计还需 ' + _fmtTime(remaining) + '）');
                await apiPost('/api/chapters/generation/update', {
                    projectId: currentProjectId.value, currentChapter: chapNum,
                    completedChapters: completed, failedChapters: failed
                });
                const ok = await _doGenerateChapter(i, o, m, false);
                const chapElapsed = Math.round((Date.now() - chapStart) / 1000);
                genStats.value.chapterTimes[chapNum] = chapElapsed;
                if (ok) completed++; else failed++;
                if (!genStopFlag.value && !genPauseFlag.value && i < totalChapters - 1) {
                    await new Promise(r => setTimeout(r, 500));
                }
            }
            await apiPost('/api/chapters/generation/stop', { projectId: currentProjectId.value });
            const totalEl = Math.round((Date.now() - genStats.value.startTime) / 1000);
            genProgress.subtitle = '全部完成！共 ' + completed + ' 章成功' + (failed > 0 ? '，' + failed + ' 章失败' : '') + '，耗时 ' + _fmtTime(totalEl);
            setTimeout(() => genEnd(), 3000);
            chapterLoading.value = false;
            genStopFlag.value = false;
            genPauseFlag.value = false;
            // 不调用 loadChaptersFromDb() — 实时更新已在 _doGenerateChapter 中完成，避免覆盖
        }

        function pauseGeneration() {
            genPauseFlag.value = true;
            chapterProgress.value = '已暂停';
        }

        function resumeGeneration() {
            // 仅清除暂停标志，已运行的循环会自动继续（while循环检测到flag=false后退出等待）
            genPauseFlag.value = false;
        }

        function stopGenerationBtn() {
            genStopFlag.value = true;
            chapterProgress.value = '正在停止...';
        }

        async function _doGenerateChapter(idx, o, m, saveToDb) {
            const chapterNumber = o.chapter_number || (idx + 1);
            chapterProgress.value = '正在生成第' + chapterNumber + '章 / 共' + novel.outline.length + '章...';
            // 累积上下文：从 DB 获取前文摘要
            let prevFullSummary = '', prevEnd = '', foreshadow = '';
            if (idx > 0) {
                const prevCh = dbChapters.value.find(c => Number(c.chapter_number) === Number(chapterNumber) - 1);
                if (prevCh) prevEnd = (prevCh.content || '').slice(-500);
                // 从 storyContext 获取摘要
                const summaries = storyContext.summaries;
                const recentN = 3;
                if (summaries.length <= recentN) {
                    prevFullSummary = summaries.join('\n');
                } else {
                    const recent = summaries.slice(-recentN).join('\n');
                    prevFullSummary = '前文概要：\n' + recent + '\n（此前共' + idx + '章已生成）';
                }
                if (storyContext.unresolvedForeshadowing.length > 0) {
                    foreshadow = '未解伏笔：\n' + storyContext.unresolvedForeshadowing.map((f, fi) => (fi + 1) + '. ' + f).join('\n');
                }
            }
            try {
                const apiPath = novel.useCraft ? '/api/novel/craft/chapter' : '/api/novel/chapter';
                let content = '';
                await apiPostStream(apiPath, {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    projectTitle: novel.title, genre: novel.genre,
                    chapterNumber: chapterNumber, chapterTitle: o.title,
                    chapterOutline: o.summary, continuationPoint: prevEnd,
                    previousChapterSummary: prevFullSummary, chapterCharacters: novel.characters.slice(0, 500),
                    foreshadowReminders: foreshadow,
                    targetWordCount: novel.targetWords, narrativePerspective: novel.perspective,
                     styleProfile: novel.styleProfile, bookOverview: bookOverview.value || novel.bookOverview || '',
                    stream: true
                }, (chunk) => {
                    if (chunk.content) {
                        content += chunk.content;
                        // 实时更新 UI（章节卡片内容）
                        novel.chapters[idx] = content;
                        dbChapters.value = dbChapters.value.map(c => {
                            if (c.chapter_number === chapterNumber) return { ...c, content: content, status: 'generating', word_count: content.length };
                            return c;
                        });
                    }
                    if (chunk.error) {
                        throw new Error(chunk.error);
                    }
                });
                // 更新累积上下文
                const chapSummary = '第' + chapterNumber + '章 ' + (o.title || '') + ': ' + (o.summary || '').slice(0, 150);
                storyContext.summaries.push(chapSummary);
                // 保存到 DB（只要项目ID存在就保存）
                if (currentProjectId.value) {
                    await saveChapterToDb(chapterNumber, o.title || ('第' + chapterNumber + '章'), content, 'done');
                }
                chapterProgress.value = '第' + chapterNumber + '章已完成（' + content.length + '字）';
                return true;
            } catch(e) {
                chapterProgress.value = '第' + chapterNumber + '章生成失败: ' + e.message;
                if (currentProjectId.value) {
                    await saveChapterToDb(chapterNumber, o.title || ('第' + chapterNumber + '章'), '', 'error');
                }
                return false;
            }
        }

        function exportNovel() { exportNovelFromDb(); }

        function exportNovelFromDb() {
            const chapters = dbChapters.value.filter(c => c.status === 'done' && c.content);
            if (!chapters.length) { alert('没有可导出的章节'); return; }
            let text = (novel.title || '小说') + '\n\n';
            if (novel.description) text += '简介：' + novel.description + '\n\n';
            if (novel.world) text += '=== 世界观 ===\n' + novel.world + '\n\n';
            if (novel.characters) text += '=== 角色 ===\n' + novel.characters + '\n\n';
            text += '=== 正文 ===\n\n';
            chapters.sort((a, b) => a.chapter_number - b.chapter_number);
            chapters.forEach(c => {
                text += '第' + c.chapter_number + '章 ' + (c.title || '') + '\n\n' + c.content + '\n\n';
            });
            const blob = new Blob(['\uFEFF' + text], { type: 'text/plain;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = (novel.title || '小说') + '.txt';
            a.click();
            setTimeout(() => URL.revokeObjectURL(a.href), 2000);
        }

        // Style analysis in novel creation
        async function analyzeStyleText() {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!styleText.value.trim()) { alert('请先粘贴小说文本'); return; }
            styleLoading.value = true;
            try {
                const d = await apiPost('/api/novel/analyze-style', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: styleText.value.trim() });
                novel.styleProfile = d.resultJson || JSON.stringify(d.result || {}) || '';
            } catch(e) {
                alert('分析失败: ' + e.message);
            }
            styleLoading.value = false;
        }

        async function loadSavedBooks() {
            try {
                const d = await api('/api/downloads/list', {});
                savedBooks.value = d.books || [];
            } catch(e) { savedBooks.value = []; }
        }

        async function analyzeSavedBook(b) {
            const m = getNovelModel();
            if (!m) { alert('请先配置AI模型'); return; }
            selectedSavedBook.value = b.book_id;
            savedBookAnalyzing.value = true;
            try {
                const d = await api('/api/downloads/content', { book_id: b.book_id });
                const content = d.content || '';
                const r = await apiPost('/api/novel/analyze-style', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content });
                novel.styleProfile = r.resultJson || JSON.stringify(r.result || {}) || '';
            } catch(e) {
                alert('分析失败: ' + e.message);
            }
            savedBookAnalyzing.value = false;
        }

        // ====== AI Style Analysis (standalone) ======
        const analyzeTab = ref('paste');
        const analyzeText = ref('');
        const analyzeModelIdx = ref(0);
        const analyzeLoading = ref(false);
        const analyzeResult = ref('');
        const analyzeResultLines = computed(() => analyzeResult.value.split('\n').filter(l => l.trim()));
        const analyzeSavedBooks = ref([]);
        const selectedAnalyzeBook = ref('');
        const analyzeBookContent = ref('');
        const styleProfile = ref('');

        async function loadAnalyzeSavedBooks() {
            try {
                const d = await api('/api/downloads/list', {});
                analyzeSavedBooks.value = d.books || [];
            } catch(e) { analyzeSavedBooks.value = []; }
        }

        async function selectAnalyzeBook(b) {
            selectedAnalyzeBook.value = b.book_id;
            try {
                const d = await api('/api/downloads/content', { book_id: b.book_id });
                analyzeBookContent.value = d.content || '';
                analyzeText.value = (d.content || '').slice(0, 10000);
            } catch(e) { analyzeBookContent.value = ''; }
        }

        async function runAnalyze() {
            const m = models.value[analyzeModelIdx.value] || models.value[0];
            if (!m) { alert('请先选择模型'); return; }
            if (!analyzeText.value.trim()) { alert('请先粘贴小说文本'); return; }
            analyzeLoading.value = true;
            try {
                const d = await apiPost('/api/ai/analyze', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content: analyzeText.value.trim() });
                analyzeResult.value = d.result;
                styleProfile.value = d.result;
            } catch(e) {
                alert('分析失败: ' + e.message);
            }
            analyzeLoading.value = false;
        }

        // ====== AI Generate ======
        const generateModelIdx = ref(0);
        const genForm = reactive({ genre: '', count: 3, protagonist: '', world: '', outline: '' });
        const genLoading = ref(false);
        const genResult = ref('');
        const genChapters = computed(() => {
            if (!genResult.value) return [];
            const chapters = [];
            const re = /第([\u4e00-\u9fa5\d]+)章\s*(.*?)(?:\n|$)/g;
            let match, lastIdx = 0;
            while ((match = re.exec(genResult.value)) !== null) {
                if (lastIdx > 0) chapters[chapters.length - 1].text = genResult.value.slice(lastIdx, match.index).trim();
                chapters.push({ title: '第' + match[1] + '章' + (match[2] ? ' ' + match[2] : ''), text: '' });
                lastIdx = match.index + match[0].length;
            }
            if (chapters.length && lastIdx < genResult.value.length) chapters[chapters.length - 1].text = genResult.value.slice(lastIdx).trim();
            return chapters;
        });

        async function runGenerate() {
            const m = models.value[generateModelIdx.value] || models.value[0];
            if (!m) { alert('请先选择模型'); return; }
            if (!styleProfile.value) { alert('请先完成风格分析'); return; }
            genLoading.value = true;
            try {
                const d = await apiPost('/api/ai/generate', {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    styleProfile: styleProfile.value, genre: genForm.genre || '未指定',
                    count: genForm.count || 3, protagonist: genForm.protagonist || '未指定',
                    world: genForm.world || '未指定', outline: genForm.outline || '未指定'
                });
                genResult.value = d.result;
            } catch(e) {
                alert('生成失败: ' + e.message);
            }
            genLoading.value = false;
        }

        function saveGenerated() {
            if (!genResult.value) return;
            const blob = new Blob(['\uFEFF' + genResult.value], { type: 'text/plain;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'AI仿写.txt';
            a.click();
            setTimeout(() => URL.revokeObjectURL(a.href), 2000);
        }

        // ====== 网文技法（Craft）======
        const craftTab = ref('detect');
        const craftSource = ref('paste');
        const craftText = ref('');
        const craftModelIdx = ref(0);
        const craftLoading = ref(false);
        const craftSavedBooks = ref([]);
        const selectedCraftBook = ref('');
        const detectResult = ref(null);
        const fixedContent = ref('');
        const deconstructResult = ref(null);
        const qualityResult = ref(null);

        function getCraftModel() {
            return models.value[craftModelIdx.value] || models.value[0];
        }

        async function loadCraftSavedBooks() {
            try {
                const d = await api('/api/downloads/list', {});
                craftSavedBooks.value = d.books || [];
            } catch(e) { craftSavedBooks.value = []; }
        }

        async function selectCraftBook(b) {
            selectedCraftBook.value = b.book_id;
            try {
                const d = await api('/api/downloads/content', { book_id: b.book_id });
                craftText.value = (d.content || '').slice(0, 10000);
            } catch(e) { craftText.value = ''; }
        }

        async function getCraftContent() {
            if (craftSource.value === 'saved' && selectedCraftBook.value) {
                const d = await api('/api/downloads/content', { book_id: selectedCraftBook.value });
                return d.content || '';
            }
            return craftText.value.trim();
        }

        async function runDetectAI() {
            const m = getCraftModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!craftText.value.trim()) { alert('请先输入小说文本'); return; }
            craftLoading.value = true;
            detectResult.value = null;
            fixedContent.value = '';
            try {
                const content = await getCraftContent();
                const d = await apiPost('/api/novel/craft/detect-ai', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content });
                detectResult.value = d;
            } catch(e) {
                alert('检测失败: ' + e.message);
            }
            craftLoading.value = false;
        }

        async function runFixAI() {
            const m = getCraftModel();
            if (!m || !detectResult.value) return;
            craftLoading.value = true;
            try {
                const d = await apiPost('/api/novel/craft/fix-ai', {
                    endpoint: m.endpoint, apiKey: m.apiKey, model: m.model,
                    content: craftText.value.trim(),
                    issues: detectResult.value.issues || []
                });
                fixedContent.value = d.content;
            } catch(e) {
                alert('修复失败: ' + e.message);
            }
            craftLoading.value = false;
        }

        function copyFixed() {
            navigator.clipboard.writeText(fixedContent.value).then(() => alert('已复制到剪贴板'));
        }

        async function runDeconstruct() {
            const m = getCraftModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!craftText.value.trim()) { alert('请先输入前三章内容'); return; }
            craftLoading.value = true;
            deconstructResult.value = null;
            try {
                const content = await getCraftContent();
                const d = await apiPost('/api/novel/craft/golden-three', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content });
                deconstructResult.value = d;
            } catch(e) {
                alert('拆解失败: ' + e.message);
            }
            craftLoading.value = false;
        }

        async function runQualityScore() {
            const m = getCraftModel();
            if (!m) { alert('请先配置AI模型'); return; }
            if (!craftText.value.trim()) { alert('请先输入小说文本'); return; }
            craftLoading.value = true;
            qualityResult.value = null;
            try {
                const content = await getCraftContent();
                const d = await apiPost('/api/novel/craft/quality-score', { endpoint: m.endpoint, apiKey: m.apiKey, model: m.model, content, title: '用户输入', genre: '' });
                qualityResult.value = d;
            } catch(e) {
                alert('评分失败: ' + e.message);
            }
            craftLoading.value = false;
        }

        onMounted(() => {
            loadModels();
            document.addEventListener('keydown', handleEscKey);
        });

        function handleEscKey(e) {
            if (e.key === 'Escape' && showSettings.value) {
                closeSettings();
            }
        }

        return {
            activeTab, models, activeModelId, showSettings, showAddForm, editingId, form, formValidation,
            loadModels, setActiveModel, getActiveModel, closeSettings, startAddModel, cancelEdit,
            editModel, deleteModel, saveModel, fillPreset, addPresetModel, handleEscKey,
            searchQuery, searchLoading, searchResults, searchError, bookCounts, book,
            dlState, dlCurrent, dlTotal, dlPct, dlStatusText, dlSessionId,
            doSearch, selectBook, resetSearch, startDownload, doPause, doResume, saveFile, apiPostStream,
            stepLabels, novel, novelModelId, inspireLoading, inspireError,
            inspireTitleOptions, inspireDescOptions, charsLoading, outlineLoading,
            chapterLoading, chapterProgress,
            styleExpanded, styleTab, styleText, styleLoading, savedBooks, selectedSavedBook, savedBookAnalyzing,
            showStep, hasStepContent, canGoToStep, getNovelModel,
            generateInspire, selectInspireTitle, selectInspireDesc,
            generateWorld, generateChars, generateOutline, generateNextChapter, generateAllChapters, exportNovel,
            styleProfileSummary, analyzeStyleText, loadSavedBooks, analyzeSavedBook,
            analyzeTab, analyzeText, analyzeModelIdx, analyzeLoading, analyzeResult, analyzeResultLines,
            analyzeSavedBooks, selectedAnalyzeBook, analyzeBookContent, styleProfile,
            loadAnalyzeSavedBooks, selectAnalyzeBook, runAnalyze,
            generateModelIdx, genForm, genLoading, genResult, genChapters, runGenerate, saveGenerated,
            // Craft
            craftTab, craftSource, craftText, craftModelIdx, craftLoading,
            craftSavedBooks, selectedCraftBook, getCraftModel, loadCraftSavedBooks, selectCraftBook,
            detectResult, fixedContent, deconstructResult, qualityResult,
            runDetectAI, runFixAI, copyFixed, runDeconstruct, runQualityScore,
            // Chapter generation
            customPrompt,
            dbChapters, regenerateChapter,
            genStopFlag, genPauseFlag, genStats,
            pauseGeneration, resumeGeneration, stopGenerationBtn, exportNovelFromDb,
            _fmtTime, _getElapsed, _getTotalTime, _getAvgTime, _formatWordCount,
            // Outline management
            dbOutlines, bookOverview, outlineLoading,
            outlineGenStats, outlineStopFlag, outlinePauseFlag,
            generateBookOverview, generateAllChapterOutlines, generateChapterOutline,
            pauseOutlineGeneration, resumeOutlineGeneration, stopOutlineGenerationBtn,
            loadOutlinesFromDb, deleteOutlineFromDb,
            parseOutline, saveOutlineToDb, saveChapterToDb,
            _getOutlineElapsed, _getOutlineTotalTime, _getOutlineAvgTime,
            // Step summaries
            saveStepSummary, loadStepSummaries,
            // Progress tracking
            genProgress, genStart, genEnd, genUpdate,
            // Project management
            currentProjectId, currentProjectName, projects, showProjectModal,
            saveNameInput, saveStatus,
            saveProject, openLoadModal, loadProject, deleteProject, newProject, scheduleAutoSave
        };
    }
}).mount('#app');
