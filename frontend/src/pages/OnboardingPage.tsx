import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import { useOrgStore } from "../store/orgStore";
import { useAuthStore } from "../store/authStore";
import { Loader2, Building2, Users, LogOut } from "lucide-react";

export default function OnboardingPage() {
    const [name, setName] = useState("");
    const [slug, setSlug] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();
    const fetchOrgs = useOrgStore((state) => state.fetchOrgs);
    const logout = useAuthStore((state) => state.logout);
    const user = useAuthStore((state) => state.user);

    const handleCreateOrg = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await apiClient.post("/organizations/", { name, slug });
            await fetchOrgs();
            navigate("/dashboard");
        } catch (error: any) {
            setError(error.response?.data?.detail || "Failed to create organization");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
            <div className="w-full max-w-lg">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <Building2 className="w-8 h-8 text-primary" />
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900">Welcome{user?.full_name ? `, ${user.full_name}` : ""}!</h1>
                    <p className="text-slate-500 mt-2">
                        You need an organization to get started. Create one or wait for an invitation from your team.
                    </p>
                </div>

                {/* Create Org Card */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 mb-4">
                    <div className="flex items-center space-x-3 mb-6">
                        <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-emerald-600" />
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900">Create an Organization</h3>
                            <p className="text-sm text-slate-500">Start a new workspace for your team.</p>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-md">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleCreateOrg} className="space-y-4">
                        <div>
                            <label className="text-sm font-semibold text-slate-700 block mb-1.5">Organization Name</label>
                            <input
                                className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white"
                                placeholder="Acme Corp"
                                value={name}
                                onChange={(e) => {
                                    setName(e.target.value);
                                    setSlug(e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''));
                                }}
                                required
                            />
                        </div>
                        <div>
                            <label className="text-sm font-semibold text-slate-700 block mb-1.5">Organization Slug</label>
                            <input
                                className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white font-mono text-sm"
                                placeholder="acme-corp"
                                value={slug}
                                onChange={(e) => setSlug(e.target.value)}
                                required
                            />
                            <p className="text-[11px] text-slate-400 mt-1">Used in URLs. Lowercase letters, numbers, and hyphens only.</p>
                        </div>
                        <button
                            type="submit"
                            className="w-full bg-primary text-white font-bold py-3 rounded-lg hover:bg-primary/90 transition shadow-md disabled:opacity-50 flex items-center justify-center"
                            disabled={loading}
                        >
                            {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                            {loading ? "Creating..." : "Create Organization"}
                        </button>
                    </form>
                </div>

                {/* Join Org Card */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                            <Users className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900">Join an Existing Organization</h3>
                            <p className="text-sm text-slate-500">
                                Ask your team admin to invite you by email. Once invited, refresh this page.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Sign out link */}
                <div className="text-center">
                    <button
                        onClick={handleLogout}
                        className="text-sm text-slate-400 hover:text-slate-600 transition inline-flex items-center"
                    >
                        <LogOut className="w-3.5 h-3.5 mr-1.5" />
                        Sign out
                    </button>
                </div>
            </div>
        </div>
    );
}
