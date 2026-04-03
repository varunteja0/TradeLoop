import { describe, it, expect, beforeEach } from "vitest";
import { useAuth } from "../auth";

describe("Auth Store", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuth.setState({ user: null, token: null, loading: false });
  });

  it("starts with null user", () => {
    expect(useAuth.getState().user).toBeNull();
  });

  it("logout clears state and localStorage", () => {
    localStorage.setItem("tradeloop_token", "test");
    localStorage.setItem("tradeloop_user", '{"id":"1"}');
    useAuth.getState().logout();
    expect(useAuth.getState().user).toBeNull();
    expect(localStorage.getItem("tradeloop_token")).toBeNull();
  });
});
