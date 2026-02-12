import axios from "axios";
import API_BASE from "./config";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Store API ───

export const getStores = () => api.get("/stores");

export const getStore = (id) => api.get(`/stores/${id}`);

export const createStore = (data) => api.post("/stores", data);

export const deleteStore = (id) => api.delete(`/stores/${id}`);

export const getStorePods = (id) => api.get(`/stores/${id}/pods`);

export const healthCheck = () => api.get("/health");

export default api;
