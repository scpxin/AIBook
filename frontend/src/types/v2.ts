// V2 Type Definitions — 灵感/世界观/角色/故事/力量/势力/时间线/卷/剧情/章节/场景/正文/伏笔/知识库/一致性

// ========== M1: 灵感 ==========
export interface IdeaCandidate {
  index: number
  concept: string
  hook: string
  premise: string
  genre: string
  differentiator: string
  referenceWorks: string[]
}

export interface IdeaScore {
  index: number
  innovation: number
  commercial: number
  sustainability: number
  differentiation: number
  difficulty: number
  totalScore: number
  rationale: string
}

export interface IdeaUpgrade {
  index: number
  originalConcept: string
  upgradedConcept: string
  coreConflict: string
  limitations: string[]
  foreshadowHints: string[]
  growthSystem: string
}

export interface RiskItem {
  dimension: string
  level: string
  description: string
  suggestion: string
}

export interface RiskAnalysis {
  overallRisk: string
  risks: RiskItem[]
  fatalIssues: string[]
  summary: string
}

// ========== M2: 项目定位 ==========
export interface NovelPosition {
  targetAudience?: Record<string, any>
  coreHook?: string
  noveltyAngle?: string
  emotionalResonance?: string
  updateStrategy?: string
  titleDirection?: string[]
  coverConcept?: string
  openerStrategy?: string
  mainConflict?: string
  subplotCount?: number
  climaxPattern?: string
  endingDirection?: string
  [key: string]: any
}

export interface PlatformCompatibility {
  score: number
  fit: string
  pros: string[]
  cons: string[]
  adjustment: string
}

export interface DerivedFields {
  estimatedChapters: number
  estimatedWords: number
  titleKeywords: string[]
  contentTags: string[]
  seriesPotential: string
}

// ========== M3: 世界观 ==========
export interface WorldRule {
  name: string
  description: string
  scope: string
  cost: string
  exception: string
  evidence: string
}

export interface WorldLayer {
  name: string
  description: string
  characteristics: string
  connections: string[]
}

export interface LandmarkLocation {
  name: string
  type: string
  significance: string
  geography: string
}

export interface CivilizationDimension {
  name: string
  description: string
  keyFeatures: string[]
}

export interface HistoryEvent {
  era: string
  yearRange: string
  event: string
  impact: string
  aftermath: string
}

export interface WorldOrigin {
  cosmology: string
  fundamentalForces: string[]
  creationMyth: string
  worldViews: string[]
  chaosOrder: string
}

export interface WorldBuilding {
  origin?: WorldOrigin | string
  rules?: WorldRule[]
  structure?: {
    dimensions?: WorldLayer[]
    realms?: any[]
    landmarkLocations?: LandmarkLocation[]
    spatialRules?: string
  }
  civilization?: Record<string, any>
  history?: {
    timelineEvents?: HistoryEvent[]
    ancientMysteries?: string[]
    prophecySystem?: string[]
    declineCycles?: string
  }
  docPath?: string
  worldForeshadows?: any
}

export interface WorldConsistencyCheck {
  passed: boolean
  score: number
  issues: Array<{ type: string; severity: string; description: string; fix: string }>
  summary: string
}

// ========== M4: 角色 ==========
export interface CharacterBasicInfo {
  name: string
  age: number
  gender: string
  nationality: string
  appearance: string
  birth: string
}

export interface CharacterPersonality {
  traits: string[]
  mbti: string
  strengths: string[]
  flaws: string[]
  contradictions: string[]
}

export interface CharacterBackstory {
  origin: string
  childhoodTrauma: string
  turningPoint: string
  secret: string
}

export interface CharacterMotivation {
  outerGoal: string
  innerNeed: string
  literalWish: string
  trueDesire: string
}

export interface CharacterAbility {
  initialPower: string
  signatureSkill: string
  growthRoute: string[]
  limits: string[]
  awakening: string
}

export interface CharacterArcItem {
  zeroState: string
  awakening: string
  setback: string
  breakthrough: string
  finalState: string
}

export interface Character {
  charId?: string
  name: string
  roleType: string
  basicInfo?: CharacterBasicInfo
  personality?: CharacterPersonality
  backstory?: CharacterBackstory
  motivation?: CharacterMotivation
  abilities?: CharacterAbility
  relationships?: any
  characterArc?: CharacterArcItem
  voice?: any
  symbols?: any
  [key: string]: any
}

export interface RelationMap {
  edges: Array<{ source: string; target: string; type: string; intensity: number; description: string; dynamic: string }>
  factions: Array<{ groupName: string; members: string[]; goal: string; internalDynamic: string }>
  lovePolygon: any[]
  hiddenConnections: any[]
}

export interface CharacterConsistencyCheck {
  passed: boolean
  score: number
  issues: Array<{ char: string; type: string; description: string }>
  summary: string
}

// ========== M5: 故事 ==========
export interface ConflictItem {
  name: string
  description: string
  level: string
  chapters: string
}

export interface PlotEvent {
  event: string
  trigger: string
  consequence: string
  chapterHint: string
}

export interface VolumeOutline {
  volumeNo: number
  title: string
  theme: string
  wordcountTarget: number
  mainEvents: Array<{ eventName: string; significance: string }>
  characterFocus: string[]
  cliffhanger: string
  arcContribution: string
}

export interface StoryMaster {
  theme: string
  conflictHierarchy: {
    mainConflict: ConflictItem
    secondaryConflicts: ConflictItem[]
    internalConflicts: ConflictItem[]
  }
  eventChain: PlotEvent[]
  emotionalArc: any
  narrativePromise: string
  stakes: string[]
  climaxSetup: any
  endingType: string
  rewatchHooks: string[]
  volumeStructure: any
}

// ========== M6: 力量体系 ==========
export interface PowerTier {
  name: string
  threshold: string
  abilities: string[]
  lifespan: string
  powerDescription: string
}

export interface CombatCategory {
  category: string
  styles: string[]
  counters: string[]
  specialMoves: string[]
}

export interface Bottleneck {
  stage: string
  manifestation: string
  breakthroughMethod: string
  percentStuck: number
  significance: string
}

export interface PowerSystem {
  tiers: PowerTier[]
  combatCategories: CombatCategory[]
  growthMethod: Record<string, any>
  limits: any[]
  bottlenecks: Bottleneck[]
  resources?: any[]
}

// ========== M7: 势力 ==========
export interface Faction {
  name: string
  title?: string
  factionType?: string
  tier?: string
  territory?: string
  leaderInfo?: Record<string, any>
  powerBase?: Record<string, any>
  resourceControl?: any
  foreignRelations?: any
  internalConflicts?: any
  plotFunction?: string
  secrets?: string[]
  fateArc?: string
  factionId?: string
  [key: string]: any
}

// ========== M8: 时间线 ==========
export interface TimelineEvent {
  year: number
  era: string
  event: string
  type: string
  impact: string
  description: string
}

export interface EraDefinition {
  name: string
  start: number
  end: number
  characteristics: string
}

export interface Timeline {
  events: TimelineEvent[]
  timeConversion: string
  eraDefinitions: EraDefinition[]
  consistencyStatus: { conflicts: any[]; gaps: any[]; resolved: boolean }
}

// ========== M9: 全书大纲 ==========
export interface OutlinePhase {
  phase: string
  mainProgress: string
  characterChange: string
  wordcount: number
}

export interface MasterOutline {
  opening: any
  risingActions: OutlinePhase[]
  subplots: any[]
  midpointTurn: any
  climaxBuildup: any
  finalClimax: any
  endingType: string
  rewatchHooks: string[]
  volumeStructure: any
}

// ========== M10-M13: 规划层 ==========
export interface ChapterBreakdown {
  chapterNo: number
  title: string
  hook: string
  mainEvent: string
  cliffhanger: string
  wordcount: number
}

export interface VolumeDetail {
  volumeNo: number
  title: string
  theme: string
  wordcountTarget: number
  storyArc?: any
  chapterBreakdown?: ChapterBreakdown[]
  characterFocus?: string[]
  powerProgress?: any
  worldExposure?: any
  foreshadowPlan?: any
  emotionalCurve?: any
  subplotThreads?: any[]
  [key: string]: any
}

export interface PlotEventDetail {
  eventId: string
  title: string
  trigger: string
  scenes: any[]
  turningPoint: any
  consequences: any
  emotionalBeats: any
  knowledgeUpdate: any
  foreshadowTriggers: any
}

export interface ChapterPlan {
  chapterNo: number | string
  events: string[]
  targetWords: number
  hook: string
  cliffhangerType?: string
  title?: string
  summary?: string
  pacing?: string
  outline?: ChapterOutline
  [key: string]: any
}

export interface SceneOutline {
  sceneNo: number
  location: string
  characters: string[]
  goal: string
  conflict: any
  outcome: string
  sensoryDetails: string
}

export interface ChapterOutline {
  chapterNo: number | string
  scenes: SceneOutline[]
  emotionalCurve: any
  povShifts: any[]
  foreshadowOps: any
  knowledgeOps: any
  dialogueBeats: any[]
  actionBeats: any[]
  transition: string
}

// ========== M14: 场景 ==========
export interface SceneSkeleton {
  sceneId: string
  title: string
  timeEnvironment: any
  locationDetail: any
  charactersPresent: any[]
  sceneGoal: string
  conflictDesign: any
  actionBeats: any[]
  emotionalFlow: any
  foreshadowOps: any
  sceneEnding: any
  transitionOut: string
}

// ========== M15: 正文 ==========
export interface Draft {
  chapterNo: number
  content: string
  contentRaw: string
  wordCountRaw: number
  wordCountFinal: number
  polishStatus: string
  foreshadowAdded: string[]
  continuityCheck: string
  version: number
  quality?: number
}

export interface DraftStreamChunk {
  type: 'chunk' | 'done' | 'error'
  content: string
  fullLength?: number
  length?: number
  message?: string
}

// ========== M16: 润色 ==========
export interface PolishChange {
  type: string
  position: string
  original: string
  new: string
  reason: string
}

export interface SimilarityMatch {
  source: string
  passage: string
  similarity: number
  suggestion: string
}

export interface PolishResult {
  polishedContent: string
  changes: PolishChange[]
  similarityReport: {
    overallSimilarity: number
    matches: SimilarityMatch[]
  }
  improvementSummary: string
}

// ========== M17: 内容解析 ==========
export interface SceneSegment {
  startPos: number
  endPos: number
  location: string
  characters: string[]
  summary: string
}

export interface DialogueExtraction {
  speaker: string
  listener: string
  content: string
  subtext: string
  emotion: string
  hiddenAgenda: string
}

export interface StatusChange {
  entity: string
  attribute: string
  oldValue: string
  newValue: string
  chapterNo: string
}

export interface ContentParseResult {
  sceneSegments: SceneSegment[]
  dialogueExtractions: DialogueExtraction[]
  actionExtractions: any[]
  statusChanges: StatusChange[]
  foreshadowDetections: any[]
  pacingAnalysis: any
  wordCount: any
}

// ========== M18: 知识库 ==========
export interface KnowledgeState {
  characterStates: Record<string, any>
  worldState: Record<string, any>
  plotState: Record<string, any>
  lastUpdatedChapter?: string
}

// ========== M19: 一致性 ==========
export interface ConsistencyCheckItem {
  dimension: string
  score: number
  issues: any[]
}

export interface CriticalIssue {
  dimension: string
  severity: string
  description: string
  fix: string
}

export interface ConsistencyReport {
  overallScore: number
  passed: boolean
  checks: ConsistencyCheckItem[]
  criticalIssues: CriticalIssue[]
  summary: string
  chapterNo?: string
}

// ========== 流水线 ==========
export type ModuleStatus = 'locked' | 'pending' | 'generating' | 'done' | 'failed'

export interface ModuleState {
  name: string
  displayName: string
  layer: string
  status: ModuleStatus
  startedAt: string | null
  completedAt: string | null
  error: string | null
  retryCount: number
}

export interface PipelineProgress {
  projectId: string
  totalModules: number
  completed: number
  failed: number
  generating: number
  progressPct: number
  currentModule: string
  nextModule: string | null
  modules: Record<string, ModuleState>
  updatedAt: string
}

export interface ModuleInfo {
  name: string
  displayName: string
  layer: string
  dependencies: string[]
  isParallel: boolean
  isIterative: boolean
}
