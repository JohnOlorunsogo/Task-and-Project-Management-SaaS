import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { useOrgStore } from "@/store/orgStore";
import {
    Users,
    Settings as SettingsIcon,
    UserPlus,
    Trash2,
    Mail,
    Loader2,
    Check
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<"general" | "members">("members");
    const { currentOrgId, orgs } = useOrgStore();
    const queryClient = useQueryClient();

    const currentOrg = orgs.find(o => o.id === currentOrgId);

    // Fetch members
    const { data: members, isLoading: membersLoading } = useQuery({
        queryKey: ["org-members", currentOrgId],
        queryFn: async () => {
            const res = await apiClient.get(`/organizations/${currentOrgId}/members`);
            return res.data;
        },
        enabled: !!currentOrgId,
    });

    // Invite member mutation
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("member");

    const inviteMutation = useMutation({
        mutationFn: async () => {
            return apiClient.post(`/organizations/${currentOrgId}/members`, {
                email: inviteEmail,
                role: inviteRole
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["org-members", currentOrgId] });
            setInviteEmail("");
            setInviteRole("member");
        }
    });

    // Remove member mutation
    const removeMutation = useMutation({
        mutationFn: async (userId: string) => {
            return apiClient.delete(`/organizations/${currentOrgId}/members/${userId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["org-members", currentOrgId] });
        }
    });

    // Change role mutation
    const roleMutation = useMutation({
        mutationFn: async ({ userId, role }: { userId: string, role: string }) => {
            return apiClient.put(`/organizations/${currentOrgId}/members/${userId}/role`, { role });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["org-members", currentOrgId] });
        }
    });

    if (!currentOrgId) {
        return <div className="p-8 text-center text-slate-500">No organization selected.</div>;
    }

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
                <p className="text-slate-500 mt-1">Manage your organization and team members.</p>
            </div>

            <div className="flex border-b border-slate-200">
                <button
                    onClick={() => setActiveTab("general")}
                    className={cn(
                        "px-6 py-3 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center space-x-2",
                        activeTab === "general" ? "border-primary text-primary" : "border-transparent text-slate-500 hover:text-slate-700"
                    )}
                >
                    <SettingsIcon className="w-4 h-4" />
                    <span>General</span>
                </button>
                <button
                    onClick={() => setActiveTab("members")}
                    className={cn(
                        "px-6 py-3 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center space-x-2",
                        activeTab === "members" ? "border-primary text-primary" : "border-transparent text-slate-500 hover:text-slate-700"
                    )}
                >
                    <Users className="w-4 h-4" />
                    <span>Members</span>
                </button>
            </div>

            {activeTab === "general" && (
                <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                    <h3 className="text-lg font-bold mb-6">Organization Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-1">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Organization Name</p>
                            <p className="text-slate-900 font-medium">{currentOrg?.name}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Slug</p>
                            <p className="text-slate-900 font-mono text-sm">{currentOrg?.slug}</p>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "members" && (
                <div className="space-y-6">
                    {/* Invite Section */}
                    <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-lg font-bold">Invite Members</h3>
                                <p className="text-sm text-slate-500">Add new people to your organization by email.</p>
                            </div>
                            <UserPlus className="w-8 h-8 text-primary/20" />
                        </div>

                        <form
                            onSubmit={(e) => { e.preventDefault(); inviteMutation.mutate(); }}
                            className="flex flex-col md:flex-row gap-4"
                        >
                            <div className="flex-1">
                                <div className="relative">
                                    <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type="email"
                                        placeholder="email@example.com"
                                        className="w-full pl-10 pr-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white text-sm"
                                        value={inviteEmail}
                                        onChange={(e) => setInviteEmail(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="w-full md:w-48">
                                <select
                                    className="w-full px-4 py-2.5 border rounded-lg border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition bg-white text-sm"
                                    value={inviteRole}
                                    onChange={(e) => setInviteRole(e.target.value)}
                                >
                                    <option value="member">Member</option>
                                    <option value="proj_admin">Project Admin</option>
                                    <option value="org_admin">Org Admin</option>
                                </select>
                            </div>
                            <button
                                type="submit"
                                disabled={inviteMutation.isPending || !inviteEmail}
                                className="bg-primary text-white px-8 py-2.5 rounded-lg font-bold hover:bg-primary/90 transition shadow-md disabled:opacity-50 flex items-center justify-center whitespace-nowrap min-w-[140px]"
                            >
                                {inviteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Invite"}
                            </button>
                        </form>
                        {inviteMutation.isSuccess && (
                            <p className="mt-3 text-sm text-emerald-600 flex items-center font-medium animate-in fade-in slide-in-from-top-1">
                                <Check className="w-4 h-4 mr-1.5" /> Invitation sent!
                            </p>
                        )}
                    </div>

                    {/* Members List */}
                    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                        <div className="px-8 py-4 bg-slate-50/50 border-b border-slate-200">
                            <h3 className="font-bold text-slate-800">Org Members ({members?.length || 0})</h3>
                        </div>

                        <div className="divide-y divide-slate-100">
                            {membersLoading ? (
                                <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-slate-400" /></div>
                            ) : members?.map((m: any) => (
                                <div key={m.user_id} className="px-8 py-5 flex items-center justify-between group hover:bg-slate-50/50 transition-colors">
                                    <div className="flex items-center space-x-4">
                                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600">
                                            {m.user_id.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-900">User ID: {m.user_id}</p>
                                            <div className="flex items-center mt-1">
                                                <span className={cn(
                                                    "text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider",
                                                    m.role === "org_admin" ? "bg-amber-100 text-amber-700" :
                                                        m.role === "proj_admin" ? "bg-blue-100 text-blue-700" :
                                                            "bg-slate-100 text-slate-600"
                                                )}>
                                                    {m.role.replace('_', ' ')}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <select
                                            value={m.role}
                                            onChange={(e) => roleMutation.mutate({ userId: m.user_id, role: e.target.value })}
                                            className="text-xs bg-white border border-slate-200 rounded px-2 py-1 outline-none focus:ring-2 focus:ring-primary/10"
                                        >
                                            <option value="member">Member</option>
                                            <option value="proj_admin">Admin</option>
                                            <option value="org_admin">Org Admin</option>
                                        </select>
                                        <button
                                            onClick={() => removeMutation.mutate(m.user_id)}
                                            className="p-1.5 text-slate-400 hover:text-destructive hover:bg-destructive/5 rounded-md transition-colors"
                                            title="Remove member"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
