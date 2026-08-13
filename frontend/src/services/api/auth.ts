import { apiClient } from "./client";
import { TokenData, User } from "../../types";

export interface LoginResponse extends TokenData {}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>("/auth/login", {
      username,
      password,
    });
    return response.data;
  },

  register: async (
    username: string,
    email: string,
    password: string,
    role: string = "Technician"
  ): Promise<User> => {
    const response = await apiClient.post<User>("/auth/register", {
      username,
      email,
      password,
      role,
    });
    return response.data;
  },
};

// Helper function to decode JWT token in frontend
export function decodeToken(token: string): User | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const decoded = JSON.parse(jsonPayload);
    return {
      id: decoded.user_id,
      username: decoded.sub,
      email: decoded.email || `${decoded.sub}@enterprise.com`,
      role: decoded.role || "Technician",
      isActive: true,
    };
  } catch (error) {
    console.error("Failed to decode token", error);
    return null;
  }
}
