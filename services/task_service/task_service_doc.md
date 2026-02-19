# Task Service API Documentation

Base URL: `/tasks`

## Architecture Notes

> [!IMPORTANT]
> **Project-Level RBAC Enforcement**: Every endpoint enforces project membership checks. If a user is not a member of the project a task belongs to, the request is denied with `403 Forbidden`. Org admins bypass project membership requirements.

> [!NOTE]
> **Two Permission Patterns**: Endpoints with an explicit `project_id` (views, create, list) use `require_project_permission`. Endpoints with only `task_id` (get, update, delete, comments, time logs) use `require_task_project_permission`, which resolves the task's project from the database first.

> [!NOTE]
> **Request-Time Role Resolution**: `org_role` is resolved at request time via Redis cache with HTTP fallback to org_service — never read from the JWT.

## Endpoints

### 1. Create Task
Create a new task in a project.

- **URL:** `/`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `CREATE_TASK` on target project)
- **Request Body:** `CreateTaskRequest`

```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Implement login page",
  "description": "Build the login form with validation",
  "status_name": "To Do",
  "priority": "high",
  "due_date": "2023-12-31T00:00:00Z",
  "assignee_ids": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
}
```

- **Response:** `TaskResponse` (201 Created)

---

### 2. List Tasks
List tasks, optionally filtered by project, assignee, status, or priority.

- **URL:** `/`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW` when `project_id` provided)
- **Query Params:**
  - `project_id` (UUID, optional) — Filter by project. Triggers permission check.
  - `assignee_id` (UUID, optional) — Filter by assignee.
  - `status_name` (string, optional) — Filter by status.
  - `priority` (string, optional) — Filter by priority.
- **Response:** `list[TaskListResponse]` (200 OK)

---

### 3. My Tasks
Get tasks assigned to the current user.

- **URL:** `/my`
- **Method:** `GET`
- **Auth Required:** Yes
- **Note:** No project-level check — user only sees their own assigned tasks.
- **Response:** `list[TaskListResponse]` (200 OK)

---

### 4. Get Task
Get full details of a single task.

- **URL:** `/{task_id}`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Response:** `TaskResponse` (200 OK)

---

### 5. Update Task
Update a task's fields.

- **URL:** `/{task_id}`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `EDIT_TASK` on task's project)
- **Request Body:** `UpdateTaskRequest`

```json
{
  "title": "Updated title",
  "status_name": "In Progress",
  "priority": "critical"
}
```

- **Response:** `TaskResponse` (200 OK)

---

### 6. Delete Task
Delete a task.

- **URL:** `/{task_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `DELETE_TASK` on task's project)
- **Response:** 204 No Content

---

### 7. Add Comment
Add a comment to a task. Supports threaded replies via `parent_id`.

- **URL:** `/{task_id}/comments`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `POST_COMMENT` on task's project)
- **Request Body:** `CreateCommentRequest`

```json
{
  "content": "Looks good, merging now.",
  "parent_id": null,
  "mentions": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
}
```

- **Response:** `CommentResponse` (201 Created)

---

### 8. List Comments
List all comments on a task.

- **URL:** `/{task_id}/comments`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Response:** `list[CommentResponse]` (200 OK)

---

### 9. Log Time
Create a manual time entry for a task.

- **URL:** `/{task_id}/time-logs`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Request Body:** `CreateTimeEntryRequest`

```json
{
  "started_at": "2023-10-27T09:00:00Z",
  "ended_at": "2023-10-27T12:00:00Z",
  "duration_seconds": 10800,
  "description": "Working on implementation"
}
```

- **Response:** `TimeEntryResponse` (201 Created)

---

### 10. Start Timer
Start a live timer on a task.

- **URL:** `/{task_id}/time-entries/start`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Response:** `StartTimerResponse` (201 Created)

---

### 11. Stop Timer
Stop a running timer.

- **URL:** `/{task_id}/time-entries/{entry_id}/stop`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Response:** `TimeEntryResponse` (200 OK)

---

### 12. List Time Entries
List all time entries for a task.

- **URL:** `/{task_id}/time-entries`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW` on task's project)
- **Response:** `list[TimeEntryResponse]` (200 OK)

---

### 13. Kanban View
Get tasks grouped by status columns for a project.

- **URL:** `/views/kanban`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW`)
- **Query Params:** `project_id` (UUID, required)
- **Response:** `KanbanResponse` (200 OK)

---

### 14. Gantt View
Get tasks with dates and dependencies for Gantt chart rendering.

- **URL:** `/views/gantt`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW`)
- **Query Params:** `project_id` (UUID, required)
- **Response:** `list[GanttTaskResponse]` (200 OK)

---

### 15. Calendar View
Get tasks with due dates for calendar rendering.

- **URL:** `/views/calendar`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW`)
- **Query Params:** `project_id` (UUID, required)
- **Response:** `list[CalendarTaskResponse]` (200 OK)

---

## Permission Matrix

| Endpoint | Permission Required | Resolution |
|---|---|---|
| `POST /tasks` | `CREATE_TASK` | project_id from body |
| `GET /tasks?project_id=` | `VIEW` | project_id from query |
| `GET /tasks/my` | *none (self-only)* | — |
| `GET /tasks/{id}` | `VIEW` | project from task DB |
| `PUT /tasks/{id}` | `EDIT_TASK` | project from task DB |
| `DELETE /tasks/{id}` | `DELETE_TASK` | project from task DB |
| `POST /tasks/{id}/comments` | `POST_COMMENT` | project from task DB |
| `GET /tasks/{id}/comments` | `VIEW` | project from task DB |
| Time entries | `VIEW` | project from task DB |
| Views (kanban/gantt/calendar) | `VIEW` | project_id from query |

> [!NOTE]
> Org admins (`org_admin`, `proj_admin`) bypass project membership requirements for all permissions.

## Data Models

### Request Models

**CreateTaskRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| project_id | UUID | Yes | Target project. |
| title | string | Yes | Min 1, max 500 chars. |
| description | string | No | |
| status_id | UUID | No | Custom status ID. |
| status_name | string | No | Default: "To Do". |
| priority | string | No | Default: "medium". Allowed: low, medium, high, critical. |
| due_date | datetime | No | |
| start_date | datetime | No | |
| end_date | datetime | No | |
| custom_properties | object | No | Key-value pairs for custom fields. |
| assignee_ids | list[UUID] | No | Users to assign. |

**UpdateTaskRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| title | string | No | Max 500 chars. |
| description | string | No | |
| status_id | UUID | No | Custom status ID. |
| status_name | string | No | |
| priority | string | No | Allowed: low, medium, high, critical. |
| due_date | datetime | No | |
| start_date | datetime | No | |
| end_date | datetime | No | |
| custom_properties | object | No | |
| position | int | No | Board position. |

**CreateCommentRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| content | string | Yes | Min 1 char. |
| parent_id | UUID | No | Reply to a comment. |
| mentions | list[UUID] | No | Mentioned user IDs. |

**CreateTimeEntryRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| started_at | datetime | Yes | When work started. |
| ended_at | datetime | No | When work ended. |
| duration_seconds | int | No | Manual duration. |
| description | string | No | Description of work. |

### Response Models

**TaskResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Task ID. |
| project_id | UUID | Project ID. |
| org_id | UUID | Organization ID. |
| parent_id | UUID | Parent task (subtask). |
| title | string | Task title. |
| description | string | Description. |
| status_id | UUID | Custom status ID. |
| status_name | string | Status label. |
| priority | string | Priority level. |
| due_date | datetime | Due date. |
| start_date | datetime | Start date. |
| end_date | datetime | End date. |
| custom_properties | object | Custom fields. |
| position | int | Board position. |
| created_by | UUID | Creator. |
| created_at | datetime | Creation time. |
| updated_at | datetime | Last update time. |
| assignments | list[TaskAssignmentResponse] | Assignees. |
| subtask_count | int | Number of subtasks. |

**TaskListResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Task ID. |
| project_id | UUID | Project ID. |
| title | string | Task title. |
| status_name | string | Status label. |
| priority | string | Priority level. |
| due_date | datetime | Due date. |
| position | int | Board position. |
| assignee_count | int | Number of assignees. |
| subtask_count | int | Number of subtasks. |

**CommentResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Comment ID. |
| task_id | UUID | Parent task. |
| parent_id | UUID | Parent comment (thread). |
| author_id | UUID | Author user ID. |
| content | string | Comment body. |
| mentions | list | Mentioned user IDs. |
| created_at | datetime | Creation time. |
| updated_at | datetime | Last update time. |
| replies | list[CommentResponse] | Nested replies. |

**TimeEntryResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Entry ID. |
| task_id | UUID | Task. |
| user_id | UUID | User. |
| started_at | datetime | Start time. |
| ended_at | datetime | End time. |
| duration_seconds | int | Duration. |
| description | string | Work description. |
| created_at | datetime | Creation time. |

**StartTimerResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Entry ID. |
| task_id | UUID | Task. |
| user_id | UUID | User. |
| started_at | datetime | Timer start time. |

**KanbanResponse**
| Field | Type | Description |
|---|---|---|
| columns | list[KanbanColumn] | Board columns. |

**KanbanColumn**
| Field | Type | Description |
|---|---|---|
| status_id | UUID | Status ID. |
| status_name | string | Column label. |
| tasks | list[TaskListResponse] | Tasks in column. |

**GanttTaskResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Task ID. |
| title | string | Task title. |
| start_date | datetime | Start date. |
| end_date | datetime | End date. |
| due_date | datetime | Due date. |
| dependencies | list[UUID] | Predecessor task IDs. |
| progress | float | Completion (0-1). |

**CalendarTaskResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Task ID. |
| title | string | Task title. |
| due_date | datetime | Due date. |
| priority | string | Priority level. |
| status_name | string | Current status. |
