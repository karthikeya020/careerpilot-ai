import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "@/app/login/page";
import { ApiError } from "@/lib/api-client";

const { pushMock, loginMock, toastErrorMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  loginMock: vi.fn(),
  toastErrorMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ login: loginMock }),
}));

vi.mock("@/lib/theme-provider", () => ({
  useTheme: () => ({ theme: "dark", toggle: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: toastErrorMock },
}));

beforeEach(() => {
  pushMock.mockClear();
  loginMock.mockClear();
  toastErrorMock.mockClear();
});

describe("LoginPage", () => {
  it("requires an email and password before submitting", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.click(screen.getByRole("button", { name: /log in/i }));

    expect(await screen.findAllByRole("alert")).not.toHaveLength(0);
    expect(loginMock).not.toHaveBeenCalled();
  });

  it("logs in and redirects to the dashboard", async () => {
    loginMock.mockResolvedValueOnce({ id: "1", email: "ada@example.com" });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), "ada@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password1");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledWith("ada@example.com", "Password1"));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dashboard"));
  });

  it("shows a toast on invalid credentials", async () => {
    loginMock.mockRejectedValueOnce(new ApiError(401, "unauthorized", "Invalid email or password"));
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), "ada@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrongpass");
    await user.click(screen.getByRole("button", { name: /log in/i }));

    await waitFor(() => expect(toastErrorMock).toHaveBeenCalledWith("Incorrect email or password."));
    expect(pushMock).not.toHaveBeenCalled();
  });
});
