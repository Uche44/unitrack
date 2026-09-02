import { describe, it, expect, afterEach, beforeEach, vi } from "vitest";
import MockAdapter from "axios-mock-adapter";
import axios from "axios";
import api from "../api";

// baseURL is set via test.env VITE_API_URL in vite.config.ts
const BASE = "http://test.local";
const refreshUrl = `${BASE}/api/refresh/`;

describe("api client", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    localStorage.clear();
    mock = new MockAdapter(api);
  });

  afterEach(() => {
    mock.restore();
    vi.restoreAllMocks();
  });

  it("sends requests with credentials enabled", () => {
    expect(
      (api.defaults as { withCredentials?: boolean }).withCredentials,
    ).toBe(true);
  });

  it("attaches the bearer token from localStorage", async () => {
    localStorage.setItem("access_token", "tok-123");
    let seenAuth: string | undefined;
    mock.onGet("/api/projects/").reply((config) => {
      seenAuth = (config.headers as Record<string, unknown> | undefined)
        ?.Authorization as string | undefined;
      return [200, []];
    });

    await api.get("/api/projects/");
    expect(seenAuth).toBe("Bearer tok-123");
  });

  it("does not attach Authorization when no token is stored", async () => {
    let seenAuth: unknown = "sentinel";
    mock.onGet("/api/health/").reply((config) => {
      seenAuth = (config.headers as Record<string, unknown> | undefined)
        ?.Authorization;
      return [200, {}];
    });

    await api.get("/api/health/");
    expect(seenAuth).toBeUndefined();
  });

  it("refreshes once and retries the original request on 401", async () => {
    localStorage.setItem("access_token", "old-tok");
    localStorage.setItem("refresh_token", "refresh-val");

    const axiosPost = vi
      .spyOn(axios, "post")
      .mockResolvedValue({ data: { access: "new-tok" } } as never);

    let retriedAuth: string | undefined;
    mock
      .onGet("/api/session/")
      .replyOnce(401)
      .onGet("/api/session/")
      .reply((config) => {
        retriedAuth = (config.headers as Record<string, unknown> | undefined)
          ?.Authorization as string | undefined;
        return [200, { ok: true }];
      });

    const res = await api.get("/api/session/");

    expect(axiosPost).toHaveBeenCalledTimes(1);
    expect(axiosPost.mock.calls[0][0]).toBe(refreshUrl);
    expect(localStorage.getItem("access_token")).toBe("new-tok");
    expect(retriedAuth).toBe("Bearer new-tok");
    expect(res.data).toEqual({ ok: true });
  });

  it("retries a failing request exactly once (single refresh)", async () => {
    localStorage.setItem("access_token", "old-tok");
    localStorage.setItem("refresh_token", "refresh-val");
    const axiosPost = vi
      .spyOn(axios, "post")
      .mockResolvedValue({ data: { access: "new-tok" } } as never);

    let calls = 0;
    mock.onGet("/api/session/").reply(() => {
      calls += 1;
      return calls === 1 ? [401, {}] : [200, { ok: true }];
    });

    const res = await api.get("/api/session/");
    expect(res.data).toEqual({ ok: true });
    expect(axiosPost).toHaveBeenCalledTimes(1);
    expect(calls).toBe(2);
  });

  it("does not refresh for the refresh endpoint itself to avoid a loop", async () => {
    let refreshCalls = 0;
    mock.onPost(refreshUrl).reply(() => {
      refreshCalls += 1;
      return [401, { detail: "bad" }];
    });

    await expect(api.post(refreshUrl, { refresh: "x" })).rejects.toBeTruthy();
    expect(refreshCalls).toBe(1);
  });

  it("clears stored tokens when the refresh attempt fails", async () => {
    localStorage.setItem("access_token", "old-tok");
    localStorage.setItem("refresh_token", "refresh-val");
    vi.spyOn(axios, "post").mockRejectedValue(new Error("refresh failed") as never);
    mock.onGet("/api/session/").replyOnce(401);

    await expect(api.get("/api/session/")).rejects.toBeTruthy();
    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });
});