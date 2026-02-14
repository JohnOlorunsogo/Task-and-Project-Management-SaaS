import asyncio
import uuid
import httpx

# Configuration
API_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = f"admin_{uuid.uuid4().hex[:8]}@example.com"
ADMIN_PASSWORD = "password123"
MEMBER_EMAIL = f"member_{uuid.uuid4().hex[:8]}@example.com"
MEMBER_PASSWORD = "password123"

async def main():
    async with httpx.AsyncClient() as client:
        print(f"--- Starting Verification: Email-Based Member Addition ---")

        # 1. Register Admin User
        print(f"\n1. Registering Admin: {ADMIN_EMAIL}")
        resp = await client.post(f"{API_URL}/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "full_name": "Admin User",
            "org_name": "Test Org"
        })
        if resp.status_code != 201:
            print(f"FAILED to register admin: {resp.text}")
            return
        admin_data = resp.json()
        admin_token = admin_data["access_token"]
        print("   Admin registered successfully.")

        # 2. Get Admin's Org
        print("\n2. Fetching Admin's Organization...")
        resp = await client.get(f"{API_URL}/organizations/me", headers={"Authorization": f"Bearer {admin_token}"})
        if resp.status_code != 200:
            print(f"FAILED to get orgs: {resp.text}")
            return
        orgs = resp.json()
        if not orgs:
            print("FAILED: No org found for admin.")
            return
        org_id = orgs[0]["id"]
        print(f"   Found Org ID: {org_id}")

        # 3. Register Member User (No Org)
        print(f"\n3. Registering Member User: {MEMBER_EMAIL}")
        resp = await client.post(f"{API_URL}/auth/register", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD,
            "full_name": "Member User"
        })
        if resp.status_code != 201:
            print(f"FAILED to register member: {resp.text}")
            return
        print("   Member registered successfully.")

        # 4. Add Member to Org using EMAIL ONLY
        print(f"\n4. Admin adding Member to Org using EMAIL: {MEMBER_EMAIL}")
        # Note: We are NOT sending user_id, only email
        resp = await client.post(
            f"{API_URL}/organizations/{org_id}/members",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": MEMBER_EMAIL,
                "role": "member"
            }
        )
        
        if resp.status_code == 201:
            print("   SUCCESS! Member added via email.")
            data = resp.json()
            print(f"   Membership ID: {data['id']}")
            print(f"   User ID Resolved: {data['user_id']}")
        elif resp.status_code == 409:
             print("   User already member (unexpected for new org)")
        else:
            print(f"   FAILED. Status: {resp.status_code}")
            print(f"   Response: {resp.text}")
            if resp.status_code == 422:
                print("   (422 often means validation error - check if 'email' field is accepted)")

        print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
