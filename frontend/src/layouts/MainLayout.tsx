import React from "react";
import { NavLink, useNavigate, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
    LayoutDashboard,
    FolderKanban,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import NotificationCenter from "@/components/NotificationCenter";
import { useOrgStore } from "@/store/orgStore";
import { apiClient } from "@/api/client";

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isCollapsed, setIsCollapsed] = React.useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = React.useState(false);
    const { user, logout } = useAuthStore();
    const { orgs, currentOrgId, setCurrentOrg, fetchOrgs } = useOrgStore();
    const navigate = useNavigate();

    const [orgCheckDone, setOrgCheckDone] = React.useState(false);
    const [hasOrgs, setHasOrgs] = React.useState(true);

    React.useEffect(() => {
        fetchOrgs().then((orgs) => {
            setHasOrgs(orgs.length > 0);
            setOrgCheckDone(true);
        });
    }, [fetchOrgs]);

    const handleLogout = () => {
        useOrgStore.getState().clearOrgs();
        logout();
        navigate("/login");
    };

    // Fetch current user's org role
    const { data: myRole } = useQuery({
        queryKey: ["my-role", currentOrgId],
        queryFn: async () => {
            const res = await apiClient.get(`/organizations/${currentOrgId}/members`);
            const members = res.data;
            const me = members.find((m: any) => m.user_id === user?.id);
            return me?.role || null;
        },
        enabled: !!currentOrgId && !!user?.id,
    });

    // If user has no orgs, redirect to onboarding
    if (orgCheckDone && !hasOrgs) {
        return <Navigate to="/onboarding" replace />;
    }

    const navItems = [
        { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
        { icon: FolderKanban, label: "My Projects", path: "/projects" }, // Future: expanded list
        { icon: Settings, label: "Settings", path: "/settings" },
    ];

    return (
        <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">
            {/* Sidebar */}
            <aside
                className={cn(
                    "bg-white border-r border-slate-200 transition-all duration-300 flex flex-col z-20",
                    isCollapsed ? "w-16" : "w-64"
                )}
            >
                <div className="h-16 flex items-center px-4 border-b border-slate-100">
                    <div className="w-8 h-8 bg-primary rounded flex items-center justify-center shrink-0">
                        <span className="text-white font-bold text-lg">T</span>
                    </div>
                    {!isCollapsed && <span className="ml-3 font-bold text-lg truncate">TaskPM</span>}
                </div>

                {!isCollapsed && (
                    <div className="px-4 py-4">
                        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                            Organization
                        </label>
                        <select
                            value={currentOrgId || ""}
                            onChange={(e) => {
                                if (e.target.value === "create-new") {
                                    navigate("/onboarding");
                                } else {
                                    setCurrentOrg(e.target.value);
                                }
                            }}
                            className="w-full bg-slate-50 border border-slate-200 rounded-md px-2 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/10 transition"
                        >
                            <option value="" disabled>Select Organization</option>
                            {orgs.map((org) => (
                                <option key={org.id} value={org.id}>
                                    {org.name}
                                </option>
                            ))}
                            <option value="create-new" className="text-primary font-medium">
                                + Create New Org
                            </option>
                        </select>
                    </div>
                )}

                <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => cn(
                                "flex items-center px-3 py-2 rounded-md transition-colors",
                                isActive
                                    ? "bg-slate-100 text-primary font-medium"
                                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                            )}
                        >
                            <item.icon className="w-5 h-5 shrink-0" />
                            {!isCollapsed && <span className="ml-3 truncate">{item.label}</span>}
                        </NavLink>
                    ))}

                    <div className="pt-4 pb-2">
                        <div className={cn("px-3 mb-2", isCollapsed ? "opacity-0" : "opacity-100")}>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                Teams
                            </span>
                        </div>
                        {/* Mock Teams listing */}
                        <div className="space-y-1">
                            <button className="w-full flex items-center px-3 py-1.5 rounded-md text-slate-600 hover:bg-slate-50 text-sm">
                                <div className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                                {!isCollapsed && <span className="ml-3 truncate">Engineering</span>}
                            </button>
                            <button className="w-full flex items-center px-3 py-1.5 rounded-md text-slate-600 hover:bg-slate-50 text-sm">
                                <div className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                                {!isCollapsed && <span className="ml-3 truncate">Marketing</span>}
                            </button>
                        </div>
                    </div>
                </nav>

                <div className="p-2 border-t border-slate-100">
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="w-full flex items-center px-3 py-2 rounded-md text-slate-600 hover:bg-slate-50 transition-colors"
                    >
                        {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                        {!isCollapsed && <span className="ml-3">Collapse</span>}
                    </button>

                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center px-3 py-2 rounded-md text-destructive hover:bg-destructive/5 transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        {!isCollapsed && <span className="ml-3">Logout</span>}
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Header */}
                <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10 shrink-0">
                    <div className="flex items-center space-x-2">
                        <h2 className="text-lg font-semibold text-slate-800 truncate">
                            {user?.full_name ? `Dashboard` : "Welcome"}
                        </h2>
                        {currentOrgId && orgs.find(o => o.id === currentOrgId) && (
                            <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs font-medium">
                                {orgs.find(o => o.id === currentOrgId)?.name}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center space-x-4">
                        <NotificationCenter />

                        <div className="h-8 w-px bg-slate-200 mx-2" />

                        <div className="relative">
                            <button
                                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                                className="flex items-center space-x-3 hover:bg-slate-50 p-2 rounded-lg transition-colors outline-none"
                            >
                                <div className="text-right hidden sm:block">
                                    <p className="text-sm font-medium text-slate-900 leading-none">{user?.full_name}</p>
                                    {myRole && (
                                        <p className="text-xs text-slate-500 mt-1 uppercase">{myRole.replace('_', ' ')}</p>
                                    )}
                                </div>
                                <div className="w-9 h-9 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold border border-primary/10">
                                    {user?.full_name?.charAt(0)}
                                </div>
                            </button>

                            {/* User Dropdown */}
                            {isUserMenuOpen && (
                                <>
                                    <div
                                        className="fixed inset-0 z-30"
                                        onClick={() => setIsUserMenuOpen(false)}
                                    />
                                    <div className="absolute right-0 top-14 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-40 animate-in fade-in zoom-in-95 duration-200">
                                        <div className="px-4 py-3 border-b border-slate-100 sm:hidden">
                                            <p className="text-sm font-medium text-slate-900">{user?.full_name}</p>
                                            <p className="text-xs text-slate-500">{user?.email}</p>
                                        </div>
                                        <button
                                            onClick={() => {
                                                setIsUserMenuOpen(false);
                                                navigate("/settings");
                                            }}
                                            className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center"
                                        >
                                            <Settings className="w-4 h-4 mr-2 text-slate-400" />
                                            Settings
                                        </button>
                                        <button
                                            onClick={() => {
                                                setIsUserMenuOpen(false);
                                                handleLogout();
                                            }}
                                            className="w-full text-left px-4 py-2 text-sm text-destructive hover:bg-destructive/5 flex items-center"
                                        >
                                            <LogOut className="w-4 h-4 mr-2" />
                                            Logout
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </header>

                {/* Scrollable Content */}
                <main className="flex-1 overflow-y-auto overflow-x-hidden p-6">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
