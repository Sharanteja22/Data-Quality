
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Login from "../Login";
import { login } from "../../api/authApi";
import { useAuth } from "../../auth/AuthContext";

vi.mock("../../api/authApi", () => ({
  login: vi.fn(),
}));

vi.mock("../../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const saveAuth = vi.fn();

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<h1>Dashboard</h1>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Login page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ saveAuth });
  });

  it("renders the login form", () => {
    renderLogin();

    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(screen.getByLabelText("Work email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("logs in successfully and redirects to dashboard", async () => {
    const user = userEvent.setup();

    const response = {
      accessToken: "test-token",
      user: {
        userId: 1,
        fullName: "Test User",
        email: "test@example.com",
        role: "ADMIN",
      },
    };

    login.mockResolvedValue(response);

    renderLogin();

    await user.type(screen.getByLabelText("Work email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "Password123!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "Password123!",
      });
      expect(saveAuth).toHaveBeenCalledWith(response);
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
  });

  it("displays an error when login fails", async () => {
    const user = userEvent.setup();

    login.mockRejectedValue({
      response: {
        data: { message: "Invalid credentials" },
      },
    });

    renderLogin();

    await user.type(screen.getByLabelText("Work email"), "wrong@example.com");
    await user.type(screen.getByLabelText("Password"), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
    expect(saveAuth).not.toHaveBeenCalled();
  });

  it("does not submit when required fields are empty", async () => {
    const user = userEvent.setup();

    renderLogin();

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(login).not.toHaveBeenCalled();
  });
});
