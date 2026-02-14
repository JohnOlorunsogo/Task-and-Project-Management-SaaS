import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { useOrgStore } from "@/store/orgStore";
import { Loader2 } from "lucide-react";

const loginSchema = z.object({
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);
    const fetchOrgs = useOrgStore((state) => state.fetchOrgs);
    const [error, setError] = React.useState<string | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    });

    const onSubmit = async (data: LoginFormValues) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await apiClient.post("/auth/login", {
                email: data.email,
                password: data.password,
            });

            const { access_token, user } = response.data;
            setAuth(user, access_token);

            // Check if user has any organizations
            try {
                const orgs = await fetchOrgs();
                if (orgs && orgs.length > 0) {
                    navigate("/dashboard");
                    return;
                }
            } catch {
                // No orgs found
            }

            // No orgs → send to onboarding
            navigate("/onboarding");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Invalid email or password");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h2 className="text-2xl font-bold mb-2">Welcome back</h2>
            <p className="text-slate-500 mb-8">Sign in to your account.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {error && (
                    <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md border border-destructive/20">
                        {error}
                    </div>
                )}

                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                        Email Address
                    </label>
                    <input
                        {...register("email")}
                        type="email"
                        className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white"
                        placeholder="name@company.com"
                    />
                    {errors.email && (
                        <p className="text-destructive text-xs mt-1">{errors.email.message}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                        Password
                    </label>
                    <input
                        {...register("password")}
                        type="password"
                        className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white"
                        placeholder="••••••••"
                    />
                    {errors.password && (
                        <p className="text-destructive text-xs mt-1">{errors.password.message}</p>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-primary text-white py-3 rounded-lg font-bold hover:bg-primary/90 transition flex items-center justify-center shadow-lg active:scale-[0.98] disabled:opacity-50"
                >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Sign In
                </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600">
                Don't have an account?{" "}
                <Link to="/register" className="text-primary font-semibold hover:underline">
                    Sign Up
                </Link>
            </p>
        </div>
    );
};

export default LoginPage;
