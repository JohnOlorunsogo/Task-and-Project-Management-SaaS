import React from "react";
import { usePermissions } from "@/hooks/usePermissions";
import { Permission, ProjectRole } from "@/types/rbac";

interface PermissionGateProps {
    permission?: Permission;
    projectRole?: ProjectRole | string;
    fallback?: React.ReactNode;
    children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({
    permission,
    projectRole,
    fallback = null,
    children,
}) => {
    const { hasPermission } = usePermissions(projectRole);

    if (permission && !hasPermission(permission)) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
};
