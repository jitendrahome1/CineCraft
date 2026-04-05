"""
Project service for business logic.
Handles project management operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.project import ProjectRepository
from app.repositories.scene import SceneRepository
from app.repositories.character import CharacterRepository
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.core.errors import (
    ProjectNotFoundError,
    AuthorizationError,
    ValidationError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Service for project management."""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)
        self.character_repo = CharacterRepository(db)

    def create_project(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        story_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: Optional[str] = "english",
        video_length: Optional[str] = "short"
    ) -> Project:
        """
        Create a new project.

        Args:
            user_id: User ID
            title: Project title
            description: Optional description
            story_prompt: Optional story prompt
            metadata: Optional metadata
            language: Language for generation ('english' or 'hindi')
            video_length: Video length ('short' or 'long')

        Returns:
            Created project

        Raises:
            ValidationError: If validation fails
        """
        if not title or len(title.strip()) == 0:
            raise ValidationError("Project title cannot be empty")

        project_data = {
            "user_id": user_id,
            "title": title.strip(),
            "description": description,
            "story_prompt": story_prompt,
            "status": ProjectStatus.DRAFT,
            "metadata": metadata or {},
            "language": language or "english",
            "video_length": video_length or "short"
        }

        project = self.project_repo.create(project_data)
        logger.info(f"Created project {project.id} for user {user_id}")
        return project

    def get_project(self, project_id: int, user_id: Optional[int] = None) -> Project:
        """
        Get a project by ID.

        Args:
            project_id: Project ID
            user_id: Optional user ID for permission check

        Returns:
            Project

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        project = self.project_repo.get(project_id)

        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        # Check permissions if user_id provided
        if user_id is not None and project.user_id != user_id and not project.is_public:
            raise AuthorizationError("You don't have permission to access this project")

        return project

    def get_project_with_details(
        self,
        project_id: int,
        user_id: Optional[int] = None
    ) -> Project:
        """
        Get project with all related data.

        Args:
            project_id: Project ID
            user_id: Optional user ID for permission check

        Returns:
            Project with scenes and characters

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        project = self.project_repo.get_with_full_details(project_id)

        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        if user_id is not None and project.user_id != user_id and not project.is_public:
            raise AuthorizationError("You don't have permission to access this project")

        return project

    def list_user_projects(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProjectStatus] = None,
        include_archived: bool = False
    ) -> List[Project]:
        """
        List user's projects.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            status: Optional status filter
            include_archived: Include archived projects

        Returns:
            List of projects
        """
        if status:
            return self.project_repo.get_by_user_and_status(
                user_id, status, skip, limit
            )
        return self.project_repo.get_by_user(user_id, skip, limit, include_archived)

    def search_projects(
        self,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        Search user's projects.

        Args:
            user_id: User ID
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching projects
        """
        return self.project_repo.search(user_id, query, skip, limit)

    def update_project(
        self,
        project_id: int,
        user_id: int,
        **update_data
    ) -> Project:
        """
        Update a project.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            **update_data: Fields to update

        Returns:
            Updated project

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        project = self.get_project(project_id, user_id)

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to update this project")

        # Filter allowed fields
        allowed_fields = [
            'title', 'description', 'story_prompt', 'metadata',
            'video_duration', 'is_public'
        ]
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        updated_project = self.project_repo.update(project, filtered_data)
        logger.info(f"Updated project {project_id}")
        return updated_project

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            True if deleted

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        project = self.get_project(project_id, user_id)

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to delete this project")

        self.project_repo.delete(project_id)
        logger.info(f"Deleted project {project_id}")
        return True

    def archive_project(self, project_id: int, user_id: int) -> Project:
        """
        Archive a project.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            Archived project

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        project = self.get_project(project_id, user_id)

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to archive this project")

        archived_project = self.project_repo.archive(project_id)
        logger.info(f"Archived project {project_id}")
        return archived_project

    def set_project_visibility(
        self,
        project_id: int,
        user_id: int,
        is_public: bool
    ) -> Project:
        """
        Set project visibility.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            is_public: Public visibility flag

        Returns:
            Updated project

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        project = self.get_project(project_id, user_id)

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to modify this project")

        updated_project = self.project_repo.set_public(project_id, is_public)
        logger.info(f"Set project {project_id} visibility to public={is_public}")
        return updated_project

    def update_project_status(
        self,
        project_id: int,
        status: ProjectStatus,
        user_id: Optional[int] = None
    ) -> Project:
        """
        Update project status.

        Args:
            project_id: Project ID
            status: New status
            user_id: Optional user ID for permission check

        Returns:
            Updated project

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        if user_id:
            project = self.get_project(project_id, user_id)
            if project.user_id != user_id:
                raise AuthorizationError("You don't have permission to update this project")

        updated_project = self.project_repo.update_status(project_id, status)
        return updated_project

    def get_project_stats(self, project_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get project statistics.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            Project statistics

        Raises:
            ProjectNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        project = self.get_project_with_details(project_id, user_id)

        scene_count = len(project.scenes)
        complete_scenes = sum(1 for scene in project.scenes if scene.is_complete)
        character_count = len(project.characters)

        return {
            "project_id": project_id,
            "status": project.status,
            "scene_count": scene_count,
            "complete_scenes": complete_scenes,
            "character_count": character_count,
            "has_story": project.story is not None,
            "has_video": project.video_url is not None,
            "views_count": project.views_count,
            "is_public": project.is_public
        }

    def increment_project_views(self, project_id: int) -> Project:
        """
        Increment project view count (for public projects).

        Args:
            project_id: Project ID

        Returns:
            Updated project
        """
        return self.project_repo.increment_views(project_id)

    def get_public_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        Get public projects for discovery.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of public projects
        """
        return self.project_repo.get_public_projects(skip, limit)
