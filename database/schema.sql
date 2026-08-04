CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'admin', 'faculty', 'placement')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE student_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    target_role TEXT,
    target_companies JSONB NOT NULL DEFAULT '[]'::jsonb,
    career_goal TEXT,
    consent_settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_profile_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    source_id UUID,
    content JSONB NOT NULL,
    reliability NUMERIC(5,4) NOT NULL CHECK (reliability BETWEEN 0 AND 1),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE skill_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_profile_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    score NUMERIC(5,4) NOT NULL CHECK (score BETWEEN 0 AND 1),
    confidence NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    trend TEXT NOT NULL DEFAULT 'stable',
    scoring_rule_version TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_profile_id, skill_id)
);

CREATE TABLE skill_state_evidence (
    skill_state_id UUID NOT NULL REFERENCES skill_states(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    weight NUMERIC(5,4) NOT NULL CHECK (weight BETWEEN 0 AND 1),
    PRIMARY KEY (skill_state_id, evidence_id)
);

CREATE TABLE career_twin_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_profile_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    state JSONB NOT NULL,
    change_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_profile_id, version)
);

CREATE TABLE decision_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_profile_id UUID REFERENCES student_profiles(id) ON DELETE SET NULL,
    task_type TEXT NOT NULL,
    route TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    agreement NUMERIC(5,4) CHECK (agreement BETWEEN 0 AND 1),
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    agents_invoked JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
    reasoning_summary TEXT NOT NULL,
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX evidence_student_idx ON evidence(student_profile_id);
CREATE INDEX skill_states_student_idx ON skill_states(student_profile_id);
CREATE INDEX decision_traces_student_idx ON decision_traces(student_profile_id);
