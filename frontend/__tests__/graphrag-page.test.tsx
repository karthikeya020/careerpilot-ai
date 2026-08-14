import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import GraphRagPage from "@/app/graphrag/page";
import type { PracticeProgressOut, StudentGraphOverviewOut } from "@/types/api";

const { getMock, postMock, searchParamsMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
  searchParamsMock: vi.fn(() => new URLSearchParams()),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/graphrag",
  useSearchParams: () => searchParamsMock(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: { id: "1", email: "student@example.com", roles: ["student"] },
    isLoading: false,
    logout: vi.fn(),
  }),
}));

vi.mock("@/lib/theme-provider", () => ({
  useTheme: () => ({ theme: "dark", toggle: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const OVERVIEW: StudentGraphOverviewOut = {
  graph_source: "relational_fallback",
  nodes: [
    {
      slug: "oop_basics",
      name: "Classes & Objects",
      domain_slug: "oop",
      domain_name: "Object-Oriented Programming",
      skill_name: "Object-Oriented Programming",
      mastery: null,
      confidence: null,
      status: "unknown",
      evidence_count: 0,
      depth: 0,
      is_target_role_relevant: false,
    },
    {
      slug: "polymorphism",
      name: "Polymorphism",
      domain_slug: "oop",
      domain_name: "Object-Oriented Programming",
      skill_name: "Object-Oriented Programming",
      mastery: 0.3,
      confidence: 0.4,
      status: "weak",
      evidence_count: 3,
      depth: 2,
      is_target_role_relevant: true,
    },
  ],
  edges: [{ source: "polymorphism", target: "oop_basics" }],
  skills: [{ name: "Object-Oriented Programming", concept_slugs: ["oop_basics", "polymorphism"] }],
  strengths: [],
  weaknesses: [
    {
      concept_slug: "polymorphism",
      concept_name: "Polymorphism",
      domain_name: "Object-Oriented Programming",
      status: "weak",
      mastery: 0.3,
      confidence: 0.4,
      evidence_count: 3,
      reasoning: "Based on 3 pieces of real evidence, your mastery of Polymorphism is 30% (confidence 40%).",
      depends_on: ["Inheritance"],
      blocks: [],
      target_role_relevant: true,
      recommended_resource: null,
      practice_available: true,
      questions_answered: 3,
      questions_total: 3,
    },
  ],
  concepts_with_evidence: 1,
  total_concepts: 2,
  overall_mastery: 0.3,
  target_role_title: "Backend Engineering Intern",
};

function mockOverviewEndpoints() {
  getMock.mockImplementation((url: string) => {
    if (url === "/graph/student-overview") return Promise.resolve(OVERVIEW);
    if (url === "/graph/concept/polymorphism/insight") return Promise.resolve(OVERVIEW.weaknesses[0]);
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <GraphRagPage />
    </QueryClientProvider>,
  );
}

async function openPolymorphismInsight(user: ReturnType<typeof userEvent.setup>) {
  const rows = await screen.findAllByText("Polymorphism");
  const row = rows[rows.length - 1];
  const button = row.closest("button");
  await user.click(button ?? row);
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  searchParamsMock.mockReturnValue(new URLSearchParams());
});

describe("GraphRagPage", () => {
  it("shows the student's whole knowledge graph by default, never redirecting to assessment", async () => {
    mockOverviewEndpoints();
    renderPage();

    expect(await screen.findByText("Your Knowledge Graph")).toBeInTheDocument();
    expect(screen.getAllByText("Polymorphism").length).toBeGreaterThan(0);
    expect(screen.queryByText(/take an assessment/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /take an assessment/i })).not.toBeInTheDocument();
  });

  it("opens a concept's detailed reasoning when clicked, with a practice option for weak concepts", async () => {
    mockOverviewEndpoints();
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Your Knowledge Graph");
    await openPolymorphismInsight(user);

    expect(await screen.findByText(/Based on 3 pieces of real evidence/i)).toBeInTheDocument();
    expect(screen.getByText("Inheritance")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /practice this concept/i })).toBeInTheDocument();
  });

  it("lets a student practice a weak concept inline, without ever calling an /assessments endpoint", async () => {
    mockOverviewEndpoints();
    postMock.mockResolvedValueOnce({
      attempt_id: "attempt-1",
      concept_slug: "polymorphism",
      is_correct: null,
      score: null,
      explanation: "",
      next_question: {
        id: "q1",
        question_type: "multiple_choice",
        prompt: "What is polymorphism?",
        options: [{ id: "a", text: "One interface, many forms" }],
        difficulty: 2,
        difficulty_band: "easy",
      },
      is_complete: false,
      answered_in_concept: 0,
      total_in_concept: 3,
    } satisfies PracticeProgressOut);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Your Knowledge Graph");
    await openPolymorphismInsight(user);
    await user.click(await screen.findByRole("button", { name: /practice this concept/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/graph/practice/polymorphism/start", {}));
    expect(await screen.findByText("What is polymorphism?")).toBeInTheDocument();
    expect(postMock.mock.calls.some(([url]) => String(url).startsWith("/assessments"))).toBe(false);
  });

  it("still supports the per-question root-cause deep link from Interview/Assessment Arena", async () => {
    searchParamsMock.mockReturnValue(new URLSearchParams("question=q1"));
    getMock.mockImplementation((url: string) => {
      if (url === "/graph/health") return Promise.resolve({ available: false });
      if (url === "/graph/root-cause/q1") {
        return Promise.resolve({
          graph_source: "relational_fallback",
          concept_slug: "inner_join",
          path: [{ step_type: "student", label: "You answered a question incorrectly", node_id: "s1", is_inference: false }],
          missing_context_warning: false,
          confidence: 0.8,
          target_role_relevance: [],
          recommended_resource_ids: [],
        });
      }
      if (url === "/resources") return Promise.resolve([]);
      return Promise.resolve(null);
    });
    renderPage();

    expect(await screen.findByText("Root cause for this question")).toBeInTheDocument();
    expect(screen.getByText(/back to your knowledge graph/i)).toBeInTheDocument();
  });
});
