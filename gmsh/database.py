import logging

from gmsh.config import cfg

from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

log = logging.getLogger(__name__)

Base = declarative_base()

default_engine = create_engine(cfg.db.main.location('sqlite:///gmsh.sqlite'))
sqlol_engine = create_engine(cfg.db.playground.location('sqlite:///playground.sqlite'))


class ReactionMessage(Base):
    __tablename__ = 'tutor_reactmsg'

    id = Column(Integer, primary_key=True)
    subject_id = Column(None, ForeignKey('tutor_subjects.id'))

    subject = relationship("Subject", back_populates="reactmsg", uselist=False)


class Subject(Base):
    __tablename__ = 'tutor_subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    reactmsg = relationship("ReactionMessage", back_populates="subject", cascade="all, delete, delete-orphan")
    roles = relationship("TutorRoles", back_populates="subject", cascade="all, delete, delete-orphan")


class TutorRoles(Base):
    __tablename__ = 'tutor_roles'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    subject_id = Column(Integer, ForeignKey('tutor_subjects.id'))
    proficiency = Column(Integer)

    subject = relationship("Subject", back_populates="roles", uselist=False)


class BreakoutRoom(Base):
    __tablename__ = 'tutor_br'

    id = Column(Integer, primary_key=True)
    vc_id = Column(Integer)
    role_id = Column(Integer)
    name = Column(String)
    private = Column(Boolean)


try:
    Base.metadata.create_all(default_engine)
    log.info("Tables created")
except Exception as e:
    log.error("Error occurred during Table creation!", exc_info=e)

DefaultSession = sessionmaker()
DefaultSession.configure(bind=default_engine)
