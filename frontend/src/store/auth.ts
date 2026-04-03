import { create } from "zustand";
import api from "../api/client";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  hydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  hydrate: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateProfile: (data: { name?: string; timezone_offset?: number }) => Promise<void>;
  changePassword: (current_password: string, new_password: string) => Promise<void>;
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,
  hydrated: false,

  hydrate: async () => {
    const token = localStorage.getItem("tradeloop_token");
    const userStr = localStorage.getItem("tradeloop_user");
    if (!token || !userStr) {
      set({ hydrated: true });
      return;
    }

    try {
      const user = JSON.parse(userStr);
      set({ token, user, hydrated: true });
      const { data } = await api.get("/auth/me");
      set({ user: data });
      localStorage.setItem("tradeloop_user", JSON.stringify(data));
    } catch {
      localStorage.removeItem("tradeloop_token");
      localStorage.removeItem("tradeloop_refresh_token");
      localStorage.removeItem("tradeloop_user");
      set({ user: null, token: null, hydrated: true });
    }
  },

  login: async (email, password) => {
    set({ loading: true });
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("tradeloop_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("tradeloop_refresh_token", data.refresh_token);
      }
      localStorage.setItem("tradeloop_user", JSON.stringify(data.user));
      set({ user: data.user, token: data.access_token, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  register: async (email, password, name) => {
    set({ loading: true });
    try {
      const { data } = await api.post("/auth/register", { email, password, name });
      localStorage.setItem("tradeloop_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("tradeloop_refresh_token", data.refresh_token);
      }
      localStorage.setItem("tradeloop_user", JSON.stringify(data.user));
      set({ user: data.user, token: data.access_token, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  logout: () => {
    localStorage.removeItem("tradeloop_token");
    localStorage.removeItem("tradeloop_refresh_token");
    localStorage.removeItem("tradeloop_user");
    set({ user: null, token: null });
  },

  refreshToken: async () => {
    const refresh = localStorage.getItem("tradeloop_refresh_token");
    if (!refresh) {
      get().logout();
      return;
    }
    try {
      const { data } = await api.post("/auth/refresh", { refresh_token: refresh });
      localStorage.setItem("tradeloop_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("tradeloop_refresh_token", data.refresh_token);
      }
      set({ token: data.access_token });
    } catch {
      get().logout();
    }
  },

  updateProfile: async (profileData) => {
    const { data } = await api.put("/auth/profile", profileData);
    set({ user: data });
    localStorage.setItem("tradeloop_user", JSON.stringify(data));
  },

  changePassword: async (current_password, new_password) => {
    await api.post("/auth/change-password", { current_password, new_password });
  },
}));
