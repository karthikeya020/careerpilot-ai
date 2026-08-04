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
  onboarding_completed: boolean;
  primary_target_role: TargetRoleOut | null;
  career_goals: CareerGoalOut[];
  target_roles: TargetRoleOut[];
}

export interface SkillOut {
  id: string;
  name: string;
  category: string;
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
}

export interface AssessmentQuestionOptionOut {
  id: string;
  text: string;
}

export interface QuestionOut {
  id: string;
  question_type: "multiple_choice" | "multiple_selection" | "short_answer" | "code_reading" | "concept_explanation";
  prompt: string;
  options: AssessmentQuestionOptionOut[] | null;
  difficulty: number;
  concept_name: string;
}

export interface QuestionResponseOut {
  id: string;
  question_id: string;
  is_correct: boolean | null;
  score: number | null;
  ai_evaluated: boolean;
}

export interface AttemptProgressOut {
  attempt_id: string;
  response: QuestionResponseOut | null;
  next_question: QuestionOut | null;
  is_complete: boolean;
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
  sections: ResumeSectionOut[];
  resume_skills: ResumeSkillOut[];
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

export type InterviewMode = "hr" | "technical" | "resume" | "role_specific" | "company_context" | "mixed";

export interface InterviewQuestionOut {
  id: string;
  order_index: number;
  mode: InterviewMode;
  prompt: string;
  question_source: string;
}

export interface InterviewAnswerOut {
  id: string;
  question_id: string;
  transcript: string;
  transcript_source: "typed" | "live_stt" | "deterministic_demo" | "unavailable";
  audio_duration_seconds: number | null;
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
  question: InterviewQuestionOut;
  answer: InterviewAnswerOut;
  evaluation: InterviewEvaluationOut | null;
}

export interface InterviewReplayOut {
  session: InterviewSessionOut;
  items: InterviewReplayItemOut[];
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
