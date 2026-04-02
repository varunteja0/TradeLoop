import { create } from "zustand";
import api from "../api/client";

interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  hydrate: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: null,
  loading: false,

  hydrate: () => {
    const token = localStorage.getItem("tradeloop_token");
    const userStr = localStorage.getItem("tradeloop_user");
    if (token && userStr) {
      try {
        set({ token, user: JSON.parse(userStr) });
      } catch {
        localStorage.removeItem("tradeloop_token");
        localStorage.removeItem("tradeloop_user");
      }
    }
  },

  login: async (email, password) => {
    set({ loading: true });
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("tradeloop_token", data.access_token);
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
      localStorage.setItem("tradeloop_user", JSON.stringify(data.user));
      set({ user: data.user, token: data.access_token, loading: false });
    } catch (e) {
      set({ loading: false });
      throw e;
    }
  },

  logout: () => {
    localStorage.removeItem("tradeloop_token");
    localStorage.removeItem("tradeloop_user");
    set({ user: null, token: null });
  },
}));
