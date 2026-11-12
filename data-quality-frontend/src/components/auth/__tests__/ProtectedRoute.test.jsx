
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "../ProtectedRoute";
import { useAuth } from "../../../auth/AuthContext";

vi.mock("../../../auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

function renderProtectedRoute(user, booting = false, roles) {
  useAuth.mockReturnValue({ user, booting });

  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute roles={roles}>
              <h1>Protected content</h1>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<h1>Login page</h1>} />
        <Route path="/" element={<h1>Home page</h1>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows loading while authentication is being checked", () => {
    renderProtectedRoute(null, true);

    expect(screen.getByText("Checking session…")).toBeInTheDocument();
  });

  it("redirects unauthenticated users to login", async () => {
    renderProtectedRoute(null);

    expect(await screen.findByText("Login page")).toBeInTheDocument();
  });

  it("allows users with permitted roles", () => {
    renderProtectedRoute({ role: "ADMIN" }, false, ["ADMIN", "OPERATOR"]);

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects users without the required role", async () => {
    renderProtectedRoute({ role: "ANALYST" }, false, ["ADMIN", "OPERATOR"]);

    expect(await screen.findByText("Home page")).toBeInTheDocument();
  });

  it("allows authenticated users when no role restriction exists", () => {
    renderProtectedRoute({ role: "ANALYST" });

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
