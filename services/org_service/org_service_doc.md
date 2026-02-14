# Organization Service API Documentation

Base URL: `/organizations`

## Endpoints

### 1. Create Organization
Create a new organization.

- **URL:** `/`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:** `CreateOrgRequest`

```json
{
  "name": "My Company",
  "slug": "my-company"
}
```

- **Response:** `OrgResponse` (201 Created)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "My Company",
  "slug": "my-company",
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### 2. List My Organizations
List organizations where the current user is a member/owner.

- **URL:** `/me`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[OrgResponse]` (200 OK)

---

### 3. List User Memberships
List all memberships for a specific user (Internal/Admin or Self use).

- **URL:** `/memberships`
- **Method:** `GET`
- **Query Params:** `user_id` (UUID)
- **Auth Required:** Yes
- **Response:** `list[UserMembershipResponse]` (200 OK)

```json
[
  {
    "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "org_name": "My Company",
    "role": "org_admin"
  }
]
```

---

### 4. Get Organization
Get details of a specific organization.

- **URL:** `/{org_id}`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `OrgResponse` (200 OK)

---

### 5. Update Organization
Update organization details.

- **URL:** `/{org_id}`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `MANAGE_ORG_SETTINGS`)
- **Request Body:** `UpdateOrgRequest`

```json
{
  "name": "New Company Name"
}
```

- **Response:** `OrgResponse` (200 OK)

---

### 6. List Members
List all members of an organization.

- **URL:** `/{org_id}/members`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[OrgMemberResponse]` (200 OK)

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "role": "member",
    "created_at": "2023-10-27T10:00:00Z",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
]
```

---

### 7. Add Member
Add a new member to the organization. Can be existing user by ID or invitation by email.

- **URL:** `/{org_id}/members`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_ORG_MEMBERS`)
- **Request Body:** `AddMemberRequest`

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", // Optional
  "email": "new.member@example.com", // Optional, if user_id not provided
  "role": "member" // default: member
}
```

- **Response:** `OrgMemberResponse` (201 Created)

---

### 8. Remove Member
Remove a user from the organization.

- **URL:** `/{org_id}/members/{user_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `MANAGE_ORG_MEMBERS`)
- **Response:** 204 No Content

---

### 9. Change Member Role
Update a member's role within the organization.

- **URL:** `/{org_id}/members/{user_id}/role`
- **Method:** `PUT`
- **Auth Required:** Yes (Permission: `MANAGE_ORG_ROLES`)
- **Request Body:** `ChangeMemberRoleRequest`

```json
{
  "role": "proj_admin"
}
```

- **Response:** `OrgMemberResponse` (200 OK)

---

### 10. Create Team
Create a new team within the organization.

- **URL:** `/{org_id}/teams`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_TEAMS`)
- **Request Body:** `CreateTeamRequest`

```json
{
  "name": "Frontend Team",
  "description": "Responsible for UI/UX"
}
```

- **Response:** `TeamResponse` (201 Created)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Frontend Team",
  "description": "Responsible for UI/UX",
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### 11. List Teams
List all teams in an organization.

- **URL:** `/{org_id}/teams`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[TeamResponse]` (200 OK)

---

### 12. Add Team Member
Add a user to a team.

- **URL:** `/{org_id}/teams/{team_id}/members`
- **Method:** `POST`
- **Auth Required:** Yes (Permission: `MANAGE_TEAMS`)
- **Request Body:** `AddTeamMemberRequest`

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

- **Response:** `TeamMemberResponse` (201 Created)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "team_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### 13. List Team Members
List all members of a team.

- **URL:** `/{org_id}/teams/{team_id}/members`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `list[TeamMemberResponse]` (200 OK)

---

### 14. Remove Team Member
Remove a user from a team.

- **URL:** `/{org_id}/teams/{team_id}/members/{user_id}`
- **Method:** `DELETE`
- **Auth Required:** Yes (Permission: `MANAGE_TEAMS`)
- **Response:** 204 No Content

## Data Models

### Request Models

**CreateOrgRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Min 1, max 255 chars. |
| slug | string | Yes | Lowercase alphanumeric and hyphens. |

**UpdateOrgRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | No | Max 255 chars. |

**AddMemberRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| user_id | UUID | No | Existing user ID. |
| email | string | No | Email to invite. |
| role | string | No | default: "member". Allowed: org_admin, proj_admin, member. |

**ChangeMemberRoleRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| role | string | Yes | Allowed: org_admin, proj_admin, member. |

**CreateTeamRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Min 1, max 255 chars. |
| description | string | No | Max 500 chars. |

**AddTeamMemberRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| user_id | UUID | Yes | User to add. |

### Response Models

**OrgResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Organization ID. |
| name | string | Organization name. |
| slug | string | URL-friendly slug. |
| created_at | datetime | Creation timestamp. |

**OrgMemberResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Membership ID. |
| org_id | UUID | Organization ID. |
| user_id | UUID | User ID. |
| role | string | Role name. |
| created_at | datetime | Creation timestamp. |
| email | string | User email. |
| full_name | string | User full name. |

**UserMembershipResponse**
| Field | Type | Description |
|---|---|---|
| org_id | UUID | Organization ID. |
| org_name | string | Organization name. |
| role | string | Role name. |

**TeamResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Team ID. |
| org_id | UUID | Organization ID. |
| name | string | Team name. |
| description | string | Description. |
| created_at | datetime | Creation timestamp. |

**TeamMemberResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Team membership ID. |
| team_id | UUID | Team ID. |
| user_id | UUID | User ID. |
| created_at | datetime | Creation timestamp. |
