import React, { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    DndContext,
    DragOverlay,
    closestCorners,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragStartEvent,
    DragEndEvent,
    DragOverEvent,
    defaultDropAnimationSideEffects,
    DropAnimation,
} from "@dnd-kit/core";
import {
    sortableKeyboardCoordinates,
} from "@dnd-kit/sortable";
import { apiClient } from "@/api/client";
import KanbanColumn from "../components/KanbanColumn";
import KanbanTask from "../components/KanbanTask";

interface TaskBoardViewProps {
    projectId: string;
}

const COLUMNS = [
    { id: "todo", title: "To Do" },
    { id: "in_progress", title: "In Progress" },
    { id: "completed", title: "Completed" },
];

const TaskBoardView: React.FC<TaskBoardViewProps> = ({ projectId }) => {
    const queryClient = useQueryClient();
    const [activeTask, setActiveTask] = useState<any>(null);

    const { data: tasks, isLoading } = useQuery({
        queryKey: ["tasks", projectId],
        queryFn: async () => {
            const response = await apiClient.get(`/tasks?project_id=${projectId}`);
            return response.data;
        },
    });

    const updateTaskMutation = useMutation({
        mutationFn: async ({ taskId, status }: { taskId: string; status: string }) => {
            return apiClient.patch(`/tasks/${taskId}`, { status });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tasks", projectId] });
        },
    });

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 5,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const tasksByStatus = useMemo(() => {
        const groups: Record<string, any[]> = {
            todo: [],
            in_progress: [],
            completed: [],
        };
        tasks?.forEach((task: any) => {
            if (groups[task.status]) {
                groups[task.status].push(task);
            }
        });
        return groups;
    }, [tasks]);

    const handleDragStart = (event: DragStartEvent) => {
        const { active } = event;
        const task = tasks?.find((t: any) => t.id === active.id);
        setActiveTask(task);
    };

    const handleDragOver = (_event: DragOverEvent) => {
        // Implement logic for moving between columns if using sorting within columns
    };

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveTask(null);

        if (!over) return;

        const taskId = active.id as string;
        const overId = over.id as string;

        // If dropped on a column
        const isOverColumn = COLUMNS.some((col) => col.id === overId);
        const task = tasks?.find((t: any) => t.id === taskId);

        if (isOverColumn && task && task.status !== overId) {
            updateTaskMutation.mutate({ taskId, status: overId });
        } else {
            // If dropped on another task
            const overTask = tasks?.find((t: any) => t.id === overId);
            if (overTask && task && task.status !== overTask.status) {
                updateTaskMutation.mutate({ taskId, status: overTask.status });
            }
        }
    };

    if (isLoading) return <div className="p-12 text-center text-slate-500">Loading board...</div>;

    const dropAnimation: DropAnimation = {
        sideEffects: defaultDropAnimationSideEffects({
            styles: {
                active: {
                    opacity: "0.5",
                },
            },
        }),
    };

    return (
        <div className="h-full bg-slate-50/50 p-6 overflow-x-auto">
            <DndContext
                sensors={sensors}
                collisionDetection={closestCorners}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDragEnd={handleDragEnd}
            >
                <div className="flex space-x-6 h-full min-w-max">
                    {COLUMNS.map((column) => (
                        <KanbanColumn
                            key={column.id}
                            id={column.id}
                            title={column.title}
                            tasks={tasksByStatus[column.id]}
                        />
                    ))}
                </div>

                <DragOverlay dropAnimation={dropAnimation}>
                    {activeTask ? (
                        <div className="w-80 rotate-2 pointer-events-none">
                            <KanbanTask task={activeTask} isOverlay />
                        </div>
                    ) : null}
                </DragOverlay>
            </DndContext>
        </div>
    );
};

export default TaskBoardView;
