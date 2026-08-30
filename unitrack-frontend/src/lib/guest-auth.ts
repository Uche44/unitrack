/* eslint-disable @typescript-eslint/no-unused-vars */
import api from "./api";

export interface GuestLoginResponse {
  message: string;
  user: {
    id: number;
    email: string;
    role: string;
    full_name: string;
    is_guest: boolean;
    is_approved: boolean;
  };
}

export const guestLogin = async (
  role: "student" | "supervisor" | "admin"
): Promise<GuestLoginResponse> => {
  try {
    const response = await api.post<GuestLoginResponse>("/api/guest-login/", {
      role,
    });
    return response.data;
  } catch (error) {
    throw new Error("Failed to login as guest");
  
  }
};
