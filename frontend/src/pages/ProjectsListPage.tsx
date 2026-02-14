import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
    Plus,
    Folder,
    Search,
    Calendar,
    Trash2,
    MoreHorizontal,
    ArrowRight,
} from "lucide-react";
import { apiClient } from "@/api/client";
import { useOrgStore } from "@/store/orgStore";
import CreateProjectModal from "@/components/CreateProjectModal";

interface Project {
    id: string;
    name: string;
    description: string | null;
    owner_id: string;
    start_date: string | null;
    end_date: string | null;
    is_template: boolean;
    created_at: string;
}

const ProjectsListPage: React.FC = () => {
    const currentOrgId = useOrgStore((state) => state.currentOrgId);
    const queryClient = useQueryClient();
    const [isCreateOpen, setIsCreateOpen] = React.useState(false);
    const [searchQuery, setSearchQuery] = React.useState("");
    const [menuOpenId, setMenuOpenId] = React.useState<string | null>(null);
    const [deletingId, setDeletingId] = React.useState<string | null>(null);

    const { data: projects, isLoading } = useQuery<Project[]>({
        queryKey: ["projects", currentOrgId],
        queryFn: async () => {
            const response = await apiClient.get("/projects");
            return response.data;
        },
        enabled: !!currentOrgId,
    });

    const deleteMutation = useMutation({
        mutationFn: async (projectId: string) => {
            await apiClient.delete(`/projects/${projectId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            setDeletingId(null);
        },
    });

    const filtered = React.useMemo(() => {
        if (!projects) return [];
        if (!searchQuery.trim()) return projects;
        const q = searchQuery.toLowerCase();
        return projects.filter(
            (p) =>
                p.name.toLowerCase().includes(q) ||
                (p.description || "").toLowerCase().includes(q)
        );
    }, [projects, searchQuery]);

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return null;
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    // Random pastel color from project name
    const getProjectColor = (name: string) => {
        const colors = [
            "bg-blue-500", "bg-purple-500", "bg-emerald-500", "bg-orange-500",
            "bg-pink-500", "bg-cyan-500", "bg-indigo-500", "bg-amber-500",
        ];
        let hash = 0;
        for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
        return colors[Math.abs(hash) % colors.length];
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
                    <p className="text-slate-500 text-sm mt-1">
                        {projects?.length || 0} project{projects?.length !== 1 ? "s" : ""} in your organization
                    </p>
                </div>
                <button
                    onClick={() => setIsCreateOpen(true)}
                    className="bg-primary text-white px-4 py-2.5 rounded-lg font-medium flex items-center shadow-sm hover:bg-primary/90 transition active:scale-[0.98]"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Project
                </button>
            </div>

            {/* Search Bar */}
            <div className="relative max-w-md">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search projects..."
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                />
            </div>

            {/* Content */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 animate-pulse">
                            <div className="flex items-center space-x-3 mb-4">
                                <div className="w-10 h-10 bg-slate-200 rounded-lg" />
                                <div className="flex-1">
                                    <div className="h-4 bg-slate-200 rounded w-2/3 mb-2" />
                                    <div className="h-3 bg-slate-100 rounded w-1/3" />
                                </div>
                            </div>
                            <div className="h-3 bg-slate-100 rounded w-full mb-2" />
                            <div className="h-3 bg-slate-100 rounded w-4/5" />
                        </div>
                    ))}
                </div>
            ) : filtered.length === 0 ? (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-16 text-center">
                    <Folder className="w-16 h-16 text-slate-200 mx-auto mb-4" />
                    {searchQuery ? (
                        <>
                            <h3 className="text-lg font-semibold text-slate-700 mb-1">No matching projects</h3>
                            <p className="text-slate-500 text-sm">Try a different search term.</p>
                        </>
                    ) : (
                        <>
                            <h3 className="text-lg font-semibold text-slate-700 mb-1">No projects yet</h3>
                            <p className="text-slate-500 text-sm mb-6">Create your first project to start organizing tasks.</p>
                            <button
                                onClick={() => setIsCreateOpen(true)}
                                className="bg-primary text-white px-5 py-2.5 rounded-lg font-medium inline-flex items-center shadow-sm hover:bg-primary/90 transition"
                            >
                                <Plus className="w-4 h-4 mr-2" />
                                Create Project
                            </button>
                        </>
                    )}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filtered.map((project) => (
                        <div
                            key={project.id}
                            className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300 transition-all group relative"
                        >
                            {/* Color stripe */}
                            <div className={`h-1.5 rounded-t-xl ${getProjectColor(project.name)}`} />

                            <div className="p-5">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center space-x-3 min-w-0">
                                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0 ${getProjectColor(project.name)}`}>
                                            {project.name.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="min-w-0">
                                            <Link
                                                to={`/projects/${project.id}`}
                                                className="text-sm font-bold text-slate-900 hover:text-primary transition truncate block"
                                            >
                                                {project.name}
                                            </Link>
                                            <p className="text-xs text-slate-400">
                                                Created {formatDate(project.created_at)}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Menu */}
                                    <div className="relative">
                                        <button
                                            onClick={() => setMenuOpenId(menuOpenId === project.id ? null : project.id)}
                                            className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition opacity-0 group-hover:opacity-100"
                                        >
                                            <MoreHorizontal className="w-4 h-4" />
                                        </button>
                                        {menuOpenId === project.id && (
                                            <div className="absolute right-0 top-8 bg-white rounded-lg border border-slate-200 shadow-lg py-1 z-10 w-36">
                                                <button
                                                    onClick={() => {
                                                        setDeletingId(project.id);
                                                        setMenuOpenId(null);
                                                    }}
                                                    className="flex items-center w-full px-3 py-2 text-sm text-destructive hover:bg-destructive/5 transition"
                                                >
                                                    <Trash2 className="w-4 h-4 mr-2" />
                                                    Delete
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <p className="text-sm text-slate-500 line-clamp-2 mb-4 min-h-[2.5rem]">
                                    {project.description || "No description"}
                                </p>

                                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                                    {project.start_date || project.end_date ? (
                                        <div className="flex items-center text-xs text-slate-400">
                                            <Calendar className="w-3.5 h-3.5 mr-1" />
                                            {formatDate(project.start_date) || "—"}
                                            {" → "}
                                            {formatDate(project.end_date) || "—"}
                                        </div>
                                    ) : (
                                        <span className="text-xs text-slate-300">No dates set</span>
                                    )}

                                    <Link
                                        to={`/projects/${project.id}`}
                                        className="text-primary text-xs font-medium flex items-center hover:underline"
                                    >
                                        Open
                                        <ArrowRight className="w-3 h-3 ml-1" />
                                    </Link>
                                </div>
                            </div>

                            {/* Delete confirmation overlay */}
                            {deletingId === project.id && (
                                <div className="absolute inset-0 bg-white/95 backdrop-blur-sm rounded-xl flex items-center justify-center p-4 z-10">
                                    <div className="text-center">
                                        <p className="text-sm font-semibold text-slate-900 mb-1">Delete this project?</p>
                                        <p className="text-xs text-slate-500 mb-4">This action cannot be undone.</p>
                                        <div className="flex space-x-2 justify-center">
                                            <button
                                                onClick={() => setDeletingId(null)}
                                                className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-md transition"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={() => deleteMutation.mutate(project.id)}
                                                disabled={deleteMutation.isPending}
                                                className="px-3 py-1.5 text-xs font-bold bg-destructive text-white rounded-md hover:bg-destructive/90 transition disabled:opacity-50"
                                            >
                                                {deleteMutation.isPending ? "Deleting..." : "Delete"}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <CreateProjectModal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
            />
        </div>
    );
};

export default ProjectsListPage;
