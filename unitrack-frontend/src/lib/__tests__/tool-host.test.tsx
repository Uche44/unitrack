import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { MemoryRouter } from "react-router-dom";
import ToolHost from "../webmcp/tool-host";
import type { UniTrackToolDefinition } from "../webmcp/types";
import { setAuth } from "../../test/utils";

const mock = new MockAdapter(axios);

const definition: UniTrackToolDefinition = {
  name: "test_tool",
  description: "A test tool for host registration.",
  inputSchema: { type: "object", properties: {} },
};

const runner = async () => ({
  data: { ok: true },
  summary: "Test complete",
});

const renderHost = () =>
  render(
    <MemoryRouter>
      <ToolHost role="admin" tools={[definition]} runners={{ test_tool: runner }} />
    </MemoryRouter>,
  );

describe("ToolHost", () => {
  afterEach(() => {
    mock.reset();
    setAuth(null);
  });

  it("enables a tool only after the server confirms the same user and role", async () => {
    setAuth({ id: 7, fullname: "Admin User", email: "admin@example.com", role: "admin" });
    mock.onGet("/api/auth/me/").reply(200, { id: 7, role: "admin" });

    renderHost();

    const status = screen.getByTestId("webmcp-status-test_tool");
    expect(status).toHaveAttribute("data-supported", "true");
    expect(status).toHaveAttribute("data-definition-valid", "true");
    expect(status).toHaveAttribute("data-registered", "true");
  });

  it("keeps the tool disabled when the server identity does not match", async () => {
    setAuth({ id: 7, fullname: "Admin User", email: "admin@example.com", role: "admin" });
    mock.onGet("/api/auth/me/").reply(200, { id: 7, role: "student" });

    renderHost();

    await waitFor(() => {
      expect(screen.getByTestId("webmcp-status-test_tool")).toHaveAttribute(
        "data-registered",
        "false",
      );
    });
  });
});
