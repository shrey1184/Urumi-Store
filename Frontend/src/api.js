import axios from "axios";
import API_BASE from "./config";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("auth_token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// ─── Auth API ───

export const getCurrentUser = () => api.get("/auth/me");

export const logout = () => {
  localStorage.removeItem("auth_token");
  window.location.href = "/";
};

// ─── Store API ───

export const getStores = () => api.get("/stores");

export const getStore = (id) => api.get(`/stores/${id}`);

export const createStore = (data) => api.post("/stores", data);

export const deleteStore = (id) => api.delete(`/stores/${id}`);

export const getStorePods = (id) => api.get(`/stores/${id}/pods`);

export const healthCheck = () => api.get("/health");

export default api;
