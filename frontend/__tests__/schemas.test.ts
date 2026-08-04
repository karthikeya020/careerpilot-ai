import { describe, expect, it } from "vitest";
import { jobDescriptionSchema, loginSchema, onboardingSchema, registerSchema } from "@/lib/schemas";

describe("registerSchema", () => {
  it("accepts a valid registration", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada Lovelace",
      email: "ada@example.com",
      password: "Password1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a password with no digit", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada Lovelace",
      email: "ada@example.com",
      password: "allletters",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = registerSchema.safeParse({
      fullName: "Ada Lovelace",
      email: "not-an-email",
      password: "Password1",
    });
    expect(result.success).toBe(false);
  });
});

describe("loginSchema", () => {
  it("requires a non-empty password", () => {
    const result = loginSchema.safeParse({ email: "ada@example.com", password: "" });
    expect(result.success).toBe(false);
  });
});

describe("onboardingSchema", () => {
  const valid = {
    full_name: "Ada Lovelace",
    career_goal_description: "Land a backend engineering internship",
    timeline_months: 6,
    target_role_title: "Backend Engineer",
    target_role_seniority: "entry_level" as const,
    self_assessed_skills: [{ skill_name: "Python", rating: 0.5 }],
    consent_data_processing: true,
  };

  it("accepts a fully valid payload", () => {
    expect(onboardingSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects a career goal shorter than 10 characters", () => {
    const result = onboardingSchema.safeParse({ ...valid, career_goal_description: "too short" });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid seniority value", () => {
    const result = onboardingSchema.safeParse({ ...valid, target_role_seniority: "godlike" });
    expect(result.success).toBe(false);
  });

  it("rejects a skill rating outside 0-1", () => {
    const result = onboardingSchema.safeParse({
      ...valid,
      self_assessed_skills: [{ skill_name: "Python", rating: 1.5 }],
    });
    expect(result.success).toBe(false);
  });
});

describe("jobDescriptionSchema", () => {
  it("rejects a job description shorter than 30 characters", () => {
    const result = jobDescriptionSchema.safeParse({ title: "Engineer", raw_text: "too short" });
    expect(result.success).toBe(false);
  });

  it("accepts a well-formed job description", () => {
    const result = jobDescriptionSchema.safeParse({
      title: "Engineer",
      company: "Acme",
      raw_text: "We are looking for a backend engineer with Python experience.",
    });
    expect(result.success).toBe(true);
  });
});
