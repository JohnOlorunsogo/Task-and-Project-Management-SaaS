import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
    CheckCircle2,
    Circle,
    Clock,
    MessageSquare,
    Paperclip,
    MoreHorizontal,
    GripVertical
} from "lucide-react";
import { apiClient } from "@/api/client";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

interface TaskListViewProps {
    projectId: string;
}

const TaskListView: React.FC<TaskListViewProps> = ({ projectId }) => {
    const { data: tasks, isLoading } = useQuery({
        queryKey: ["tasks", projectId],
        queryFn: async () => {
            const response = await apiClient.get(`/tasks?project_id=${projectId}`);
            return response.data;
        },
    });

    const getPriorityColor = (priority: string) => {
        switch (priority.toLowerCase()) {
            case 'high': return 'text-red-500';
            case 'medium': return 'text-orange-500';
            case 'low': return 'text-blue-500';
            default: return 'text-slate-400';
        }
    };

    if (isLoading) return <div className="p-12 text-center text-slate-500 text-sm">Loading tasks...</div>;

    return (
        <div className="h-full bg-slate-50/50 p-6 overflow-y-auto">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                <table className="w-full text-sm text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50/50 text-slate-500 font-medium border-b border-slate-100">
                            <th className="w-10 px-4 py-3"></th>
                            <th className="px-4 py-3 font-semibold">Task Name</th>
                            <th className="w-32 px-4 py-3 font-semibold">Status</th>
                            <th className="w-32 px-4 py-3 font-semibold">Assignee</th>
                            <th className="w-32 px-4 py-3 font-semibold">Due Date</th>
                            <th className="w-24 px-4 py-3 font-semibold">Priority</th>
                            <th className="w-20 px-4 py-3 text-right"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                        {tasks?.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                                    No tasks found in this project.
                                </td>
                            </tr>
                        ) : (
                            tasks?.map((task: any) => (
                                <tr key={task.id} className="group hover:bg-slate-50/80 transition-colors">
                                    <td className="px-4 py-3">
                                        <div className="flex items-center">
                                            <GripVertical className="w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 transition mr-2 cursor-grab" />
                                            <button className="text-slate-300 hover:text-primary transition">
                                                {task.status === 'completed' ? (
                                                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                                                ) : (
                                                    <Circle className="w-5 h-5" />
                                                )}
                                            </button>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col">
                                            <span className={cn(
                                                "font-medium text-slate-900",
                                                task.status === 'completed' && "line-through text-slate-400"
                                            )}>
                                                {task.title}
                                            </span>
                                            <div className="flex items-center space-x-3 mt-1 text-[11px] text-slate-400 uppercase tracking-wide">
                                                <span className="flex items-center">
                                                    <MessageSquare className="w-3 h-3 mr-1" /> {task.comments_count || 0}
                                                </span>
                                                <span className="flex items-center">
                                                    <Paperclip className="w-3 h-3 mr-1" /> {task.attachments_count || 0}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={cn(
                                            "px-2 py-1 rounded text-[11px] font-bold uppercase tracking-wider",
                                            task.status === 'todo' && "bg-slate-100 text-slate-600",
                                            task.status === 'in_progress' && "bg-blue-100 text-blue-700",
                                            task.status === 'completed' && "bg-green-100 text-green-700"
                                        )}>
                                            {task.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center">
                                            <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold mr-2">
                                                {task.assignee_id ? 'U' : '?'}
                                            </div>
                                            <span className="text-slate-600 truncate">{task.assignee_name || 'Unassigned'}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center text-slate-500">
                                            <Clock className="w-3 h-3 mr-1.5" />
                                            {task.due_date ? format(new Date(task.due_date), 'MMM d') : '-'}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={cn("capitalize flex items-center", getPriorityColor(task.priority))}>
                                            <span className="w-1.5 h-1.5 rounded-full bg-current mr-2" />
                                            {task.priority}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <button className="p-1 text-slate-400 hover:text-slate-900 rounded opacity-0 group-hover:opacity-100 transition">
                                            <MoreHorizontal className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TaskListView;
