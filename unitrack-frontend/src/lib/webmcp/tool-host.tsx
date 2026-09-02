/**
 * Role-scoped WebMCP tool host.
 *
 * Registration happens only when the locally persisted user and the
 * server-side authenticated identity (`GET /api/auth/me/`) agree on the
 * permitted role. A route parameter is never used as authorization. When the
 * host unmounts (logout, role change, navigation) the hook unregisters its
 * tools automatically via `use-webmcp-tool`.
 */

import React, { useEffect, useState } from "react";
import api from "../api";
import { useUserStore } from "../../context/user-context";
import type { UserRole } from "../../types/user";
import { useUniTrackTool } from "./use-uni-track-tool";
import type { UniTrackToolDefinition } from "./types";

interface SingleToolHostProps {
  definition: UniTrackToolDefinition;
  run: (args: never) => Promise<{
    data: unknown;
    summary: string;
    scope?: Record<string, unknown>;
    warnings?: string[];
    counts?: Record<string, number>;
  }>;
  enabled: boolean;
}

const SingleToolHost: React.FC<SingleToolHostProps> = ({
  definition,
  run,
  enabled,
}) => {
  const { supported, registered, error, definitionValid } = useUniTrackTool({
    definition,
    run,
    enabled,
  });

  // Development-only status surface: tool name and booleans, never user data.
  if (!import.meta.env.DEV) return null;

  return (
    <div
      data-testid={`webmcp-status-${definition.name}`}
      data-supported={String(supported)}
      data-registered={String(registered)}
      data-definition-valid={String(definitionValid)}
      data-error={error ? String((error as Error).message) : ""}
      hidden
    />
  );
};

export interface ToolHostProps {
  /** The only role permitted to register the hosted tools. */
  role: UserRole;
  /** Business tools; empty until Milestones 4-9 add them. */
  tools?: UniTrackToolDefinition[];
  runners?: Record<string, (args: never) => Promise<{
    data: unknown;
    summary: string;
    scope?: Record<string, unknown>;
    warnings?: string[];
    counts?: Record<string, number>;
  }>>;
}

export const ToolHost: React.FC<ToolHostProps> = ({ role, tools = [], runners = {} }) => {
  const user = useUserStore((state) => state.user);
  const [roleAgreed, setRoleAgreed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    if (!user) {
      queueMicrotask(() => {
        if (!cancelled) setRoleAgreed(false);
      });
      return () => {
        cancelled = true;
      };
    }

    api
      .get("/api/auth/me/")
      .then((response) => {
        if (cancelled) return;
        const me = response.data as { id?: number; role?: string };
        setRoleAgreed(Boolean(me && me.role === role && me.id === user.id));
      })
      .catch(() => {
        // Expired authentication or any failure: keep registration off.
        if (!cancelled) setRoleAgreed(false);
      });

    return () => {
      cancelled = true;
    };
  }, [role, user?.id, user?.role, user]);

  return (
    <>
      {tools.map((definition) => (
        <SingleToolHost
          key={definition.name}
          definition={definition}
          run={runners[definition.name]}
          enabled={roleAgreed}
        />
      ))}
    </>
  );
};

export default ToolHost;