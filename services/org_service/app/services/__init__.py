"""Organization Service - Business Logic."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.events import TOPICS, ORG_CREATED, ORG_MEMBER_ADDED, ORG_MEMBER_REMOVED, ORG_MEMBER_ROLE_CHANGED
from shared.events.producer import event_producer

from app.models import Organization, OrgMembership, Team, TeamMembership
from app.schemas import (
    AddMemberRequest, AddTeamMemberRequest, ChangeMemberRoleRequest,
    CreateOrgRequest, CreateTeamRequest, OrgMemberResponse, OrgResponse,
    TeamMemberResponse, TeamResponse, UpdateOrgRequest, UserMembershipResponse,
)
from app.config import get_settings
import httpx


class OrgService:
    """Organization business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Organizations ----

    async def create_org(self, data: CreateOrgRequest, creator_id: str) -> OrgResponse:
        # Check slug uniqueness
        existing = await self.db.execute(select(Organization).where(Organization.slug == data.slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "Organization slug already taken")

        org = Organization(name=data.name, slug=data.slug)
        self.db.add(org)
        await self.db.flush()

        # Auto-add creator as org_admin
        membership = OrgMembership(org_id=org.id, user_id=uuid.UUID(creator_id), role="org_admin")
        self.db.add(membership)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["organizations"],
            {"event_type": ORG_CREATED, "org_id": str(org.id), "name": org.name, "creator_id": creator_id},
            key=str(org.id),
        )

        return OrgResponse.model_validate(org)

    async def get_org(self, org_id: uuid.UUID) -> OrgResponse:
        stmt = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
        return OrgResponse.model_validate(org)

    async def update_org(self, org_id: uuid.UUID, data: UpdateOrgRequest) -> OrgResponse:
        stmt = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")

        if data.name is not None:
            org.name = data.name
        await self.db.flush()

        return OrgResponse.model_validate(org)

    async def list_user_orgs(self, user_id: str) -> list[OrgResponse]:
        stmt = (
            select(Organization)
            .join(OrgMembership, OrgMembership.org_id == Organization.id)
            .where(OrgMembership.user_id == uuid.UUID(user_id))
        )
        result = await self.db.execute(stmt)
        return [OrgResponse.model_validate(o) for o in result.scalars().all()]

    async def list_user_memberships(self, user_id: str) -> list[UserMembershipResponse]:
        """List all organization memberships for a user, including role and org details."""
        stmt = (
            select(OrgMembership, Organization)
            .join(Organization, Organization.id == OrgMembership.org_id)
            .where(OrgMembership.user_id == uuid.UUID(user_id))
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        return [
            UserMembershipResponse(
                org_id=membership.org_id,
                org_name=org.name,
                role=membership.role
            )
            for membership, org in rows
        ]

    # ---- Members ----

    async def add_member(self, org_id: uuid.UUID, data: AddMemberRequest) -> OrgMemberResponse:
        user_id = data.user_id

        if not user_id:
            if not data.email:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Either user_id or email must be provided")

            # Resolve email to user_id via Auth Service
            settings = get_settings()
            try:
                async with httpx.AsyncClient() as client:
                    # auth_service_url does not include /auth prefix in config default, 
                    # but router prefix is /auth.
                    # We need to construct: http://auth_service:8001/auth/users/by-email/{email}
                    url = f"{settings.auth_service_url}/auth/users/by-email/{data.email}"
                    resp = await client.get(url)
                    
                    if resp.status_code == 200:
                        user_data = resp.json()
                        user_id = uuid.UUID(user_data["id"])
                    elif resp.status_code == 404:
                         raise HTTPException(status.HTTP_404_NOT_FOUND, f"User with email {data.email} not found")
                    else:
                        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Auth service returned {resp.status_code}")
            except httpx.RequestError as e:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Failed to reach Auth Service: {e}")

        existing = await self.db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id,
                OrgMembership.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already a member")

        membership = OrgMembership(org_id=org_id, user_id=user_id, role=data.role)
        self.db.add(membership)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["organizations"],
            {"event_type": ORG_MEMBER_ADDED, "org_id": str(org_id), "user_id": str(user_id), "role": data.role},
            key=str(org_id),
        )

        return OrgMemberResponse.model_validate(membership)

    async def remove_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = delete(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        await event_producer.publish(
            TOPICS["organizations"],
            {"event_type": ORG_MEMBER_REMOVED, "org_id": str(org_id), "user_id": str(user_id)},
            key=str(org_id),
        )

    async def change_member_role(
        self, org_id: uuid.UUID, user_id: uuid.UUID, data: ChangeMemberRoleRequest
    ) -> OrgMemberResponse:
        stmt = select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        old_role = membership.role
        membership.role = data.role
        await self.db.flush()

        await event_producer.publish(
            TOPICS["organizations"],
            {
                "event_type": ORG_MEMBER_ROLE_CHANGED,
                "org_id": str(org_id), "user_id": str(user_id),
                "old_role": old_role, "new_role": data.role,
            },
            key=str(org_id),
        )

        return OrgMemberResponse.model_validate(membership)

    async def list_members(self, org_id: uuid.UUID) -> list[OrgMemberResponse]:
        stmt = select(OrgMembership).where(OrgMembership.org_id == org_id)
        result = await self.db.execute(stmt)
        return [OrgMemberResponse.model_validate(m) for m in result.scalars().all()]

    async def get_membership(self, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMemberResponse | None:
        stmt = select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        m = result.scalar_one_or_none()
        return OrgMemberResponse.model_validate(m) if m else None

    # ---- Teams ----

    async def create_team(self, org_id: uuid.UUID, data: CreateTeamRequest) -> TeamResponse:
        team = Team(org_id=org_id, name=data.name, description=data.description)
        self.db.add(team)
        await self.db.flush()
        return TeamResponse.model_validate(team)

    async def list_teams(self, org_id: uuid.UUID) -> list[TeamResponse]:
        stmt = select(Team).where(Team.org_id == org_id)
        result = await self.db.execute(stmt)
        return [TeamResponse.model_validate(t) for t in result.scalars().all()]

    async def add_team_member(self, team_id: uuid.UUID, data: AddTeamMemberRequest) -> TeamMemberResponse:
        existing = await self.db.execute(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == data.user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already in team")

        tm = TeamMembership(team_id=team_id, user_id=data.user_id)
        self.db.add(tm)
        await self.db.flush()
        return TeamMemberResponse.model_validate(tm)

    async def list_team_members(self, team_id: uuid.UUID) -> list[TeamMemberResponse]:
        stmt = select(TeamMembership).where(TeamMembership.team_id == team_id)
        result = await self.db.execute(stmt)
        return [TeamMemberResponse.model_validate(tm) for tm in result.scalars().all()]

    async def remove_team_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = delete(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Team member not found")
