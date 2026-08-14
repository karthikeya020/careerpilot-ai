export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id: string;
  };
}

export interface UserOut {
  id: string;
  email: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserOut;
}

export interface TargetRoleOut {
  id: string;
  title: string;
  seniority: string;
  is_primary: boolean;
}

export interface CareerGoalOut {
  id: string;
  description: string;
  timeline_months: number | null;
  is_active: boolean;
}

export interface StudentProfileOut {
  id: string;
  full_name: string;
  date_of_birth: string | null;
  college_year: string | null;
  branch: string | null;
  github_username: string | null;
  camera_consent: boolean;
  onboarding_completed: boolean;
  primary_target_role: TargetRoleOut | null;
  career_goals: CareerGoalOut[];
  target_roles: TargetRoleOut[];
}

export type GithubProfileStatus = "not_configured" | "ok" | "not_found" | "unavailable";

export interface GithubRepoOut {
  name: string;
  html_url: string;
  language: string | null;
  stargazers_count: number;
  pushed_at: string | null;
}

export interface GithubActivityDayOut {
  date: string;
  count: number;
}

export interface GithubProfileOut {
  status: GithubProfileStatus;
  username: string | null;
  name: string | null;
  bio: string | null;
  avatar_url: string | null;
  html_url: string | null;
  public_repos: number;
  followers: number;
  account_created_at: string | null;
  language_breakdown: Record<string, number>;
  activity_heatmap: GithubActivityDayOut[];
  top_repos: GithubRepoOut[];
  last_synced_at: string | null;
}

export interface SkillOut {
  id: string;
  name: string;
  category: string;
}

export type JobSector = "faang" | "startup" | "research" | "government" | "consulting" | "finance";

export interface SectorOut {
  slug: JobSector;
  label: string;
  listing_count: number;
}

export interface CompanyJobListingOut {
  id: string;
  company: string;
  title: string;
  sector: JobSector;
  seniority: string;
  package_min_lpa: number;
  package_max_lpa: number;
  description: string;
  emphasis_domains: string[];
  created_at: string;
}

export interface JobListingMatchOut {
  listing: CompanyJobListingOut;
  matched_skills: SkillOut[];
  partial_skills: SkillOut[];
  missing_skills: SkillOut[];
  readiness: number | null;
  is_tracked: boolean;
}

export interface TrackedJobOut {
  id: string;
  created_at: string;
  match: JobListingMatchOut;
}

export interface GapPlanItemOut {
  skill_name: string;
  status: "missing" | "partial";
  estimated_hours: number;
  recommended_resource: { id: string; title: string; url?: string; duration_minutes?: number } | null;
}

export interface JobGapPlanOut {
  listing: CompanyJobListingOut;
  readiness: number | null;
  matched_count: number;
  partial_count: number;
  missing_count: number;
  total_estimated_hours: number;
  weekly_commitment_hours: number;
  estimated_weeks_to_ready: number;
  items: GapPlanItemOut[];
  assumptions: string[];
}

export interface ReadinessComponentOut {
  component_type: string;
  score: number | null;
  confidence: number | null;
  status: "scored" | "insufficient_evidence";
  evidence_count: number;
  explanation: string;
  trend: number | null;
  uncertainty: number | null;
  // twin-v2 small-sample safeguard: evidence_diversity is the count of
  // distinct evidence source types behind this component; is_low_sample and
  // low_sample_notice surface when the score/confidence were shrunk/capped
  // because the evidence is too sparse or too narrowly sourced to support a
  // confident estimate (see docs/implementation/CAREER_TWIN_SCORING.md).
  evidence_diversity: number;
  is_low_sample: boolean;
  low_sample_notice: string | null;
  // twin-v2 freshness safeguard: stale_evidence_fraction is the share of
  // this component's evidence older than 6 months at scoring time;
  // is_stale_evidence/stale_evidence_notice surface when a majority is
  // stale and confidence was capped as a result.
  stale_evidence_fraction: number;
  is_stale_evidence: boolean;
  stale_evidence_notice: string | null;
  // Ripple-effect: other components whose evidence overlaps this one's.
  ripple_notes: RippleNoteOut[];
  // Evidence provenance: this component's evidence weight broken down by
  // evidence_type, normalized to fractions that sum to ~1.0.
  provenance: Record<string, number>;
}

export interface RippleNoteOut {
  target_component: string;
  reason: string;
}

export interface CareerTwinSnapshotOut {
  id: string;
  version: number;
  overall_score: number | null;
  overall_confidence: number | null;
  evidence_count: number;
  formula_version: string;
  change_summary: string;
  score_delta: number | null;
  created_at: string;
  components: ReadinessComponentOut[];
  // Quiet, purely self-comparative milestone callouts (Constitution rule 6:
  // no leaderboard, no cross-student comparison).
  milestones: string[];
}

export interface RoleAlignmentOut {
  role_title: string;
  alignment: number;
  matched_skills: string[];
  missing_skills: string[];
}

export type ProjectionStatus = "already_at_target" | "insufficient_history" | "not_improving" | "projected";

export interface ComponentProjectionOut {
  component_type: string;
  current_score: number | null;
  status: ProjectionStatus;
  weeks_to_target: number | null;
  weeks_to_target_low: number | null;
  weeks_to_target_high: number | null;
  weekly_rate: number | null;
  note: string;
}

export interface EvidenceCitationOut {
  skill_name: string;
  evidence_type: string;
  explanation: string;
  created_at: string;
}

export interface ComponentProofOut {
  component_type: string;
  score: number | null;
  confidence: number | null;
  status: string;
  evidence_count: number;
  citations: EvidenceCitationOut[];
}

export interface SnapshotProofOut {
  student_name: string;
  target_role: string | null;
  version: number;
  created_at: string;
  overall_score: number | null;
  overall_confidence: number | null;
  formula_version: string;
  components: ComponentProofOut[];
  disclaimer: string;
}

export interface LearningMissionOut {
  id: string;
  title: string;
  description: string;
  target_skill: SkillOut | null;
  source_component: string;
  status: "pending" | "in_progress" | "completed" | "dismissed";
  created_at: string;
  completed_at: string | null;
}

export interface GraphPathStepOut {
  step_type: "student" | "question" | "concept" | "concept_dependency" | "job_role" | "resource" | "inference";
  label: string;
  node_id: string | null;
  is_inference: boolean;
}

export type GraphSourceOut = "neo4j" | "relational_fallback";

export interface RootCauseResultOut {
  graph_source: GraphSourceOut;
  concept_slug: string;
  path: GraphPathStepOut[];
  missing_context_warning: boolean;
  confidence: number;
  target_role_relevance: string[];
  recommended_resource_ids: string[];
}

export interface GraphNodeOut {
  id: string;
  label: string;
  type: GraphPathStepOut["step_type"];
}

export interface GraphEdgeOut {
  source: string;
  target: string;
  relationship: string;
}

export interface GraphSnapshotOut {
  graph_source: GraphSourceOut;
  nodes: GraphNodeOut[];
  edges: GraphEdgeOut[];
}

export type ConceptStatus = "strong" | "developing" | "weak" | "unknown";

export interface ConceptNodeOut {
  slug: string;
  name: string;
  domain_slug: string;
  domain_name: string;
  skill_name: string | null;
  mastery: number | null;
  confidence: number | null;
  status: ConceptStatus;
  evidence_count: number;
  depth: number;
  is_target_role_relevant: boolean;
}

export interface ConceptEdgeOut {
  source: string;
  target: string;
}

export interface SkillGroupOut {
  name: string;
  concept_slugs: string[];
}

export interface ConceptInsightOut {
  concept_slug: string;
  concept_name: string;
  domain_name: string;
  status: ConceptStatus;
  mastery: number | null;
  confidence: number | null;
  evidence_count: number;
  reasoning: string;
  depends_on: string[];
  blocks: string[];
  target_role_relevant: boolean;
  recommended_resource: { id: string; title: string; url?: string | null } | null;
  practice_available: boolean;
  questions_answered: number;
  questions_total: number;
}

export interface StudentGraphOverviewOut {
  graph_source: GraphSourceOut;
  nodes: ConceptNodeOut[];
  edges: ConceptEdgeOut[];
  skills: SkillGroupOut[];
  strengths: ConceptInsightOut[];
  weaknesses: ConceptInsightOut[];
  concepts_with_evidence: number;
  total_concepts: number;
  overall_mastery: number | null;
  target_role_title: string | null;
}

export interface PracticeQuestionOut {
  id: string;
  question_type: "multiple_choice" | "multiple_selection" | "short_answer" | "code_reading" | "concept_explanation";
  prompt: string;
  options: AssessmentQuestionOptionOut[] | null;
  difficulty: number;
  difficulty_band: DifficultyBand;
}

export interface PracticeProgressOut {
  attempt_id: string;
  concept_slug: string;
  is_correct: boolean | null;
  score: number | null;
  explanation: string;
  next_question: PracticeQuestionOut | null;
  is_complete: boolean;
  answered_in_concept: number;
  total_in_concept: number;
}

export interface AgentRunOut {
  id: string;
  agent_name: string;
  prompt_version: string;
  confidence: number;
  evidence_citations: string[];
  inference_type: "deterministic_calculation" | "model_inference" | "extracted_fact" | "user_claim";
  status: "completed" | "failed";
  latency_ms: number;
  created_at: string;
  // GraphRAG agent runs carry a `graph_source` field here ("neo4j" or
  // "relational_fallback") so the Trust Center can label which data path
  // actually produced a root-cause result.
  output_payload: Record<string, unknown>;
}

export interface CareExecutionSummaryOut {
  id: string;
  task_type: string;
  route: "deterministic" | "single_agent" | "graphrag_agent" | "multi_agent" | "critic_reflection" | "human_review";
  confidence: number;
  agents_invoked: string[];
  retrieval_used: boolean;
  reflection_used: boolean;
  requires_human_review: boolean;
  final_status: string;
  created_at: string;
}

export interface CareExecutionDetailOut extends CareExecutionSummaryOut {
  request_summary: string;
  input_evidence_ids: string[];
  routing_factors: Record<string, unknown>;
  reasoning_summary: string;
  agreement: number | null;
  cost_usd: number;
  latency_ms: number;
  policy_version: string;
  agent_runs: AgentRunOut[];
}

export interface ComponentDiffOut {
  component_type: string;
  previous_score: number | null;
  current_score: number | null;
  delta: number | null;
  evidence_count: number;
  evidence_ids: string[];
  explanation: string;
}

export interface TwinChangeExplanationOut {
  snapshot_id: string;
  version: number;
  overall_score: number | null;
  overall_confidence: number | null;
  score_delta: number | null;
  change_summary: string;
  formula_version: string;
  component_diffs: ComponentDiffOut[];
}

export interface AssessmentDomainOut {
  id: string;
  slug: string;
  name: string;
  description: string;
  question_count: number;
  recommended: boolean;
  matched_skills: string[];
}

export interface AssessmentQuestionOptionOut {
  id: string;
  text: string;
}

export type DifficultyBand = "easy" | "medium" | "hard";

export interface QuestionOut {
  id: string;
  question_type: "multiple_choice" | "multiple_selection" | "short_answer" | "code_reading" | "concept_explanation";
  prompt: string;
  options: AssessmentQuestionOptionOut[] | null;
  difficulty: number;
  difficulty_band: DifficultyBand;
  concept_name: string;
}

export interface QuestionResponseOut {
  id: string;
  question_id: string;
  is_correct: boolean | null;
  score: number | null;
  ai_evaluated: boolean;
  explanation: string;
}

export interface AttemptProgressOut {
  attempt_id: string;
  response: QuestionResponseOut | null;
  next_question: QuestionOut | null;
  is_complete: boolean;
  domain_exhausted: boolean;
  answered_in_domain: number;
  total_in_domain: number;
}

export interface ActivityDayOut {
  date: string;
  count: number;
  correct_count: number;
}

export interface ActivityDayDetailOut {
  response_id: string;
  question_id: string;
  prompt: string;
  domain_name: string;
  concept_name: string;
  difficulty: number;
  difficulty_band: DifficultyBand;
  question_type: string;
  is_correct: boolean | null;
  score: number | null;
  submitted_at: string;
}

export interface DomainAccuracyOut {
  domain: string;
  accuracy: number;
  answered: number;
}

export interface DifficultyAccuracyOut {
  band: DifficultyBand;
  accuracy: number;
  answered: number;
}

export interface ScoreTrendPointOut {
  date: string;
  avg_score: number;
}

export interface AssessmentAnalyticsOut {
  total_answered: number;
  total_correct: number;
  overall_accuracy: number | null;
  accuracy_by_domain: DomainAccuracyOut[];
  accuracy_by_difficulty: DifficultyAccuracyOut[];
  score_trend: ScoreTrendPointOut[];
  current_streak_days: number;
  longest_streak_days: number;
  active_day_count: number;
}

export interface AssessmentAttemptOut {
  id: string;
  domain: AssessmentDomainOut;
  status: "in_progress" | "completed";
  score: number | null;
  confidence: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface ResourceOut {
  id: string;
  title: string;
  provider: string;
  url: string;
  resource_type: string;
  difficulty: number;
  duration_minutes: number;
  quality_score: number;
  language: string;
  cost: string;
  source_verified: boolean;
  description: string;
}

export interface ResumeSectionOut {
  id: string;
  section_type: string;
  heading: string;
  raw_text: string;
  order_index: number;
}

export interface ResumeSkillOut {
  skill: SkillOut;
  confidence: number;
  evidence_snippet: string;
}

export interface ResumeOut {
  id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  parsing_status: "pending" | "parsed" | "failed";
  parsing_error: string | null;
  uploaded_at: string;
  parsed_at: string | null;
  is_active: boolean;
  superseded_at: string | null;
  sections: ResumeSectionOut[];
  resume_skills: ResumeSkillOut[];
}

export interface ResumeSummaryOut {
  id: string;
  original_filename: string;
  file_size: number;
  parsing_status: "pending" | "parsed" | "failed";
  uploaded_at: string;
  parsed_at: string | null;
  is_active: boolean;
  superseded_at: string | null;
  skill_count: number;
}

export type BulletStrength = "strong" | "moderate" | "weak";

export interface BulletGradeOut {
  section_type: string;
  text: string;
  strength: BulletStrength;
  has_action_verb: boolean;
  has_metric: boolean;
  has_outcome_language: boolean;
  fix_suggestion: string | null;
}

export interface SelfConsistencyFlagOut {
  skill_id: string;
  skill_name: string;
  message: string;
}

export interface ParseabilityOut {
  score: number;
  warnings: string[];
}

export interface ResumeAnalysisOut {
  has_resume: boolean;
  bullet_grades: BulletGradeOut[];
  self_consistency_flags: SelfConsistencyFlagOut[];
  parseability: ParseabilityOut | null;
  graph_diagnosis: ConceptInsightOut[];
}

export interface RewriteSuggestionOut {
  skill_name: string;
  status: "missing" | "partial";
  has_sufficient_evidence: boolean;
  rewritten_bullet: string | null;
  note: string;
}

export interface RecruiterCardOut {
  has_resume: boolean;
  trust_score: number | null;
  strengths: string[];
  concerns: string[];
  verified_skill_count: number;
  total_skill_count: number;
  parseability_score: number | null;
  bullet_strong_ratio: number | null;
  disclaimer: string;
}

export interface JobRequirementOut {
  id: string;
  requirement_type: "skill" | "experience" | "education" | "responsibility";
  raw_text: string;
  is_required: boolean;
  skill: SkillOut | null;
}

export interface JobDescriptionOut {
  id: string;
  title: string;
  company: string | null;
  raw_text: string;
  source: string;
  created_at: string;
  requirements: JobRequirementOut[];
}

export interface MatchResultOut {
  matched_skills: SkillOut[];
  partial_skills: SkillOut[];
  missing_skills: SkillOut[];
  coverage: number | null;
  confidence: number | null;
  explanation: string;
}

export interface ResumeStatusOut {
  uploaded: boolean;
  filename: string | null;
  parsing_status: string | null;
  parsing_error: string | null;
  skills_detected: number;
  uploaded_at: string | null;
}

export interface JobDescriptionStatusOut {
  added: boolean;
  title: string | null;
  coverage: number | null;
  matched_count: number;
  partial_count: number;
  missing_count: number;
}

export interface EvidenceItemOut {
  id: string;
  skill_name: string;
  evidence_type: string;
  normalized_score: number;
  confidence: number;
  explanation: string;
  created_at: string;
}

export interface TwinUpdateSummaryOut {
  version: number;
  overall_score: number | null;
  score_delta: number | null;
  change_summary: string;
  created_at: string;
}

export interface AuditEventOut {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface SystemTrustOut {
  formula_version: string;
  components_scored: number;
  components_total: number;
  total_evidence_count: number;
}

export type InterviewMode = "hr" | "technical" | "dsa" | "resume" | "role_specific" | "company_context" | "mixed";
export type InterviewDifficulty = "easy" | "medium" | "hard";

export interface InterviewQuestionOut {
  id: string;
  order_index: number;
  mode: InterviewMode;
  prompt: string;
  difficulty: InterviewDifficulty;
  question_source: string;
  is_follow_up: boolean;
  follow_up_rationale: string | null;
}

/** Replay/report-only view -- the round is already over, so it's safe to
 * also reveal the reference answer here (never present on the live
 * InterviewQuestionOut used during the round). */
export interface InterviewReplayQuestionOut extends InterviewQuestionOut {
  model_answer_summary: string;
}

export interface InterviewAnswerOut {
  id: string;
  question_id: string;
  transcript: string;
  transcript_source: "typed" | "live_stt" | "browser_stt" | "deterministic_demo" | "unavailable";
  audio_duration_seconds: number | null;
  audio_mime_type: string | null;
  has_audio: boolean;
  submitted_at: string;
}

export interface TimelineMarkerOut {
  type: string;
  label: string;
  position_percent: number;
}

export interface EvidenceCheckOut {
  claim: string;
  classification:
    | "supported_by_resume_evidence"
    | "partially_supported"
    | "not_currently_supported"
    | "contradicted_by_uploaded_evidence"
    | "insufficient_evidence";
  explanation: string;
}

export interface CommunicationMetricsOut {
  word_count: number;
  filler_word_count: number;
  filler_ratio: number;
  sentence_count: number;
  sentence_completeness_ratio: number;
  speaking_rate_wpm: number | null;
  star_components_found: string[];
  clarity_score: number;
  conciseness_score: number;
  professional_communication_score: number;
  camera_on_ratio: number | null;
}

export interface InterviewEvaluationOut {
  id: string;
  care_execution_id: string | null;
  dimension_scores: Record<string, number>;
  overall_score: number;
  confidence: number;
  agreement: number | null;
  strengths: string[];
  improvements: string[];
  evidence_checks: EvidenceCheckOut[];
  communication_metrics: CommunicationMetricsOut;
  timeline_markers: TimelineMarkerOut[];
  better_answer_framework: string;
  requires_human_review: boolean;
  created_at: string;
}

export interface InterviewSessionOut {
  id: string;
  mode: InterviewMode;
  target_role_id: string | null;
  job_description_id: string | null;
  company_name: string | null;
  status: "in_progress" | "completed";
  overall_score: number | null;
  overall_confidence: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface InterviewProgressOut {
  session: InterviewSessionOut;
  answer: InterviewAnswerOut | null;
  evaluation: InterviewEvaluationOut | null;
  next_question: InterviewQuestionOut | null;
  is_complete: boolean;
}

export interface InterviewReplayItemOut {
  question: InterviewReplayQuestionOut;
  answer: InterviewAnswerOut;
  evaluation: InterviewEvaluationOut | null;
}

export interface DifficultyBreakdownOut {
  difficulty: InterviewDifficulty;
  average_score: number | null;
  question_count: number;
}

export interface CommunicationRollupOut {
  average_filler_ratio: number | null;
  average_clarity_score: number | null;
  average_speaking_rate_wpm: number | null;
  average_camera_on_ratio: number | null;
}

export interface InterviewRoundSummaryOut {
  overall_score: number | null;
  overall_confidence: number | null;
  scripted_question_count: number;
  follow_up_count: number;
  difficulty_breakdown: DifficultyBreakdownOut[];
  dimension_averages: Record<string, number>;
  communication_rollup: CommunicationRollupOut;
  narrative_summary: string;
}

export interface InterviewReplayOut {
  session: InterviewSessionOut;
  items: InterviewReplayItemOut[];
  summary: InterviewRoundSummaryOut;
}

export interface AllocationRequest {
  skill_name: string;
  activity_type: string;
  hours: number;
}

export interface ComponentChangeOut {
  component_type: string;
  current_score: number | null;
  simulated_score: number;
  delta: number;
  confidence: number;
  uncertainty: number;
  assumptions: string[];
  evidence_used: string[];
}

export interface SensitivityFactorOut {
  factor: string;
  label: string;
  swing: number;
}

export interface ExperimentResultOut {
  id: string;
  engine_version: string;
  baseline_snapshot_id: string | null;
  current_overall_score: number | null;
  simulated_overall_score: number | null;
  overall_score_delta: number | null;
  overall_confidence: number;
  overall_uncertainty: number;
  component_changes: ComponentChangeOut[];
  assumptions: string[];
  evidence_used: string[];
  sensitivity: SensitivityFactorOut[];
  waste_notes: string[];
  explanation: string;
  disclaimer: string;
  created_at: string;
}

export interface ExperimentScenarioOut {
  id: string;
  name: string;
  target_role_id: string | null;
  time_horizon_days: number;
  allocations: AllocationRequest[];
  created_at: string;
  result: ExperimentResultOut | null;
}

export interface AllocationPlanItemOut {
  skill_name: string;
  activity_type: string;
  hours: number;
  order_rank: number;
  scheduling_reason: string | null;
}

export interface CalendarWeekOut {
  week_number: number;
  start_date: string;
  items: { skill_name: string; activity_type: string; hours: number }[];
  total_hours: number;
}

export interface CalendarPlanOut {
  weeks: CalendarWeekOut[];
  weekly_hours_budget: number;
  total_hours: number;
  weeks_needed: number;
  deadline: string | null;
  fits_deadline: boolean | null;
  feasibility_note: string | null;
}

export interface MarginalGainPointOut {
  hours: number;
  marginal_gain: number;
  cumulative_gain: number;
}

export interface TargetPlanOut {
  engine_version: string;
  target_component: string;
  target_score: number;
  baseline_score: number | null;
  reached_target: boolean;
  plan: AllocationPlanItemOut[];
  total_hours: number;
  weeks_to_complete: number | null;
  assumptions: string[];
  disclaimer: string;
  calendar: CalendarPlanOut;
  marginal_gain_curve: MarginalGainPointOut[];
}

export interface TargetPlanRequest {
  target_component: string;
  target_score: number;
  candidate_skills: string[];
  weekly_hours?: number;
  deadline?: string | null;
  activity_type?: string;
}

export interface PredictionAccuracyOut {
  status: "measured" | "no_new_evidence_yet" | "no_baseline";
  predicted_delta: number | null;
  actual_delta: number | null;
  absolute_error: number | null;
  days_elapsed: number | null;
  baseline_snapshot_version: number | null;
  current_snapshot_version: number | null;
  message: string;
}

export interface ResponsibleAIVersionsOut {
  care_policy_version: string;
  career_twin_formula_version: string;
  simulation_engine_version: string;
  agent_prompt_versions: Record<string, string>;
}

export interface ResponsibleAIOverviewOut {
  evaluates: string[];
  does_not_evaluate: string[];
  versions: ResponsibleAIVersionsOut;
  human_review: { pending_count: number };
  evidence_provenance: Record<string, number>;
  current_career_twin_confidence: number | null;
  consent: Record<string, unknown>;
  stored_interview_audio_count: number;
  non_claims: string[];
}

export interface RoutingExperimentOut {
  run_id: string;
  dataset_name: string;
  case_count: number;
  agreement_rate_by_variant: Record<string, number>;
  rows: Record<string, unknown>[];
}

export interface GraphVsVectorExperimentOut {
  run_id: string;
  case_count: number;
  indexed_documents: number;
  graph_traversal_accuracy: number | null;
  vector_only_accuracy: number | null;
  rows: Record<string, unknown>[];
  methodology_note: string;
  sample_size_warning: string;
}

export interface AblationSuiteOut {
  harness_version: string;
  ablations: Record<string, Record<string, unknown>>;
  methodology_note: string;
}

export interface EvaluationRunSummaryOut {
  id: string;
  name: string;
  dataset_name: string;
  notes: string;
  created_at: string;
  result_count: number;
}

export interface ReliabilityBinOut {
  bin_start: number;
  bin_end: number;
  count: number;
  mean_confidence: number | null;
  accuracy: number | null;
}

export interface CalibrationReportOut {
  sample_size: number;
  brier_score: number | null;
  expected_calibration_error: number | null;
  bins: ReliabilityBinOut[];
  high_confidence_error_rate: number | null;
  preliminary: boolean;
}

export interface EfficiencyFrontierConditionOut {
  condition: "single_agent_fixed" | "multi_agent_fixed" | "care_adaptive";
  accuracy: number;
  mean_latency_ms: number;
  mean_llm_calls: number;
  cost_usd: number;
}

export interface EfficiencyFrontierOut {
  run_id: string;
  engine_version: string;
  case_count: number;
  frontier: EfficiencyFrontierConditionOut[];
  rows: Record<string, unknown>[];
  cost_note: string;
  preliminary: boolean;
}

export interface ThresholdCombinationOut {
  single_agent_threshold: number;
  multi_agent_threshold: number;
  human_review_threshold: number;
  agreement_rate: number;
}

export interface ThresholdTuningOut {
  run_id: string;
  case_count: number;
  combinations_swept: number;
  current_defaults: ThresholdCombinationOut;
  empirical_best: ThresholdCombinationOut | null;
  matches_current_defaults: boolean;
  current_defaults_tied_for_best: boolean;
  all_results: ThresholdCombinationOut[];
  preliminary: boolean;
  methodology_note: string;
}

export interface AdversarialCaseOut {
  case_id: string;
  category: string;
  input_summary: string;
  confidence: number;
  classification: string;
  passed: boolean;
  note: string;
}

export interface AdversarialSuiteOut {
  engine_version: string;
  case_count: number;
  passed_count: number;
  all_passed: boolean;
  cases: AdversarialCaseOut[];
  methodology_note: string;
}

export interface FallbackFidelityOut {
  engine_version: string;
  measurable: boolean;
  message?: string;
  fake_provider?: string;
  live_provider?: string;
  fake_summary?: string;
  live_summary?: string;
  strength_set_overlap?: number | null;
  methodology_note: string;
}

export interface FairnessPairRowOut {
  pair_id: string;
  variant_a_label: string;
  variant_a_confidence: number;
  variant_a_correctness: number;
  variant_b_label: string;
  variant_b_confidence: number;
  variant_b_correctness: number;
  confidence_delta: number;
  correctness_delta: number;
}

export interface FairnessProbeOut {
  engine_version: string;
  pair_count: number;
  rows: FairnessPairRowOut[];
  max_absolute_correctness_delta: number;
  disclaimer: string;
}

export interface DriftCanaryCaseOut {
  case_id: string;
  baseline_confidence: number;
  current_confidence: number;
  confidence_drift: number;
  baseline_correctness_score: number;
  current_correctness_score: number;
  correctness_drift: number;
  baseline_depth_score: number;
  current_depth_score: number;
  depth_drift: number;
  drifted: boolean;
}

export interface DriftCanaryOut {
  engine_version: string;
  baseline_frozen_at: string;
  baseline_engine: string;
  tolerance: number;
  case_count: number;
  any_drifted: boolean;
  cases: DriftCanaryCaseOut[];
  methodology_note: string;
}

export interface LiveCriticToggleRequest {
  transcript: string;
  question_prompt?: string | null;
  expected_keywords?: string[] | null;
}

export interface LiveCriticToggleOut {
  engine_version: string;
  transcript: string;
  technical_confidence: number;
  communication_confidence: number;
  critic_off_confidence: number;
  critic_on_confidence: number;
  delta: number;
  issues_found: string[];
  verdict: string;
}

export interface ResearchReportOut {
  report_version: string;
  generated_at: string;
  calibration: Record<string, unknown>;
  ablations: Record<string, unknown>;
  efficiency_frontier: Record<string, unknown>;
  threshold_tuning: Record<string, unknown>;
  adversarial_suite: Record<string, unknown>;
  fallback_fidelity: Record<string, unknown>;
  fairness_probe: Record<string, unknown>;
  drift_canary: Record<string, unknown>;
}

export interface CohortSkillGapOut {
  component_type: string;
  average_score: number | null;
  scored_student_count: number;
}

export interface StudentNeedingSupportOut {
  student_profile_id: string;
  full_name: string;
  flagged_decision_count: number;
}

export interface FacultyDashboardOut {
  total_students: number;
  cohort_skill_gaps: CohortSkillGapOut[];
  mission_completion_rate: number | null;
  assessment_completion_rate: number | null;
  average_readiness_trend: number | null;
  students_needing_support: StudentNeedingSupportOut[];
}

export interface ReadinessBucketOut {
  range_start: number;
  range_end: number;
  student_count: number;
}

export interface PlacementDashboardOut {
  student_count_with_snapshot: number;
  readiness_distribution: ReadinessBucketOut[];
  role_alignment_average: number | null;
  common_skill_gaps: CohortSkillGapOut[];
  program_effectiveness_average_delta: number | null;
  disclaimer: string;
}

export interface CandidateComponentOut {
  component_type: string;
  score: number | null;
  confidence: number | null;
  status: string;
}

export interface RecruiterCandidateOut {
  student_profile_id: string;
  full_name: string;
  target_role: string | null;
  overall_score: number | null;
  overall_confidence: number | null;
  components: CandidateComponentOut[];
  requires_human_review: boolean;
  consent_status: string;
}

export interface ServiceHealthOut {
  database: boolean;
  redis: boolean;
  neo4j: boolean;
}

export interface CareExecutionStatsOut {
  total_executions: number;
  route_frequency: Record<string, number>;
  average_confidence: number | null;
  average_latency_ms: number | null;
  average_cost_usd: number | null;
  human_review_rate: number | null;
}

export interface RecentAuditEventOut {
  id: string;
  event_type: string;
  created_at: string;
}

export interface AdminDashboardOut {
  service_health: ServiceHealthOut;
  users_by_role: Record<string, number>;
  total_users: number;
  care_execution_stats: CareExecutionStatsOut;
  recent_audit_events: RecentAuditEventOut[];
}

export interface DashboardOut {
  student_name: string;
  onboarding_completed: boolean;
  target_role: TargetRoleOut | null;
  career_twin: CareerTwinSnapshotOut | null;
  mission: LearningMissionOut | null;
  priority_weakness: ReadinessComponentOut | null;
  resume_status: ResumeStatusOut;
  job_description_status: JobDescriptionStatusOut;
  recent_evidence: EvidenceItemOut[];
  recent_twin_updates: TwinUpdateSummaryOut[];
  recent_audit_events: AuditEventOut[];
  system_trust: SystemTrustOut;
}
