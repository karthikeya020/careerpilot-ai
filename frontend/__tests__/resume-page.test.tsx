import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResumePage from "@/app/resume/page";
import type { ResumeOut, ResumeSummaryOut } from "@/types/api";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/resume",
  useParams: () => ({}),
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

const ACTIVE_RESUME: ResumeOut = {
  id: "resume-b",
  original_filename: "resume-b.docx",
  content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  file_size: 2048,
  parsing_status: "parsed",
  parsing_error: null,
  uploaded_at: "2026-08-06T00:00:00Z",
  parsed_at: "2026-08-06T00:00:05Z",
  is_active: true,
  superseded_at: null,
  sections: [],
  resume_skills: [{ skill: { id: "sk1", name: "Pandas", category: "technical" }, confidence: 0.7, evidence_snippet: "Pandas" }],
};

const HISTORY: ResumeSummaryOut[] = [
  {
    id: "resume-b",
    original_filename: "resume-b.docx",
    file_size: 2048,
    parsing_status: "parsed",
    uploaded_at: "2026-08-06T00:00:00Z",
    parsed_at: "2026-08-06T00:00:05Z",
    is_active: true,
    superseded_at: null,
    skill_count: 1,
  },
  {
    id: "resume-a",
    original_filename: "resume-a.docx",
    file_size: 1024,
    parsing_status: "parsed",
    uploaded_at: "2026-08-05T00:00:00Z",
    parsed_at: "2026-08-05T00:00:05Z",
    is_active: false,
    superseded_at: "2026-08-06T00:00:00Z",
    skill_count: 1,
  },
];

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ResumePage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
});

describe("ResumePage", () => {
  it("shows the active resume badge and a history list with a superseded version", async () => {
    getMock.mockImplementation((path: string) => {
      if (path === "/resumes/me") return Promise.resolve(ACTIVE_RESUME);
      if (path === "/resumes") return Promise.resolve(HISTORY);
      return Promise.reject(new Error(`unexpected path ${path}`));
    });
    renderPage();

    expect(await screen.findByText("resume-b.docx")).toBeInTheDocument();
    expect(screen.getAllByText(/active resume/i).length).toBeGreaterThan(0);
    expect(await screen.findByText("resume-a.docx")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /make active/i })).toBeInTheDocument();
  });

  it("lets the student reactivate an older resume version", async () => {
    getMock.mockImplementation((path: string) => {
      if (path === "/resumes/me") return Promise.resolve(ACTIVE_RESUME);
      if (path === "/resumes") return Promise.resolve(HISTORY);
      return Promise.reject(new Error(`unexpected path ${path}`));
    });
    postMock.mockResolvedValueOnce({ ...ACTIVE_RESUME, id: "resume-a", is_active: true });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("resume-a.docx");
    await user.click(screen.getByRole("button", { name: /make active/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/resumes/resume-a/activate"));
  });
});
