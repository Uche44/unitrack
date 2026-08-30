import { create } from "zustand";
import type { User } from "../types/user";
import { persist } from "zustand/middleware";

interface UserState {
  user: User | null;
  is_guest: boolean;
  guest_role: string | null;
  setUser: (user: User) => void;
  setGuest: (is_guest: boolean, guest_role?: string | null) => void;
  clearUser: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      is_guest: false,
      guest_role: null,
      setUser: (user) => set({ user }),
      setGuest: (is_guest, guest_role = null) =>
        set({ is_guest, guest_role: guest_role || null }),
      clearUser: () => set({ user: null, is_guest: false, guest_role: null }),
    }),
    {
      name: "user-storage",
    }
  )
);
