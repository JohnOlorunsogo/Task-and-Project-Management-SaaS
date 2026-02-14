# Project Service API Documentation

Base URL: `/projects`

## Endpoints

### 1. Create Project
Create a new project in the organization.

- **URL:** `/`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_PROJECTS`)
- **Request Body:** `CreateProjectRequest`

```json
{
  "name": "New Project",
  "description": "Project description",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31"
}
```

- **Response:** `ProjectResponse` (201 Created)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "New Project",
  "description": "Project description",
  "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "is_template": false,
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### 2. List My Projects
List projects where the current user is a member/owner.

- **URL:** `/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[ProjectResponse]` (200 OK)

---

### 3. List All Projects
List all projects in the organization (OrgAdmin/ProjAdmin only).

- **URL:** `/all`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `MANAGE_PROJECTS`)
- **Response:** `list[ProjectResponse]` (200 OK)

---

### 4. Get Project
Get details of a specific project.

- **URL:** `/{project_id}`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `ProjectResponse` (200 OK)

---

### 5. Update Project
Update project details.

- **URL:** `/{project_id}`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `EDIT_PROJECT`)
- **Request Body:** `UpdateProjectRequest`

```json
{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

- **Response:** `ProjectResponse` (200 OK)

---

### 6. Delete Project
Delete a project.

- **URL:** `/{project_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `DELETE_PROJECT`)
- **Response:** 204 No Content

---

### 7. Create Template
Create a project template.

- **URL:** `/templates`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_PROJECTS`)
- **Request Body:** `CreateProjectRequest`
- **Response:** `ProjectResponse` (201 Created)

---

### 8. List Templates
List all project templates in the organization.

- **URL:** `/templates/list`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[ProjectResponse]` (200 OK)

---

### 9. Create from Template
Create a new project from an existing template.

- **URL:** `/from-template/{template_id}`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_PROJECTS`)
- **Request Body:** `CreateFromTemplateRequest`

```json
{
  "name": "Project from Template",
  "description": "Custom description",
  "start_date": "2023-02-01",
  "end_date": "2023-11-30"
}
```

- **Response:** `ProjectResponse` (201 Created)

---

### 10. List Members
List all members of a project.

- **URL:** `/{project_id}/members`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW`)
- **Response:** `list[ProjectMemberResponse]` (200 OK)

---

### 11. Add Member
Add a user to the project.

- **URL:** `/{project_id}/members`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_MEMBERS`)
- **Request Body:** `AddProjectMemberRequest`

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "role": "team_member"
}
```

- **Response:** `ProjectMemberResponse` (201 Created)

---

### 12. Change Member Role
Update a member's role within the project.

- **URL:** `/{project_id}/members/{user_id}/role`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `ASSIGN_ROLES`)
- **Request Body:** `ChangeProjectRoleRequest`

```json
{
  "role": "project_manager"
}
```

- **Response:** `ProjectMemberResponse` (200 OK)

---

### 13. Remove Member
Remove a user from the project.

- **URL:** `/{project_id}/members/{user_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `MANAGE_MEMBERS`)
- **Response:** 204 No Content

---

### 14. Check Membership
Internal endpoint to check if a user is a member of a project.

- **URL:** `/{project_id}/check-membership?user_id={user_id}`
- **Method:** `GET`
- **Auth Required:** Yes (Service-to-Service or Admin)
- **Response:** `UserProjectMembershipResponse` (200 OK)
- **Errors:**
  - 404 Not Found: User is not a member.

---

### 15. List Custom Statuses
List custom statuses defined for a project.

- **URL:** `/{project_id}/statuses`
- **Method:** `GET`
- **Auth Required:** Yes (Permission: `VIEW`)
- **Response:** `list[CustomStatusResponse]` (200 OK)

---

### 16. Create Status
Create a new custom status for a project.

- **URL:** `/{project_id}/statuses`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `EDIT_PROJECT`)
- **Request Body:** `CreateStatusRequest`

```json
{
  "name": "In Review",
  "color": "#FF5733",
  "position": 1
}
```

- **Response:** `CustomStatusResponse` (201 Created)

---

### 17. Update Status
Update a custom status.

- **URL:** `/{project_id}/statuses/{status_id}`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `EDIT_PROJECT`)
- **Request Body:** `UpdateStatusRequest`

```json
{
  "name": "In QA",
  "color": "#33FF57"
}
```

- **Response:** `CustomStatusResponse` (200 OK)

---

### 18. Delete Status
Delete a custom status.

- **URL:** `/{project_id}/statuses/{status_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `EDIT_PROJECT`)
- **Response:** 204 No Content

## Data Models

### Request Models

**CreateProjectRequest / CreateProjectTemplateRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Min 1, max 255 chars. |
| description | string | No | |
| start_date | date | No | |
| end_date | date | No | |

**UpdateProjectRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | No | Max 255 chars. |
| description | string | No | |
| start_date | date | No | |
| end_date | date | No | |

**CreateFromTemplateRequest**
Same fields as CreateProjectRequest.

**AddProjectMemberRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| user_id | UUID | Yes | User to add. |
| role | string | No | Default: "team_member". Allowed: owner, admin, project_manager, team_member, viewer. |

**ChangeProjectRoleRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| role | string | Yes | Allowed: owner, admin, project_manager, team_member, viewer. |

**CreateStatusRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Min 1, max 100 chars. |
| color | string | No | Hex color code (e.g., #RRGGBB). |
| position | int | No | Default: 0. Order index. |

**UpdateStatusRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | No | Max 100 chars. |
| color | string | No | Hex color code. |
| position | int | No | |

### Response Models

**ProjectResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Project ID. |
| org_id | UUID | Organization ID. |
| name | string | Project name. |
| description | string | Description. |
| owner_id | UUID | Owner User ID. |
| start_date | date | Start date. |
| end_date | date | End date. |
| is_template | boolean | whether it is a template. |
| created_at | datetime | Creation timestamp. |

**ProjectMemberResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Membership ID. |
| project_id | UUID | Project ID. |
| user_id | UUID | User ID. |
| role | string | Role name. |
| created_at | datetime | Creation timestamp. |

**UserProjectMembershipResponse**
| Field | Type | Description |
|---|---|---|
| project_id | UUID | Project ID. |
| user_id | UUID | User ID. |
| role | string | Role name. |

**CustomStatusResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Status ID. |
| project_id | UUID | Project ID. |
| name | string | Status name. |
| position | int | Order index. |
| color | string | Hex color code. |
| is_default | boolean | Whether it is a default status. |
| created_at | datetime | Creation timestamp. |
