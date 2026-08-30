import { create } from "zustand";
import api from "../lib/api";

export interface SessionData {
  session: string;
  duration: string;
  start_date: string;
  end_date: string;
}

interface SessionStore {
  currentSession: SessionData | null;
  setSession: (session: SessionData) => void;
  clearSession: () => void;
  fetchSession: () => Promise<void>;
}

export const useSessionStore = create<SessionStore>((set) => {
  const fetchSession = async () => {
    try {
      const res = await api.get("/api/projects/session/");

      if (res.status === 200) {
        const data = res.data;
        let sessionObj: unknown = null;

        if (Array.isArray(data)) {
          sessionObj = data.length ? data[0] : null;
        } else if (data && typeof data === "object") {
          sessionObj = data;
        }

        if (sessionObj && typeof sessionObj === "object") {
          const obj = sessionObj as {
            session?: string;
            duration?: string;
            start_date?: string;
            end_date?: string;
          };

          if (obj.session || obj.session === "") {
            set({
              currentSession: {
                session: obj.session || "",
                duration: obj.duration ?? "",
                start_date: obj.start_date ?? "",
                end_date: obj.end_date ?? "",
              },
            });
          }
        }
      }
    } catch (error) {
      console.log(error);
    }
  };

  const store = {
    currentSession: null,
    setSession: (session: SessionData) => set({ currentSession: session }),
    clearSession: () => set({ currentSession: null }),
    fetchSession,
  };

  void fetchSession();
  // Do not auto-fetch session on module import — call `fetchSession` from
  // components that need it to avoid triggering auth/refresh loops during
  // redirects or on the login page.

  return store;
});
