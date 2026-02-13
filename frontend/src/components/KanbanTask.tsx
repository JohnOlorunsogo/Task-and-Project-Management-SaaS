import React from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
    Clock,
    MessageSquare,
    GripVertical
} from "lucide-react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

interface KanbanTaskProps {
    task: any;
    isOverlay?: boolean;
}

const KanbanTask: React.FC<KanbanTaskProps> = ({ task, isOverlay }) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: task.id });

    const style = {
        transform: CSS.Translate.toString(transform),
        transition,
        opacity: isDragging ? 0.3 : 1,
    };

    const getPriorityColor = (priority: string) => {
        switch (priority.toLowerCase()) {
            case 'high': return 'bg-red-500';
            case 'medium': return 'bg-orange-500';
            case 'low': return 'bg-blue-500';
            default: return 'bg-slate-400';
        }
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={cn(
                "bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition active:cursor-grabbing group",
                isOverlay && "shadow-xl border-primary/20 ring-1 ring-primary/10"
            )}
        >
            <div className="flex items-start justify-between mb-2">
                <div className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase text-white", getPriorityColor(task.priority))}>
                    {task.priority}
                </div>
                <div {...attributes} {...listeners} className="p-1 -mr-1 text-slate-300 hover:text-slate-900 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition">
                    <GripVertical className="w-4 h-4" />
                </div>
            </div>

            <h4 className={cn(
                "font-semibold text-slate-800 text-sm mb-2",
                task.status === 'completed' && "line-through text-slate-400"
            )}>
                {task.title}
            </h4>

            {task.description && (
                <p className="text-xs text-slate-500 line-clamp-2 mb-3 leading-relaxed">
                    {task.description}
                </p>
            )}

            <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-50">
                <div className="flex items-center space-x-3 text-slate-400">
                    <div className="flex items-center text-[10px]">
                        <MessageSquare className="w-3 h-3 mr-1" />
                        {task.comments_count || 0}
                    </div>
                    {task.due_date && (
                        <div className="flex items-center text-[10px]">
                            <Clock className="w-3 h-3 mr-1" />
                            {format(new Date(task.due_date), 'MMM d')}
                        </div>
                    )}
                </div>

                <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600">
                    {task.assignee_id ? 'U' : '?'}
                </div>
            </div>
        </div>
    );
};

export default KanbanTask;
