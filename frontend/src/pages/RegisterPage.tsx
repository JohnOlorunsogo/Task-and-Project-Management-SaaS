import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { Loader2 } from "lucide-react";

const registerSchema = z.object({
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    full_name: z.string().min(2, "Full name required"),
    org_name: z.string().min(2, "Organization name required"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);
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
            // 1. Register user and create org
            await apiClient.post("/auth/register", data);

            // 2. Log them in immediately after success
            const loginResponse = await apiClient.post("/auth/login", {
                username: data.email,
                password: data.password,
            });

            const { access_token, user } = loginResponse.data;
            setAuth(user, access_token);
            navigate("/dashboard");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Registration failed. Try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h2 className="text-xl font-semibold mb-6">Create your Organization</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {error && (
                    <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md border border-destructive/20">
                        {error}
                    </div>
                )}

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Full Name
                    </label>
                    <input
                        {...register("full_name")}
                        className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
                        placeholder="John Doe"
                    />
                    {errors.full_name && (
                        <p className="text-destructive text-xs mt-1">{errors.full_name.message}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Work Email
                    </label>
                    <input
                        {...register("email")}
                        type="email"
                        className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
                        placeholder="name@company.com"
                    />
                    {errors.email && (
                        <p className="text-destructive text-xs mt-1">{errors.email.message}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Organization Name
                    </label>
                    <input
                        {...register("org_name")}
                        className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
                        placeholder="Acme Inc."
                    />
                    {errors.org_name && (
                        <p className="text-destructive text-xs mt-1">{errors.org_name.message}</p>
                    )}
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                        Password
                    </label>
                    <input
                        {...register("password")}
                        type="password"
                        className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition"
                        placeholder="Min 8 characters"
                    />
                    {errors.password && (
                        <p className="text-destructive text-xs mt-1">{errors.password.message}</p>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-primary text-white py-2 rounded-md font-medium hover:bg-primary/90 transition flex items-center justify-center"
                >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Get Started
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
