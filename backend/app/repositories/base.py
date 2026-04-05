"""
Base repository class with common CRUD operations.
All repositories should inherit from this.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Get a single record by field value.

        Args:
            field_name: Field name to filter by
            value: Field value

        Returns:
            Model instance or None
        """
        return self.db.query(self.model).filter(
            getattr(self.model, field_name) == value
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by (descending)

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        if order_by:
            query = query.order_by(desc(getattr(self.model, order_by)))

        return query.offset(skip).limit(limit).all()

    def get_multi(
        self,
        filters: dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with filters.

        Args:
            filters: Dictionary of field:value filters
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        for field, value in filters.items():
            query = query.filter(getattr(self.model, field) == value)

        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Dictionary of field values

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """
        Update an existing record.

        Args:
            db_obj: Existing model instance
            obj_in: Dictionary of field values to update

        Returns:
            Updated model instance
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.

        Args:
            filters: Optional dictionary of field:value filters

        Returns:
            Number of records
        """
        query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                query = query.filter(getattr(self.model, field) == value)

        return query.count()

    def exists(self, id: int) -> bool:
        """
        Check if a record exists by ID.

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first() is not None
