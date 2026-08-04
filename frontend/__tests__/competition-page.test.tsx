import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CompetitionPage from "@/app/competition/page";

const { getMock, pushMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  pushMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/competition",
  useParams: () => ({}),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <CompetitionPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  pushMock.mockReset();
  getMock.mockResolvedValue(null);
});

describe("CompetitionPage", () => {
  it("opens on the Opening step with the tagline visible", async () => {
    renderPage();
    expect(await screen.findByText("CareerPilot AI")).toBeInTheDocument();
    expect(screen.getByText("The Career Operating System")).toBeInTheDocument();
  });

  it("advances steps with the Next button and the right-arrow key", async () => {
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("CareerPilot AI");
    await user.click(screen.getByRole("button", { name: /^next/i }));
    expect(await screen.findByRole("heading", { level: 2, name: "Meet the Student" })).toBeInTheDocument();

    await user.keyboard("{ArrowRight}");
    await waitFor(() => expect(screen.getByRole("heading", { level: 2, name: "Career Twin Awakening" })).toBeInTheDocument());
  });

  it("resets to the Opening step with the Reset button", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /^next/i }));
    await user.click(screen.getByRole("button", { name: /^next/i }));
    expect(await screen.findByRole("heading", { level: 2, name: "Career Twin Awakening" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /reset/i }));
    expect(await screen.findByText("The Career Operating System")).toBeInTheDocument();
  });

  it("exits to the dashboard when the exit control is used", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /exit competition mode/i }));
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("toggles technical view", async () => {
    const user = userEvent.setup();
    renderPage();

    const toggle = await screen.findByRole("button", { name: /technical view/i });
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });
});
