import React from "react";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useUserStore } from "../context/user-context";
import type { User } from "../types/user";

export const resetAuth = () => {
  useUserStore.setState({ user: null, is_guest: false, guest_role: null });
};

export const setAuth = (
  user: User | null,
  { is_guest = false, guest_role = null }: { is_guest?: boolean; guest_role?: string | null } = {},
) => {
  useUserStore.setState({ user, is_guest, guest_role: guest_role ?? null });
};

export const renderWithRouter = (ui: React.ReactElement, { route = "/" } = {}) => {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
};