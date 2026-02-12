"""Kafka event schema definitions."""

from __future__ import annotations

TOPICS = {
    "users": "taskpm.users",
    "organizations": "taskpm.organizations",
    "projects": "taskpm.projects",
    "tasks": "taskpm.tasks",
    "comments": "taskpm.comments",
    "notifications": "taskpm.notifications",
    "files": "taskpm.files",
}

# Event type constants
USER_REGISTERED = "user.registered"
USER_UPDATED = "user.updated"

ORG_CREATED = "organization.created"
ORG_MEMBER_ADDED = "organization.member_added"
ORG_MEMBER_REMOVED = "organization.member_removed"
ORG_MEMBER_ROLE_CHANGED = "organization.member_role_changed"

PROJECT_CREATED = "project.created"
PROJECT_UPDATED = "project.updated"
PROJECT_DELETED = "project.deleted"
PROJECT_MEMBER_ADDED = "project.member_added"
PROJECT_MEMBER_REMOVED = "project.member_removed"
PROJECT_MEMBER_ROLE_CHANGED = "project.member_role_changed"

TASK_CREATED = "task.created"
TASK_UPDATED = "task.updated"
TASK_DELETED = "task.deleted"
TASK_STATUS_CHANGED = "task.status_changed"
TASK_ASSIGNED = "task.assigned"
TASK_UNASSIGNED = "task.unassigned"

COMMENT_ADDED = "comment.added"
COMMENT_UPDATED = "comment.updated"
COMMENT_DELETED = "comment.deleted"

FILE_UPLOADED = "file.uploaded"
FILE_VERSION_ADDED = "file.version_added"
FILE_DELETED = "file.deleted"
