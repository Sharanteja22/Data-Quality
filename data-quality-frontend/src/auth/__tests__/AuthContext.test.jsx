

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth, normalizeUser } from "../AuthContext";
import { getMe } from "../../api/authApi";

vi.mock("../../api/authApi", () => ({
  getMe: vi.fn(),
}));

const wrapper = ({ children }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe("AuthContext", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("starts unauthenticated when no token exists", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.booting).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("restores an existing authenticated session", async () => {
    sessionStorage.setItem("dq_access_token", "existing-token");

    getMe.mockResolvedValue({
      userId: 10,
      fullName: "Test User",
      email: "test@example.com",
      role: "ADMIN",
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.booting).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user.role).toBe("ADMIN");
    expect(sessionStorage.getItem("dq_user")).toContain("Test User");
  });

  it("clears an invalid session", async () => {
    sessionStorage.setItem("dq_access_token", "invalid-token");
    sessionStorage.setItem("dq_user", JSON.stringify({ userId: 1 }));

    getMe.mockRejectedValue(new Error("Unauthorized"));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.booting).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(sessionStorage.getItem("dq_access_token")).toBeNull();
    expect(sessionStorage.getItem("dq_user")).toBeNull();
  });

  it("saves authentication details", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.saveAuth({
        accessToken: "new-token",
        user: {
          userId: 20,
          fullName: "Operator User",
          email: "operator@example.com",
          role: "operator",
        },
      });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user.role).toBe("OPERATOR");
    expect(sessionStorage.getItem("dq_access_token")).toBe("new-token");
  });

  it("logs out and clears session storage", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.saveAuth({
        accessToken: "token",
        user: { userId: 1, role: "ADMIN" },
      });
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(sessionStorage.getItem("dq_access_token")).toBeNull();
    expect(sessionStorage.getItem("dq_user")).toBeNull();
  });

  it("normalizes different backend user field formats", () => {
    const user = normalizeUser({
      user_id: 5,
      full_name: "Sample User",
      email: "sample@example.com",
      role: "analyst",
    });

    expect(user).toEqual({
      userId: 5,
      fullName: "Sample User",
      email: "sample@example.com",
      role: "ANALYST",
    });
  });
});
