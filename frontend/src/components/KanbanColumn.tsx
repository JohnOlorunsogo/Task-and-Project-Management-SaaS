import React from "react";
import { useDroppable } from "@dnd-kit/core";
import {
    SortableContext,
    verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import KanbanTask from "./KanbanTask.tsx";
import { cn } from "@/lib/utils";

interface KanbanColumnProps {
    id: string;
    title: string;
    tasks: any[];
}

const KanbanColumn: React.FC<KanbanColumnProps> = ({ id, title, tasks }) => {
    const { setNodeRef, isOver } = useDroppable({
        id: id,
    });

    return (
        <div
            ref={setNodeRef}
            className={cn(
                "w-80 flex flex-col h-full bg-slate-100/50 rounded-xl border border-slate-200 transition-colors",
                isOver && "bg-slate-200/50 border-primary/20"
            )}
        >
            <div className="p-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-slate-700 text-sm uppercase tracking-wider">{title}</h3>
                    <span className="bg-slate-200 text-slate-500 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        {tasks.length}
                    </span>
                </div>
            </div>

            <div className="flex-1 px-3 pb-4 space-y-3 overflow-y-auto">
                <SortableContext
                    id={id}
                    items={tasks.map((t) => t.id)}
                    strategy={verticalListSortingStrategy}
                >
                    {tasks.map((task) => (
                        <KanbanTask key={task.id} task={task} />
                    ))}
                </SortableContext>

                {tasks.length === 0 && !isOver && (
                    <div className="h-24 border-2 border-dashed border-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-xs text-center p-4">
                        No tasks here
                    </div>
                )}
            </div>
        </div>
    );
};

export default KanbanColumn;
