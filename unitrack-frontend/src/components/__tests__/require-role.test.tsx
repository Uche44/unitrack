import { describe, it, expect, afterEach } from "vitest";
import { screen } from "@testing-library/react";
import RequireRole from "../require-role";
import { renderWithRouter, setAuth, resetAuth } from "../../test/utils";

const Child = () => <div>protected content</div>;

describe("RequireRole guard", () => {
  afterEach(() => {
    resetAuth();
  });

  it("redirects unauthenticated users to login", () => {
    setAuth(null);
    renderWithRouter(
      <RequireRole role="admin">
        <Child />
      </RequireRole>,
    );
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
  });

  it("renders children for a matching role", () => {
    setAuth({ id: 1, fullname: "Ada", email: "ada@example.com", role: "admin" });
    renderWithRouter(
      <RequireRole role="admin">
        <Child />
      </RequireRole>,
    );
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });

  it("redirects a supervisor from an admin-only route", () => {
    setAuth({ id: 2, fullname: "Bob", email: "bob@example.com", role: "supervisor" });
    renderWithRouter(
      <RequireRole role="admin">
        <Child />
      </RequireRole>,
    );
    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
  });

  it("renders for a guest whose guest role matches", () => {
    setAuth(
      { id: 3, fullname: "Guest", email: "g@example.com", role: "student" },
      { is_guest: true, guest_role: "student" },
    );
    renderWithRouter(
      <RequireRole role="student">
        <Child />
      </RequireRole>,
    );
    expect(screen.getByText("protected content")).toBeInTheDocument();
  });
});