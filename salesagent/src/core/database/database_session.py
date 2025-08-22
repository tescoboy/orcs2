"""
Standardized database session management for the AdCP Sales Agent.

This module provides a consistent, thread-safe approach to database session
management across the entire application.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from src.core.database.db_config import DatabaseConfig

# Create engine and session factory
engine = create_engine(DatabaseConfig.get_connection_string())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import logging

logger = logging.getLogger(__name__)

# Thread-safe session factory
db_session = scoped_session(SessionLocal)


def get_engine():
    """Get the current database engine."""
    return engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.

    Usage:
        with get_db_session() as session:
            result = session.query(Model).filter(...).first()
            session.add(new_object)
            session.commit()  # Explicit commit needed

    The session will automatically rollback on exception and
    always be properly closed.
    """
    session = db_session()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        db_session.remove()


def execute_with_retry(func, max_retries: int = 3, retry_on: tuple = (SQLAlchemyError,)) -> Any:
    """
    Execute a database operation with retry logic.

    Args:
        func: Function that takes a session as its first argument
        max_retries: Maximum number of retry attempts
        retry_on: Tuple of exception types to retry on

    Returns:
        The result of the function
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            with get_db_session() as session:
                result = func(session)
                session.commit()
                return result
        except retry_on as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                db_session.remove()  # Clear the session registry
                continue
            raise

    if last_exception:
        raise last_exception


class DatabaseManager:
    """
    Manager class for database operations with session management.

    This class can be used as a base for services that need
    consistent database access patterns.
    """

    def __init__(self):
        self._session: Session | None = None

    @property
    def session(self) -> Session:
        """Get or create a session."""
        if self._session is None:
            self._session = db_session()
        return self._session

    def commit(self):
        """Commit the current transaction."""
        if self._session:
            try:
                self._session.commit()
            except SQLAlchemyError:
                self.rollback()
                raise

    def rollback(self):
        """Rollback the current transaction."""
        if self._session:
            self._session.rollback()

    def close(self):
        """Close and cleanup the session."""
        if self._session:
            self._session.close()
            db_session.remove()
            self._session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


# Convenience functions for common patterns
def get_or_404(session: Session, model, **kwargs):
    """
    Get a model instance or raise 404-like exception.

    Args:
        session: Database session
        model: SQLAlchemy model class
        **kwargs: Filter criteria

    Returns:
        Model instance

    Raises:
        ValueError: If not found
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        raise ValueError(f"{model.__name__} not found with criteria: {kwargs}")
    return instance


def get_or_create(session: Session, model, defaults: dict = None, **kwargs):
    """
    Get an existing instance or create a new one.

    Args:
        session: Database session
        model: SQLAlchemy model class
        defaults: Default values for creation
        **kwargs: Filter criteria (also used for creation)

    Returns:
        Tuple of (instance, created) where created is a boolean
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False

    params = dict(kwargs)
    if defaults:
        params.update(defaults)

    instance = model(**params)
    session.add(instance)
    return instance, True
