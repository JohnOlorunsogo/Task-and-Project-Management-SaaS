import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { useOrgStore } from "@/store/orgStore";
import { Loader2 } from "lucide-react";

const registerSchema = z.object({
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    full_name: z.string().min(2, "Full name required"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);
    const fetchOrgs = useOrgStore((state) => state.fetchOrgs);
    const [error, setError] = React.useState<string | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
    });

    const onSubmit = async (data: RegisterFormValues) => {
        setIsLoading(true);
        setError(null);
        try {
            // 1. Register user (no org)
            await apiClient.post("/auth/register", {
                email: data.email,
                password: data.password,
                full_name: data.full_name,
            });

            // 2. Log them in immediately
            const loginResponse = await apiClient.post("/auth/login", {
                email: data.email,
                password: data.password,
            });

            const { access_token, user } = loginResponse.data;
            setAuth(user, access_token);

            // 3. Check if user already belongs to any org (e.g. was invited)
            try {
                const orgs = await fetchOrgs();
                if (orgs && orgs.length > 0) {
                    navigate("/dashboard");
                    return;
                }
            } catch {
                // No orgs, continue to onboarding
            }

            // 4. New user with no orgs → onboarding
            navigate("/onboarding");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Registration failed. Try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto">
            <h2 className="text-2xl font-bold mb-2">Create your account</h2>
            <p className="text-slate-500 mb-8">Sign up to start managing your projects.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {error && (
                    <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md border border-destructive/20">
                        {error}
                    </div>
                )}

                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                        Full Name
                    </label>
                    <input
                        {...register("full_name")}
                        className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white"
                        placeholder="John Doe"
                    />
                    {errors.full_name && (
                        <p className="text-destructive text-xs mt-1">{errors.full_name.message}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                        Work Email
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
                        placeholder="At least 8 characters"
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
                    Create Account
                </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600">
                Already have an account?{" "}
                <Link to="/login" className="text-primary font-semibold hover:underline">
                    Sign In
                </Link>
            </p>
        </div>
    );
};

export default RegisterPage;
