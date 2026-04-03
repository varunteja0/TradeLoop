import axios from "axios";
import { useAuth } from "../store/auth";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("tradeloop_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isHandling401 = false;

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !isHandling401 &&
      !error.config?.url?.includes("/auth/me") &&
      !error.config?.url?.includes("/auth/login") &&
      !error.config?.url?.includes("/auth/register")
    ) {
      isHandling401 = true;
      useAuth.getState().logout();
      setTimeout(() => { isHandling401 = false; }, 1000);
    }
    return Promise.reject(error);
  }
);

export default api;
