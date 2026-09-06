"""
Application database: users, repositories, memberships (RBAC), analyses,
audit log. This is the persistent "system of record" layer — separate from
the Entire Graph evidence (queried live/mocked) and the Databricks
historical layer (queried separately, see databricks_adapter.py).

Uses SQLAlchemy so DATABASE_URL can point at SQLite (default, zero-setup)
or a real Postgres instance without any model changes.
"""
import datetime
import uuid

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean, Text, Integer, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    github_login = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    avatar_url = Column(String, default="")
    # In real mode: encrypted at rest, never returned to the client.
    github_access_token_encrypted = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memberships = relationship("Membership", back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"
    id = Column(String, primary_key=True, default=gen_id)
    full_name = Column(String, nullable=False)  # e.g. "acme/checkout-service"
    default_branch = Column(String, default="main")
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memberships = relationship("Membership", back_populates="repository")
    analyses = relationship("Analysis", back_populates="repository")


class Membership(Base):
    """Role-based access: viewer / developer / admin, scoped per repository."""
    __tablename__ = "memberships"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    role = Column(String, nullable=False, default="viewer")  # viewer|developer|admin

    user = relationship("User", back_populates="memberships")
    repository = relationship("Repository", back_populates="memberships")


class Analysis(Base):
    """One 'What will this change break?' run against a commit/PR."""
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    ref_label = Column(String, nullable=False)  # branch/commit/PR shown to user
    base_sha = Column(String, default="")
    head_sha = Column(String, default="")
    status = Column(String, default="completed")  # queued|running|completed|failed
    risk_level = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    result_json = Column(Text, nullable=True)  # full cached AnalysisResult payload
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    repository = relationship("Repository", back_populates="analyses")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, default="")
    ip = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Existing demo databases used the pre-buildathon vocabulary.  Migrate it
    # in-place so authorization is always evaluated against the public model.
    with engine.begin() as conn:
        for legacy, role in {"owner": "admin", "member": "developer", "reviewer": "viewer"}.items():
            conn.execute(
                Membership.__table__.update()
                .where(Membership.role == legacy)
                .values(role=role)
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
