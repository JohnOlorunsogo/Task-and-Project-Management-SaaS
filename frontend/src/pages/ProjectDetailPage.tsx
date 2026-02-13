import React from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
    List,
    Trello,
    Calendar,
    GanttChart,
    Settings,
    Plus,
    Filter,
    Search,
} from "lucide-react";
import { apiClient } from "@/api/client";
import { cn } from "@/lib/utils";
import TaskListView from "./TaskListView.tsx";
import TaskBoardView from "./TaskBoardView.tsx";
import CreateTaskModal from "@/components/CreateTaskModal";

const ProjectDetailPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const [searchParams, setSearchParams] = useSearchParams();
    const [isTaskModalOpen, setIsTaskModalOpen] = React.useState(false);
    const currentView = searchParams.get("view") || "list";

    const { data: project, isLoading } = useQuery({
        queryKey: ["project", projectId],
        queryFn: async () => {
            const response = await apiClient.get(`/projects/${projectId}`);
            return response.data;
        },
    });

    const views = [
        { id: "list", label: "List", icon: List },
        { id: "board", label: "Board", icon: Trello },
        { id: "timeline", label: "Timeline", icon: GanttChart },
        { id: "calendar", label: "Calendar", icon: Calendar },
    ];

    if (isLoading) return <div className="p-8 text-center text-slate-500">Loading project...</div>;
    if (!project) return <div className="p-8 text-center text-destructive">Project not found</div>;

    return (
        <div className="h-full flex flex-col -m-6">
            {/* Project Header */}
            <div className="bg-white border-b border-slate-200 px-6 py-4 shrink-0">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center text-white font-bold">
                            {project.name.charAt(0)}
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
                            <p className="text-xs text-slate-500">Project · {project.status || "Active"}</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <div className="flex -space-x-1.5 mr-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="w-7 h-7 rounded-full border-2 border-white bg-slate-200 flex items-center justify-center text-[8px] font-bold">
                                    U{i}
                                </div>
                            ))}
                            <button className="w-7 h-7 rounded-full border-2 border-white bg-slate-100 flex items-center justify-center text-slate-400 hover:bg-slate-200 transition cursor-pointer">
                                <Plus className="w-3 h-3" />
                            </button>
                        </div>
                        <button className="p-2 hover:bg-slate-50 rounded-md text-slate-400">
                            <Settings className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* View Switcher Tabs */}
                <div className="flex items-center justify-between">
                    <div className="flex space-x-1">
                        {views.map((view) => (
                            <button
                                key={view.id}
                                onClick={() => setSearchParams({ view: view.id })}
                                className={cn(
                                    "flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors relative",
                                    currentView === view.id
                                        ? "text-primary bg-primary/5"
                                        : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                                )}
                            >
                                <view.icon className="w-4 h-4 mr-2" />
                                {view.label}
                                {currentView === view.id && (
                                    <div className="absolute bottom-[-17px] left-0 right-0 h-0.5 bg-primary" />
                                )}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center space-x-2">
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                            <input
                                placeholder="Search tasks..."
                                className="pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-sm outline-none focus:ring-1 focus:ring-primary/20 w-48 transition-all focus:w-64"
                            />
                        </div>
                        <button className="flex items-center px-3 py-1.5 border border-slate-200 rounded-md text-sm text-slate-600 hover:bg-slate-50">
                            <Filter className="w-4 h-4 mr-2" />
                            Filter
                        </button>
                        <button
                            onClick={() => setIsTaskModalOpen(true)}
                            className="bg-primary text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-primary/90 transition shadow-sm"
                        >
                            Add Task
                        </button>
                    </div>
                </div>
            </div>

            {/* View Content */}
            <div className="flex-1 overflow-hidden">
                {currentView === "list" && <TaskListView projectId={projectId!} />}
                {currentView === "board" && <TaskBoardView projectId={projectId!} />}
                {currentView === "timeline" && <div className="p-8 text-center text-slate-400">Timeline View Coming Soon</div>}
                {currentView === "calendar" && <div className="p-8 text-center text-slate-400">Calendar View Coming Soon</div>}
            </div>

            <CreateTaskModal
                projectId={projectId!}
                isOpen={isTaskModalOpen}
                onClose={() => setIsTaskModalOpen(false)}
            />
        </div>
    );
};

export default ProjectDetailPage;
