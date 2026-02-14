import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export const ProtectedRoute: React.FC = () => {
    const { isAuthenticated, logout } = useAuthStore();
    const token = localStorage.getItem("auth_token");

    if (!isAuthenticated || !token) {
        // If state says authenticated but token is gone, force sync
        if (isAuthenticated) {
            logout();
        }
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
};

export const PublicRoute: React.FC = () => {
    const { isAuthenticated } = useAuthStore();
    const token = localStorage.getItem("auth_token");

    // Only redirect to dashboard if both state and token are present
    if (isAuthenticated && token) {
        return <Navigate to="/dashboard" replace />;
    }

    return <Outlet />;
};
