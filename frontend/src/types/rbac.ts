export enum OrgRole {
    ORG_ADMIN = "org_admin",
    PROJ_ADMIN = "proj_admin",
    MEMBER = "member",
}

export enum ProjectRole {
    OWNER = "owner",
    ADMIN = "admin",
    PROJECT_MANAGER = "project_manager",
    TEAM_MEMBER = "team_member",
    VIEWER = "viewer",
}

export enum Permission {
    DELETE_PROJECT = "delete_project",
    EDIT_PROJECT = "edit_project",
    MANAGE_MEMBERS = "manage_members",
    ASSIGN_ROLES = "assign_roles",
    CREATE_TASK = "create_task",
    EDIT_ANY_TASK = "edit_any_task",
    DELETE_ANY_TASK = "delete_any_task",
    EDIT_ASSIGNED_TASK = "edit_assigned_task",
    DELETE_ASSIGNED_TASK = "delete_assigned_task",
    ASSIGN_TASK = "assign_task",
    CHANGE_STATUS = "change_status",
    POST_COMMENT = "post_comment",
    LOG_TIME = "log_time",
    MANAGE_ATTACHMENTS = "manage_attachments",
    VIEW = "view",
}

export const PROJECT_PERMISSIONS: Record<ProjectRole, Permission[]> = {
    [ProjectRole.OWNER]: Object.values(Permission),
    [ProjectRole.ADMIN]: [
        Permission.EDIT_PROJECT,
        Permission.MANAGE_MEMBERS,
        Permission.ASSIGN_ROLES,
        Permission.CREATE_TASK,
        Permission.EDIT_ANY_TASK,
        Permission.DELETE_ANY_TASK,
        Permission.ASSIGN_TASK,
        Permission.CHANGE_STATUS,
        Permission.POST_COMMENT,
        Permission.LOG_TIME,
        Permission.MANAGE_ATTACHMENTS,
        Permission.VIEW,
    ],
    [ProjectRole.PROJECT_MANAGER]: [
        Permission.CREATE_TASK,
        Permission.EDIT_ANY_TASK,
        Permission.DELETE_ANY_TASK,
        Permission.ASSIGN_TASK,
        Permission.CHANGE_STATUS,
        Permission.POST_COMMENT,
        Permission.LOG_TIME,
        Permission.MANAGE_ATTACHMENTS,
        Permission.VIEW,
    ],
    [ProjectRole.TEAM_MEMBER]: [
        Permission.CREATE_TASK,
        Permission.EDIT_ASSIGNED_TASK,
        Permission.DELETE_ASSIGNED_TASK,
        Permission.CHANGE_STATUS,
        Permission.POST_COMMENT,
        Permission.LOG_TIME,
        Permission.MANAGE_ATTACHMENTS,
        Permission.VIEW,
    ],
    [ProjectRole.VIEWER]: [Permission.VIEW],
};
