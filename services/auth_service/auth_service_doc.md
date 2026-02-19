# Auth Service API Documentation

Base URL: `/auth`

## Architecture Notes

> [!IMPORTANT]
> **Identity-Only JWT**: Access tokens contain only identity claims (`user_id`, `email`, `org_id`). Organization roles are **not** stored in the JWT — they are resolved at request time by each service using a Redis-cached `PermissionResolver`. This ensures role changes take effect immediately without requiring re-authentication.

> [!NOTE]
> **Organization Switching**: Users belonging to multiple organizations can switch their active org context via `POST /auth/switch-org` without re-authentication. This issues a new token pair with the target `org_id`.

## Endpoints

### 1. Register User
Register a new user account. Optionally creates an organization if `org_name` is provided.

- **URL:** `/register`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body:** `RegisterRequest`

```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "org_name": "My Corp" // Optional
}
```

- **Response:** `AuthResponse` (201 Created)

```json
{
  "access_token": "eyJhbGciOiJIUz...",
  "refresh_token": "def50200...",
  "token_type": "bearer",
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2023-10-27T10:00:00Z",
    "permissions": ["manage_org_members", "create_project"]
  },
  "permissions": ["manage_org_members", "create_project"]
}
```

---

### 2. Login
Authenticate with email and password to receive access tokens.

- **URL:** `/login`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body:** `LoginRequest`

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

- **Response:** `AuthResponse` (200 OK)

---

### 3. Refresh Token
Refresh an access token using a valid refresh token.

- **URL:** `/refresh`
- **Method:** `POST`
- **Auth Required:** No (Token signature verified)
- **Request Body:** `RefreshRequest`

```json
{
  "refresh_token": "def50200..."
}
```

- **Response:** `TokenResponse` (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUz...",
  "token_type": "bearer"
}
```

---

### 4. Logout
Logout by blacklisting the refresh token.

- **URL:** `/logout`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:** `RefreshRequest`

```json
{
  "refresh_token": "def50200..."
}
```

- **Response:** `MessageResponse` (200 OK)

```json
{
  "message": "Successfully logged out"
}
```

---

### 5. Switch Organization
Switch the active organization context. Verifies the user is a member of the target organization and issues new tokens.

- **URL:** `/switch-org`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body:** `SwitchOrgRequest`

```json
{
  "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

- **Response:** `AuthResponse` (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUz...",
  "refresh_token": "def50200...",
  "token_type": "bearer",
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2023-10-27T10:00:00Z",
    "permissions": ["manage_org_members", "create_project"]
  },
  "permissions": ["manage_org_members", "create_project"]
}
```

- **Errors:**
  - 403 Forbidden: User is not a member of the target organization.
  - 502 Bad Gateway: Failed to verify organization membership.
  - 503 Service Unavailable: Organization service is unreachable.

---

### 6. Get Current User
Get the current user's profile information.

- **URL:** `/me`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `UserResponse` (200 OK)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2023-10-27T10:00:00Z",
  "permissions": ["manage_org_members", "create_project"]
}
```

---

### 7. Get User by Email
Get a user's details by their email address. Primarily for internal service use or admin actions.

- **URL:** `/users/by-email/{email}`
- **Method:** `GET`
- **Auth Required:** Yes
- **Response:** `UserResponse` (200 OK)
- **Errors:**
  - 404 Not Found: If user does not exist.

---

### 8. Change Password
Change the current user's password.

- **URL:** `/password`
- **Method:** `PUT`
- **Auth Required:** Yes
- **Request Body:** `ChangePasswordRequest`

```json
{
  "current_password": "oldpassword123",
  "new_password": "newsecurepassword456"
}
```

- **Response:** `MessageResponse` (200 OK)

```json
{
  "message": "Password changed successfully"
}
```

## Data Models

### Request Models

**RegisterRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| email | string (email) | Yes | User email address. |
| password | string | Yes | Min 8, max 128 chars. |
| full_name | string | Yes | Unix 1, max 255 chars. |
| org_name | string | No | If provided, creates a new org and assigns user as OrgAdmin. |

**LoginRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| email | string (email) | Yes | |
| password | string | Yes | |

**RefreshRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| refresh_token | string | Yes | Valid refresh token. |

**SwitchOrgRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| org_id | UUID | Yes | Target organization ID to switch to. |

**ChangePasswordRequest**
| Field | Type | Required | Description |
|---|---|---|---|
| current_password | string | Yes | |
| new_password | string | Yes | Min 8, max 128 chars. |

### Response Models

**UserResponse**
| Field | Type | Description |
|---|---|---|
| id | UUID | Unique user ID. |
| email | string | User email. |
| full_name | string | User full name. |
| is_active | boolean | Whether the account is active. |
| created_at | datetime | Timestamp of creation. |
| permissions | list[string] | List of organization permissions. |

**AuthResponse**
| Field | Type | Description |
|---|---|---|
| access_token | string | JWT access token. |
| refresh_token | string | Refresh token. |
| token_type | string | Token type (default "bearer"). |
| user | UserResponse | User profile details. |
| permissions | list[string] | List of organization permissions. |

**TokenResponse**
| Field | Type | Description |
|---|---|---|
| access_token | string | New JWT access token. |
| token_type | string | Token type (default "bearer"). |

**MessageResponse**
| Field | Type | Description |
|---|---|---|
| message | string | Status message. |
