import React from "react";
import { Outlet } from "react-router-dom";

const AuthLayout: React.FC = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
            <div className="w-full max-w-md bg-white rounded-xl shadow-lg border border-slate-200 p-8">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                        <span className="text-white font-bold text-2xl">TP</span>
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900">TaskPM Enterprise</h1>
                    <p className="text-slate-500">Manage your projects with ease</p>
                </div>
                <Outlet />
            </div>
        </div>
    );
};

export default AuthLayout;
