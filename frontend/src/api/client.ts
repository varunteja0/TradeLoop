import axios from "axios";
import { useAuth } from "../store/auth";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

let isRedirecting = false;

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("tradeloop_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (import.meta.env.DEV) {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data ?? "");
  }

  return config;
});

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error(`[API] ${error.response?.status ?? "ERR"} ${error.config?.url}`, error.response?.data ?? error.message);
    }

    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true;
      useAuth.getState().logout();
      window.location.href = "/login";
      setTimeout(() => { isRedirecting = false; }, 2000);
    }

    return Promise.reject(error);
  }
);

export default api;
