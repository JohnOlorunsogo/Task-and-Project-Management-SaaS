import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, X, CheckSquare, Info } from "lucide-react";
import { apiClient } from "@/api/client";
import { wsService } from "@/api/ws";
import { cn } from "@/lib/utils";

const NotificationCenter: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);

    const { data: notifications, refetch } = useQuery({
        queryKey: ["notifications"],
        queryFn: async () => {
            const response = await apiClient.get("/notifications");
            const data = response.data;
            setUnreadCount(data.filter((n: any) => !n.is_read).length);
            return data;
        },
    });

    useEffect(() => {
        wsService.connect();
        const unsubscribe = wsService.subscribe((data) => {
            console.log("New notification:", data);
            refetch();
        });
        return () => unsubscribe();
    }, [refetch]);

    const markAsRead = async (id: string) => {
        await apiClient.patch(`/notifications/${id}/read`);
        refetch();
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 text-slate-500 hover:bg-slate-50 rounded-full relative transition"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 bg-destructive text-white text-[10px] font-bold rounded-full border-2 border-white flex items-center justify-center">
                        {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)} />
                    <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-xl z-40 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                            <h3 className="font-bold text-sm">Notifications</h3>
                            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="max-h-96 overflow-y-auto divide-y divide-slate-100">
                            {notifications?.length === 0 ? (
                                <div className="p-8 text-center text-slate-400 text-xs">
                                    No notifications yet.
                                </div>
                            ) : (
                                notifications?.map((n: any) => (
                                    <div
                                        key={n.id}
                                        className={cn(
                                            "p-4 hover:bg-slate-50 transition cursor-pointer flex items-start space-x-3",
                                            !n.is_read && "bg-primary/5"
                                        )}
                                        onClick={() => !n.is_read && markAsRead(n.id)}
                                    >
                                        <div className={cn(
                                            "p-2 rounded-full",
                                            n.type === 'task_assigned' ? "bg-blue-100 text-blue-600" : "bg-slate-100 text-slate-600"
                                        )}>
                                            {n.type === 'task_assigned' ? <CheckSquare className="w-4 h-4" /> : <Info className="w-4 h-4" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-slate-900 font-medium leading-snug">{n.title}</p>
                                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{n.message}</p>
                                            <p className="text-[10px] text-slate-400 mt-2">Just now</p>
                                        </div>
                                        {!n.is_read && <div className="w-2 h-2 bg-primary rounded-full mt-2" />}
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/50 text-center">
                            <button className="text-[10px] font-bold text-primary uppercase tracking-wider hover:underline">
                                View all notifications
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default NotificationCenter;
