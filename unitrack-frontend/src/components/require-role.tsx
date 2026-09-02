import React from "react";
import { Navigate } from "react-router-dom";
import { useUserStore } from "../context/user-context";
import type { UserRole } from "../types/user";

interface RequireRoleProps {
  role: UserRole;
  children: React.ReactNode;
}

/**
 * Guards a dashboard layout so it only renders for the expected role.
 * Unauthenticated users and users with the wrong role are redirected to login.
 * Guest demo users are allowed only when their selected guest role matches.
 */
const RequireRole: React.FC<RequireRoleProps> = ({ role, children }) => {
  const user = useUserStore((state) => state.user);
  const is_guest = useUserStore((state) => state.is_guest);
  const guest_role = useUserStore((state) => state.guest_role);

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  const activeRole = is_guest && guest_role ? guest_role : user.role;

  if (activeRole !== role) {
    return <Navigate to="/auth/login" replace />;
  }

  return <>{children}</>;
};

export default RequireRole;