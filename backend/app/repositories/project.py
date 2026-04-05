"""
Repository for Project model.
Handles data access operations for projects.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc

from app.repositories.base import BaseRepository
from app.models.project import Project, ProjectStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project CRUD operations."""

    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False
    ) -> List[Project]:
        """
        Get all projects for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            include_archived: Whether to include archived projects

        Returns:
            List of projects
        """
        query = self.db.query(Project).filter(Project.user_id == user_id)

        if not include_archived:
            query = query.filter(Project.is_archived == False)

        return query.order_by(desc(Project.updated_at)).offset(skip).limit(limit).all()

    def get_by_user_and_status(
        self,
        user_id: int,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        Get projects by user and status.

        Args:
            user_id: User ID
            status: Project status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of projects
        """
        return (
            self.db.query(Project)
            .filter(
                and_(
                    Project.user_id == user_id,
                    Project.status == status,
                    Project.is_archived == False
                )
            )
            .order_by(desc(Project.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_scenes(self, project_id: int) -> Optional[Project]:
        """
        Get project with all scenes eagerly loaded.

        Args:
            project_id: Project ID

        Returns:
            Project with scenes or None
        """
        return (
            self.db.query(Project)
            .options(joinedload(Project.scenes))
            .filter(Project.id == project_id)
            .first()
        )

    def get_with_full_details(self, project_id: int) -> Optional[Project]:
        """
        Get project with all related data (scenes, characters).

        Args:
            project_id: Project ID

        Returns:
            Project with full details or None
        """
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.scenes),
                joinedload(Project.characters)
            )
            .filter(Project.id == project_id)
            .first()
        )

    def search(
        self,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        Search projects by title or description.

        Args:
            user_id: User ID
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching projects
        """
        search_pattern = f"%{query}%"
        return (
            self.db.query(Project)
            .filter(
                and_(
                    Project.user_id == user_id,
                    or_(
                        Project.title.ilike(search_pattern),
                        Project.description.ilike(search_pattern)
                    ),
                    Project.is_archived == False
                )
            )
            .order_by(desc(Project.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_public_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        Get public projects (for discovery/gallery).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of public projects
        """
        return (
            self.db.query(Project)
            .filter(
                and_(
                    Project.is_public == True,
                    Project.status == ProjectStatus.COMPLETED,
                    Project.is_archived == False
                )
            )
            .order_by(desc(Project.views_count), desc(Project.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(self, project_id: int, status: ProjectStatus) -> Optional[Project]:
        """
        Update project status.

        Args:
            project_id: Project ID
            status: New status

        Returns:
            Updated project or None
        """
        project = self.get(project_id)
        if project:
            project.update_status(status)
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Updated project {project_id} status to {status}")
        return project

    def archive(self, project_id: int) -> Optional[Project]:
        """
        Archive a project.

        Args:
            project_id: Project ID

        Returns:
            Archived project or None
        """
        project = self.get(project_id)
        if project:
            project.is_archived = True
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Archived project {project_id}")
        return project

    def set_public(self, project_id: int, is_public: bool) -> Optional[Project]:
        """
        Set project visibility.

        Args:
            project_id: Project ID
            is_public: Public visibility flag

        Returns:
            Updated project or None
        """
        project = self.get(project_id)
        if project:
            project.is_public = is_public
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Set project {project_id} public={is_public}")
        return project

    def increment_views(self, project_id: int) -> Optional[Project]:
        """
        Increment project view count.

        Args:
            project_id: Project ID

        Returns:
            Updated project or None
        """
        project = self.get(project_id)
        if project:
            project.views_count += 1
            self.db.commit()
            self.db.refresh(project)
        return project

    def get_user_project_count(self, user_id: int, status: Optional[ProjectStatus] = None) -> int:
        """
        Get count of user's projects.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Project count
        """
        query = self.db.query(Project).filter(
            and_(
                Project.user_id == user_id,
                Project.is_archived == False
            )
        )

        if status:
            query = query.filter(Project.status == status)

        return query.count()
