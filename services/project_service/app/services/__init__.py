"""Project Service - Business Logic."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.events import TOPICS, PROJECT_CREATED, PROJECT_UPDATED, PROJECT_DELETED, PROJECT_MEMBER_ADDED, PROJECT_MEMBER_REMOVED, PROJECT_MEMBER_ROLE_CHANGED
from shared.events.producer import event_producer

from app.models import CustomStatus, Project, ProjectMembership
from app.schemas import (
    AddProjectMemberRequest, ChangeProjectRoleRequest, CreateFromTemplateRequest,
    CreateProjectRequest, CreateStatusRequest, CustomStatusResponse,
    ProjectMemberResponse, ProjectResponse, UpdateProjectRequest, UpdateStatusRequest,
)


DEFAULT_STATUSES = [
    {"name": "To Do", "position": 0, "color": "#6B7280"},
    {"name": "In Progress", "position": 1, "color": "#3B82F6"},
    {"name": "In Review", "position": 2, "color": "#F59E0B"},
    {"name": "Done", "position": 3, "color": "#10B981"},
]


class ProjectService:
    """Project business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Projects ----

    async def create_project(
        self, org_id: str, owner_id: str, data: CreateProjectRequest
    ) -> ProjectResponse:
        project = Project(
            org_id=uuid.UUID(org_id),
            owner_id=uuid.UUID(owner_id),
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        self.db.add(project)
        await self.db.flush()

        # Auto-add owner as project owner
        membership = ProjectMembership(
            project_id=project.id, user_id=uuid.UUID(owner_id), role="owner"
        )
        self.db.add(membership)

        # Create default statuses
        for s in DEFAULT_STATUSES:
            cs = CustomStatus(
                project_id=project.id,
                name=s["name"],
                position=s["position"],
                color=s["color"],
                is_default=True,
            )
            self.db.add(cs)

        await self.db.flush()

        await event_producer.publish(
            TOPICS["projects"],
            {
                "event_type": PROJECT_CREATED,
                "project_id": str(project.id),
                "org_id": org_id,
                "owner_id": owner_id,
                "name": project.name,
            },
            key=str(project.id),
        )

        return ProjectResponse.model_validate(project)

    async def get_project(self, project_id: uuid.UUID, org_id: str) -> ProjectResponse:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.org_id == uuid.UUID(org_id),
        )
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        return ProjectResponse.model_validate(project)

    async def list_projects(self, org_id: str) -> list[ProjectResponse]:
        stmt = select(Project).where(
            Project.org_id == uuid.UUID(org_id),
            Project.is_template == False,
        ).order_by(Project.created_at.desc())
        result = await self.db.execute(stmt)
        return [ProjectResponse.model_validate(p) for p in result.scalars().all()]

    async def list_user_projects(self, org_id: str, user_id: str) -> list[ProjectResponse]:
        stmt = (
            select(Project)
            .join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(
                Project.org_id == uuid.UUID(org_id),
                ProjectMembership.user_id == uuid.UUID(user_id),
                Project.is_template == False,
            )
            .order_by(Project.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [ProjectResponse.model_validate(p) for p in result.scalars().all()]

    async def update_project(
        self, project_id: uuid.UUID, org_id: str, data: UpdateProjectRequest
    ) -> ProjectResponse:
        stmt = select(Project).where(Project.id == project_id, Project.org_id == uuid.UUID(org_id))
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["projects"],
            {"event_type": PROJECT_UPDATED, "project_id": str(project_id), "org_id": org_id},
            key=str(project_id),
        )

        return ProjectResponse.model_validate(project)

    async def delete_project(self, project_id: uuid.UUID, org_id: str) -> None:
        stmt = select(Project).where(Project.id == project_id, Project.org_id == uuid.UUID(org_id))
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

        await self.db.delete(project)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["projects"],
            {"event_type": PROJECT_DELETED, "project_id": str(project_id), "org_id": org_id},
            key=str(project_id),
        )

    # ---- Templates ----

    async def create_template(
        self, org_id: str, owner_id: str, data: CreateProjectRequest
    ) -> ProjectResponse:
        project = Project(
            org_id=uuid.UUID(org_id),
            owner_id=uuid.UUID(owner_id),
            name=data.name,
            description=data.description,
            is_template=True,
        )
        self.db.add(project)
        await self.db.flush()
        return ProjectResponse.model_validate(project)

    async def list_templates(self, org_id: str) -> list[ProjectResponse]:
        stmt = select(Project).where(
            Project.org_id == uuid.UUID(org_id),
            Project.is_template == True,
        )
        result = await self.db.execute(stmt)
        return [ProjectResponse.model_validate(p) for p in result.scalars().all()]

    async def create_from_template(
        self, template_id: uuid.UUID, org_id: str, owner_id: str, data: CreateFromTemplateRequest
    ) -> ProjectResponse:
        template = await self.db.execute(
            select(Project).where(Project.id == template_id, Project.is_template == True)
        )
        template_project = template.scalar_one_or_none()
        if not template_project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

        new_project = Project(
            org_id=uuid.UUID(org_id),
            owner_id=uuid.UUID(owner_id),
            name=data.name,
            description=data.description or template_project.description,
            start_date=data.start_date,
            end_date=data.end_date,
            template_source_id=template_id,
        )
        self.db.add(new_project)
        await self.db.flush()

        # Copy statuses from template
        tmpl_statuses = await self.db.execute(
            select(CustomStatus).where(CustomStatus.project_id == template_id).order_by(CustomStatus.position)
        )
        for s in tmpl_statuses.scalars().all():
            cs = CustomStatus(
                project_id=new_project.id,
                name=s.name,
                position=s.position,
                color=s.color,
            )
            self.db.add(cs)

        # Owner membership
        self.db.add(ProjectMembership(
            project_id=new_project.id, user_id=uuid.UUID(owner_id), role="owner"
        ))
        await self.db.flush()

        return ProjectResponse.model_validate(new_project)

    # ---- Members ----

    async def add_member(
        self, project_id: uuid.UUID, data: AddProjectMemberRequest
    ) -> ProjectMemberResponse:
        existing = await self.db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == data.user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already a member")

        membership = ProjectMembership(
            project_id=project_id, user_id=data.user_id, role=data.role
        )
        self.db.add(membership)
        await self.db.flush()

        await event_producer.publish(
            TOPICS["projects"],
            {
                "event_type": PROJECT_MEMBER_ADDED,
                "project_id": str(project_id),
                "user_id": str(data.user_id),
                "role": data.role,
            },
            key=str(project_id),
        )

        return ProjectMemberResponse.model_validate(membership)

    async def remove_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        stmt = delete(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        await event_producer.publish(
            TOPICS["projects"],
            {"event_type": PROJECT_MEMBER_REMOVED, "project_id": str(project_id), "user_id": str(user_id)},
            key=str(project_id),
        )

    async def change_member_role(
        self, project_id: uuid.UUID, user_id: uuid.UUID, data: ChangeProjectRoleRequest
    ) -> ProjectMemberResponse:
        stmt = select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        if not membership:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        membership.role = data.role
        await self.db.flush()

        await event_producer.publish(
            TOPICS["projects"],
            {
                "event_type": PROJECT_MEMBER_ROLE_CHANGED,
                "project_id": str(project_id),
                "user_id": str(user_id),
                "new_role": data.role,
            },
            key=str(project_id),
        )

        return ProjectMemberResponse.model_validate(membership)

    async def _enrich_members(self, members: list[ProjectMemberResponse]) -> list[ProjectMemberResponse]:
        """Fetch user details from Auth Service and populate members."""
        if not members:
            return members

        user_ids = [m.user_id for m in members]
        
        # Need to import get_settings inside method to avoid circular imports or context issues
        from app.config import get_settings
        import httpx
        settings = get_settings()
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.auth_service_url}/auth/users/batch"
                resp = await client.post(url, json={"user_ids": [str(uid) for uid in user_ids]})
                
                if resp.status_code == 200:
                    users_data = resp.json()
                    user_map = {u["id"]: u for u in users_data}
                    
                    for member in members:
                        user = user_map.get(str(member.user_id))
                        if user:
                            member.email = user["email"]
                            member.full_name = user["full_name"]
        except Exception as e:
            print(f"Failed to enrich project members: {e}")
            pass
            
        return members

    async def list_members(self, project_id: uuid.UUID) -> list[ProjectMemberResponse]:
        stmt = select(ProjectMembership).where(ProjectMembership.project_id == project_id)
        result = await self.db.execute(stmt)
        members = [ProjectMemberResponse.model_validate(m) for m in result.scalars().all()]
        return await self._enrich_members(members)

    async def get_membership(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[dict]:
        stmt = select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership:
            return {"role": membership.role, "user_id": str(membership.user_id)}
        return None

    # ---- Custom Statuses ----

    async def create_status(
        self, project_id: uuid.UUID, data: CreateStatusRequest
    ) -> CustomStatusResponse:
        cs = CustomStatus(
            project_id=project_id,
            name=data.name,
            position=data.position,
            color=data.color,
        )
        self.db.add(cs)
        await self.db.flush()
        return CustomStatusResponse.model_validate(cs)

    async def list_statuses(self, project_id: uuid.UUID) -> list[CustomStatusResponse]:
        stmt = (
            select(CustomStatus)
            .where(CustomStatus.project_id == project_id)
            .order_by(CustomStatus.position)
        )
        result = await self.db.execute(stmt)
        return [CustomStatusResponse.model_validate(s) for s in result.scalars().all()]

    async def update_status(
        self, status_id: uuid.UUID, data: UpdateStatusRequest
    ) -> CustomStatusResponse:
        stmt = select(CustomStatus).where(CustomStatus.id == status_id)
        result = await self.db.execute(stmt)
        cs = result.scalar_one_or_none()
        if not cs:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Status not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cs, field, value)
        await self.db.flush()

        return CustomStatusResponse.model_validate(cs)

    async def delete_status(self, status_id: uuid.UUID) -> None:
        stmt = select(CustomStatus).where(CustomStatus.id == status_id)
        result = await self.db.execute(stmt)
        cs = result.scalar_one_or_none()
        if not cs:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Status not found")
        await self.db.delete(cs)
        await self.db.flush()
