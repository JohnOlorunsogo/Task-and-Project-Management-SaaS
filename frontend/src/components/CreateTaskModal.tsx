import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { X, Loader2 } from "lucide-react";
import { apiClient } from "@/api/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const taskSchema = z.object({
    title: z.string().min(1, "Title is required"),
    description: z.string().optional(),
    priority: z.enum(["low", "medium", "high"]),
    status: z.enum(["todo", "in_progress", "completed"]),
    due_date: z.string().optional(),
    assignee_id: z.string().optional(),
});

type TaskFormValues = z.infer<typeof taskSchema>;

interface CreateTaskModalProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ projectId, isOpen, onClose }) => {
    const queryClient = useQueryClient();

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<TaskFormValues>({
        resolver: zodResolver(taskSchema),
        defaultValues: {
            priority: "medium",
            status: "todo",
        },
    });

    const mutation = useMutation({
        mutationFn: async (data: TaskFormValues) => {
            return apiClient.post("/tasks", { ...data, project_id: projectId });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks", projectId] });
            reset();
            onClose();
        },
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <h3 className="font-bold text-lg">Create New Task</h3>
                    <button onClick={onClose} className="p-1 hover:bg-slate-200 rounded-full transition">
                        <X className="w-5 h-5 text-slate-500" />
                    </button>
                </div>

                <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Task Title</label>
                        <input
                            {...register("title")}
                            className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition"
                            placeholder="What needs to be done?"
                            autoFocus
                        />
                        {errors.title && <p className="text-destructive text-xs mt-1">{errors.title.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                        <textarea
                            {...register("description")}
                            rows={3}
                            className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition resize-none"
                            placeholder="Add more details..."
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
                            <select
                                {...register("priority")}
                                className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white transition"
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
                            <select
                                {...register("status")}
                                className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white transition"
                            >
                                <option value="todo">To Do</option>
                                <option value="in_progress">In Progress</option>
                                <option value="completed">Completed</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                        <input
                            {...register("due_date")}
                            type="date"
                            className="w-full px-3 py-2 border rounded-md border-slate-300 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition"
                        />
                    </div>

                    <div className="pt-4 flex items-center justify-end space-x-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-md transition"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={mutation.isPending}
                            className="px-6 py-2 bg-primary text-white text-sm font-bold rounded-md hover:bg-primary/90 transition flex items-center shadow-md disabled:opacity-50"
                        >
                            {mutation.isPending && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                            Create Task
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateTaskModal;
