import requests
import time
import sys

BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/v1/auth"
ORG_URL = f"{BASE_URL}/api/v1/organizations"
PROJECT_URL = f"{BASE_URL}/api/v1/projects"

def register_user():
    email = f"user_{int(time.time())}@example.com"
    password = "password123"
    full_name = "Test User"
    
    print(f"Registering user {email}...")
    resp = requests.post(f"{AUTH_URL}/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
        "org_name": f"Org {int(time.time())}"
    })
    
    if resp.status_code != 201:
        print(f"Registration failed: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    print("Registration successful.")
    # Check permissions in AuthResponse if present (it might not be on register, but on login)
    # Actually register returns AuthResponse too.
    if "permissions" in data:
        print(f"Permissions in Register Response: {data['permissions']}")
    else:
        print("Permissions NOT found in Register Response.")
        
    return email, password, data["access_token"], data["user"]["id"]

def login_user(email, password):
    print(f"Logging in user {email}...")
    resp = requests.post(f"{AUTH_URL}/login", json={
        "email": email,
        "password": password
    })
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    print("Login successful.")
    
    if "permissions" in data:
        print(f"Permissions in Login Response: {data['permissions']}")
    else:
        print("Permissions NOT found in Login Response.")
        
    return data["access_token"]

def get_me(token):
    print("Fetching /me...")
    resp = requests.get(f"{AUTH_URL}/me", headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code != 200:
        print(f"Get Me failed: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    if "permissions" in data:
        print(f"Permissions in Me Response: {data['permissions']}")
    else:
        print("Permissions NOT found in Me Response.")

def create_project(token, org_id):
    print("Creating project...")
    # Need org_id from token or /me? 
    # Actually create project needs permission MANAGE_PROJECTS.
    # We are org admin, so we should have it.
    
    resp = requests.post(f"{PROJECT_URL}/", json={
        "name": "Test Project",
        "description": "Test"
    }, headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code != 201:
        print(f"Create Project failed: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    print(f"Project created: {data['id']}")
    return data["id"]

def check_membership(token, project_id, user_id):
    print(f"Checking membership for project {project_id}...")
    # Internal endpoint, but we can try to call it via gateway if exposed?
    # Or we can just use the internal URL if we are running inside docker network, but we are outside.
    # Wait, check-membership is an internal endpoint, it might not be exposed on the gateway.
    # Let's check docker-compose.yml or api_gateway to see if it is exposed.
    # If not, we can simulate it by calling 'get project' or something?
    # But the user specifically asked for 'check-membership' response to include permissions.
    # If it is internal only, the frontend can't use it directly.
    # Ah, the plan said "Update project_service (ProjectResponse / membership check)".
    # If the frontend uses it, it MUST be exposed. 
    # Let's try to call it.
    
    resp = requests.get(f"{PROJECT_URL}/{project_id}/check-membership", params={"user_id": user_id}, headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code != 200:
        print(f"Check Membership failed (might be internal only): {resp.status_code} {resp.text}")
        return

    data = resp.json()
    if "permissions" in data:
        print(f"Permissions in Check Membership Response: {data['permissions']}")
    else:
        print("Permissions NOT found in Check Membership Response.")

def main():
    email, password, token, user_id = register_user()
    token = login_user(email, password)
    get_me(token)
    
    # We need to find org_id to create project?
    # Not strictly needed if `create_project` endpoint gets it from token.
    # But we need to verify Project permissions.
    project_id = create_project(token, None)
    
    check_membership(token, project_id, user_id)

if __name__ == "__main__":
    main()
