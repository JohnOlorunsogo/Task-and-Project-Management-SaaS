import { useAuthStore } from "@/store/authStore";
import { OrgRole, Permission, PROJECT_PERMISSIONS, ProjectRole } from "@/types/rbac";

export const usePermissions = (currentProjectRole?: ProjectRole | string) => {
    const { user } = useAuthStore();

    const hasOrgRole = (roles: OrgRole[]) => {
        return user?.org_role && roles.includes(user.org_role as OrgRole);
    };

    const hasPermission = (permission: Permission) => {
        // OrgAdmin has all permissions
        if (user?.org_role === OrgRole.ORG_ADMIN) return true;

        if (!currentProjectRole) return false;

        const role = currentProjectRole as ProjectRole;
        const allowedPermissions = PROJECT_PERMISSIONS[role] || [];

        return allowedPermissions.includes(permission);
    };

    const canEditTask = (taskAssigneeId?: string) => {
        if (hasPermission(Permission.EDIT_ANY_TASK)) return true;

        if (hasPermission(Permission.EDIT_ASSIGNED_TASK)) {
            return taskAssigneeId === user?.id;
        }

        return false;
    };

    return {
        hasOrgRole,
        hasPermission,
        canEditTask,
        isAdmin: user?.org_role === OrgRole.ORG_ADMIN || user?.org_role === OrgRole.PROJ_ADMIN,
    };
};
