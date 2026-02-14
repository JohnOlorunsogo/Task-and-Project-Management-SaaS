import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Folder, Users, Clock, ArrowRight } from "lucide-react";
import { apiClient } from "@/api/client";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useOrgStore } from "@/store/orgStore";
import CreateProjectModal from "@/components/CreateProjectModal";

const DashboardPage: React.FC = () => {
    const currentOrgId = useOrgStore((state) => state.currentOrgId);
    const [isCreateOpen, setIsCreateOpen] = React.useState(false);

    const { data: projects, isLoading } = useQuery({
        queryKey: ["projects", currentOrgId],
        queryFn: async () => {
            const response = await apiClient.get("/projects");
            return response.data;
        },
        enabled: !!currentOrgId,
    });

    const stats = [
        { label: "Active Projects", value: projects?.length || 0, icon: Folder, color: "text-blue-600", bg: "bg-blue-50" },
        { label: "Team Members", value: "—", icon: Users, color: "text-purple-600", bg: "bg-purple-50" },
        { label: "Hours Tracked", value: "—", icon: Clock, color: "text-orange-600", bg: "bg-orange-50" },
    ];

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Organization Overview</h1>
                    <p className="text-slate-500">Welcome back! Here is what is happening in your organization.</p>
                </div>
                <button
                    onClick={() => setIsCreateOpen(true)}
                    className="bg-primary text-white px-4 py-2 rounded-md font-medium flex items-center shadow-sm hover:bg-primary/90 transition"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    New Project
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center">
                        <div className={cn("p-3 rounded-lg mr-4", stat.bg)}>
                            <stat.icon className={cn("w-6 h-6", stat.color)} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                            <p className="text-2xl font-bold">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Projects Section */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                    <h3 className="font-semibold">Recent Projects</h3>
                    <Link to="/projects" className="text-sm font-medium text-primary hover:underline">View all</Link>
                </div>

                <div className="divide-y divide-slate-100">
                    {isLoading ? (
                        <div className="px-6 py-12 text-center text-slate-500">Loading projects...</div>
                    ) : projects?.length === 0 ? (
                        <div className="px-6 py-12 text-center">
                            <Folder className="w-12 h-12 text-slate-200 mx-auto mb-3" />
                            <p className="text-slate-500">No projects yet. Create your first one to get started!</p>
                        </div>
                    ) : (
                        projects?.slice(0, 5).map((project: any) => (
                            <div key={project.id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                                <div className="flex items-center space-x-4">
                                    <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center font-bold text-slate-600">
                                        {project.name.charAt(0)}
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-slate-900">{project.name}</h4>
                                        <p className="text-sm text-slate-500 truncate max-w-md">{project.description || "No description"}</p>
                                    </div>
                                </div>
                                <Link
                                    to={`/projects/${project.id}`}
                                    className="p-2 text-slate-400 hover:text-primary transition-colors"
                                >
                                    <ArrowRight className="w-5 h-5" />
                                </Link>
                            </div>
                        ))
                    )}
                </div>
            </div>

            <CreateProjectModal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
            />
        </div>
    );
};

export default DashboardPage;
