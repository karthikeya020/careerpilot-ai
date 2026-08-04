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
