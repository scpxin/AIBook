from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict


def _to_camel(name: str) -> str:
    parts = name.split('_')
    return parts[0] + ''.join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class ProjectSaveRequest(CamelModel):
    id: Optional[str] = None
    name: str = "未命名项目"
    data: Dict[str, Any] = {}
    step: int = 0
    tags: str = ""


class ProjectLoadRequest(CamelModel):
    id: str


class ProjectDeleteRequest(CamelModel):
    id: str


class ChapterSaveRequest(CamelModel):
    projectId: str
    chapterNumber: int
    title: str = ""
    content: str = ""
    status: str = "done"
    errorMessage: str = ""
    metadata: Optional[Any] = None


class ChapterGetRequest(CamelModel):
    projectId: str
    chapterNumber: Optional[int] = None


class ChapterDeleteRequest(CamelModel):
    projectId: str
    chapterNumber: int


class ChapterRegenerateRequest(CamelModel):
    projectId: str
    chapterNumber: int


class GenerationStatusRequest(CamelModel):
    projectId: str


class GenerationStartRequest(CamelModel):
    projectId: str
    totalChapters: int
    endpoint: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    styleProfile: str = ""
    bookOverview: str = ""
    targetWords: int = 3000
    narrativePerspective: str = "第三人称"
    chapterCharacters: str = ""


class GenerationPauseRequest(CamelModel):
    projectId: str


class GenerationStopRequest(CamelModel):
    projectId: str


class GenerationUpdateRequest(CamelModel):
    projectId: str
    currentChapter: int = 0
    completedChapters: Optional[int] = None
    failedChapters: Optional[int] = None


class OutlineSaveRequest(CamelModel):
    projectId: str
    chapterNumber: int
    title: str = ""
    summary: str = ""
    scenes: Optional[List] = None
    characters: Optional[List] = None
    key_points: Optional[List] = None
    emotion: str = ""
    goal: str = ""
    techniqueFocus: str = ""
    bookOverview: str = ""
    chapterHook: str = ""
    acts: Optional[List] = None
    status: str = "done"
    errorMessage: str = ""


class OutlineGetRequest(CamelModel):
    projectId: str
    chapterNumber: Optional[int] = None


class OutlineDeleteRequest(CamelModel):
    projectId: str
    chapterNumber: int


class OutlineGenerationStartRequest(CamelModel):
    projectId: str
    totalChapters: int = 0
    endpoint: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    styleProfile: str = ""
    bookOverview: str = ""
    targetWords: int = 3000
    narrativePerspective: str = "第三人称"
    chapterCharacters: str = ""


class StepSummarySaveRequest(CamelModel):
    projectId: str
    step: str
    summary: Any = {}


class StepSummaryGetRequest(CamelModel):
    projectId: str
    step: Optional[str] = None


class NovelInspirationRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    userInput: str = ""
    title: str = ""
    description: str = ""
    theme: str = ""
    genre: str = ""
    styleProfile: Any = None
    temperature: float = 0.7
    maxTokens: int = 4000


class WorldbuildingRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    title: str = ""
    theme: str = ""
    genre: str = ""
    description: str = ""
    styleProfile: Any = None
    temperature: float = 0.7
    maxTokens: int = 4000


class WorldbuildingReparseRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    worldText: str = ""
    styleProfile: Any = None
    temperature: float = 0.7
    maxTokens: int = 4000


class CharactersReparseRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    charactersText: str = ""
    styleProfile: Any = None
    temperature: float = 0.7
    maxTokens: int = 4000


class CharactersRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    theme: str = ""
    genre: str = ""
    count: int = 6
    requirements: str = ""
    worldData: Any = {}
    styleProfile: Any = None
    novelDescription: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class OutlineRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    title: str = ""
    theme: str = ""
    genre: str = ""
    charactersInfo: Any = ""
    chapterCount: int = 3
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    worldSummary: str = ""
    projectId: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class BookOverviewRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    title: str = ""
    theme: str = ""
    genre: str = ""
    charactersInfo: str = ""
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    worldSummary: str = ""
    inspirationDesc: str = ""
    description: str = ""
    projectId: str = ""
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class ChapterOutlineRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    bookOverview: str = ""
    chapterNumber: int = 1
    totalChapters: int = 1
    charactersInfo: str = ""
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    worldSummary: str = ""
    prevChapterTitle: str = ""
    prevChapterTail: str = ""
    useCraft: bool = False
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class ChapterRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    chapterNumber: int = 1
    chapterTitle: str = ""
    chapterOutline: str = ""
    continuationPoint: str = ""
    previousChapterSummary: str = ""
    chapterCharacters: str = ""
    foreshadowReminders: str = ""
    worldSummary: str = ""
    firstChapterStrategy: str = ""
    targetWordCount: int = 3000
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    techniqueFocus: str = ""
    bookOverview: str = ""
    progressContent: str = ""
    segmentChars: int = 0
    prevChapterHook: str = ""
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class ChapterPolishRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    chapterNumber: int = 1
    chapterTitle: str = ""
    chapterOutline: str = ""
    originalContent: str = ""
    polishFocus: str = "整体优化"
    styleProfile: Any = None
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class ChapterSummarizeRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    chapterTitle: str = ""
    chapterNumber: int = 1
    content: str = ""


class NovelChapterRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    chapterNumber: int = 1
    chapterTitle: str = ""
    chapterOutline: str = ""
    continuationPoint: str = ""
    previousChapterSummary: str = ""
    chapterCharacters: str = ""
    foreshadowReminders: str = ""
    worldSummary: str = ""
    firstChapterStrategy: str = ""
    targetWordCount: int = 3000
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    techniqueFocus: str = ""
    bookOverview: str = ""
    progressContent: str = ""
    segmentChars: int = 0
    prevChapterHook: str = ""
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class CraftChapterRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    projectTitle: str = ""
    genre: str = ""
    chapterNumber: int = 1
    chapterTitle: str = ""
    chapterOutline: str = ""
    continuationPoint: str = ""
    previousChapterSummary: str = ""
    chapterCharacters: str = ""
    foreshadowReminders: str = ""
    worldSummary: str = ""
    firstChapterStrategy: str = ""
    targetWordCount: int = 3000
    narrativePerspective: str = "第三人称"
    styleProfile: Any = None
    techniqueFocus: str = ""
    bookOverview: str = ""
    progressContent: str = ""
    segmentChars: int = 0
    prevChapterHook: str = ""
    stream: bool = False
    temperature: float = 0.7
    maxTokens: int = 4000


class CraftTitlesRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    userInput: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class CraftDescriptionsRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    title: str = ""
    userInput: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class CraftReportRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    content: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class AIAnalyzeRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    content: str = ""


class AIGenerateRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    styleProfile: str = ""
    genre: str = "未指定"
    count: int = 3
    protagonist: str = "未指定"
    world: str = "未指定"
    outline: str = "未指定"


class AITestConnectionRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""


class AnalyzeStyleRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    content: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000


class GenerateStyleRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    styleProfile: str = ""
    genre: str = "未指定"
    count: int = 3
    protagonist: str = "未指定"
    world: str = "未指定"
    outline: str = "未指定"
    targetWordCount: int = 3000
    temperature: float = 0.7
    maxTokens: int = 4000


class AnalyzeChapterRequest(CamelModel):
    endpoint: str = ""
    apiKey: str = ""
    model: str = ""
    chapterNumber: int = 1
    title: str = ""
    content: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000
