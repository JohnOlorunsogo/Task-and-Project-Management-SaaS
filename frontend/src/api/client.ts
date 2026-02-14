import axios from "axios";
import { useAuthStore } from "../store/authStore";

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor for JWT and Org scoping
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("auth_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Add Organization Context
        const orgStorage = localStorage.getItem("org-storage");
        if (orgStorage) {
            try {
                const { state } = JSON.parse(orgStorage);
                if (state?.currentOrgId) {
                    config.headers["X-Org-Id"] = state.currentOrgId;
                }
            } catch (e) {
                console.error("Failed to parse org storage", e);
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for handle token expiry
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            useAuthStore.getState().logout();
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);
