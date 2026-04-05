"""
Database base configuration.
Import all models here to ensure they are registered with SQLAlchemy.
"""
from sqlalchemy.ext.declarative import declarative_base

# Create base class for all models
Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models.user import User  # noqa
from app.models.plan import Plan  # noqa
from app.models.subscription import Subscription  # noqa
from app.models.payment import Payment  # noqa
from app.models.project import Project  # noqa
from app.models.scene import Scene  # noqa
from app.models.character import Character  # noqa
from app.models.media_asset import MediaAsset  # noqa
from app.models.render_job import RenderJob  # noqa
from app.models.feature_flag import FeatureFlag  # noqa
from app.models.analytics_log import AnalyticsLog  # noqa
