"""
SQLite persistence layer for resume analysis history.
"""

import datetime
import json
import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


DATABASE_URL = "sqlite:///./data/history/ats_history.db"


# Make sure the database directory exists.
os.makedirs(
    "data/history",
    exist_ok=True,
)


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


Base = declarative_base()


class AnalysisRecord(Base):

    __tablename__ = "analysis_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    candidate_name = Column(
        String,
        nullable=True,
    )

    resume_filename = Column(
        String,
        nullable=True,
    )

    job_title = Column(
        String,
        nullable=True,
    )

    overall_ats_score = Column(Float)

    skills_match_score = Column(Float)

    experience_match_score = Column(Float)

    education_match_score = Column(Float)

    keyword_match_score = Column(Float)

    semantic_similarity_score = Column(Float)

    resume_quality_score = Column(Float)

    full_report_json = Column(Text)


def init_db():

    Base.metadata.create_all(
        bind=engine
    )


def save_analysis(
    report: dict,
    candidate_name: str = None,
    resume_filename: str = None,
    job_title: str = None,
) -> int:

    session = SessionLocal()

    try:

        ats_report = report.get(
            "ats_report",
            {},
        )

        quality_report = report.get(
            "quality_report",
            {},
        )

        # Support both names so the database
        # remains compatible with the quality module.
        quality_score = quality_report.get(
            "quality_score",
            quality_report.get(
                "overall_quality_score",
                0.0,
            ),
        )

        record = AnalysisRecord(

            candidate_name=candidate_name,

            resume_filename=resume_filename,

            job_title=job_title,

            overall_ats_score=ats_report.get(
                "overall_ats_score",
                0.0,
            ),

            skills_match_score=ats_report.get(
                "skills_match_score",
                0.0,
            ),

            experience_match_score=ats_report.get(
                "experience_match_score",
                0.0,
            ),

            education_match_score=ats_report.get(
                "education_match_score",
                0.0,
            ),

            keyword_match_score=ats_report.get(
                "keyword_match_score",
                0.0,
            ),

            semantic_similarity_score=ats_report.get(
                "semantic_similarity_score",
                0.0,
            ),

            resume_quality_score=quality_score,

            full_report_json=json.dumps(
                report,
                default=str,
            ),
        )

        session.add(record)

        session.commit()

        session.refresh(record)

        return record.id

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()


def get_history(
    limit: int = 50,
    offset: int = 0,
) -> list:

    session = SessionLocal()

    try:

        rows = (
            session.query(AnalysisRecord)
            .order_by(
                AnalysisRecord.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [

            {
                "id": r.id,

                "created_at": (
                    r.created_at.isoformat()
                    if r.created_at
                    else None
                ),

                "candidate_name": r.candidate_name,

                "resume_filename": r.resume_filename,

                "job_title": r.job_title,

                "overall_ats_score": (
                    r.overall_ats_score
                ),

                "skills_match_score": (
                    r.skills_match_score
                ),

                "experience_match_score": (
                    r.experience_match_score
                ),

                "education_match_score": (
                    r.education_match_score
                ),

                "keyword_match_score": (
                    r.keyword_match_score
                ),

                "semantic_similarity_score": (
                    r.semantic_similarity_score
                ),

                "resume_quality_score": (
                    r.resume_quality_score
                ),
            }

            for r in rows
        ]

    finally:

        session.close()


def get_analysis_by_id(
    analysis_id: int,
) -> dict:

    session = SessionLocal()

    try:

        record = (
            session.query(AnalysisRecord)
            .filter(
                AnalysisRecord.id == analysis_id
            )
            .first()
        )

        if not record:
            return None

        return json.loads(
            record.full_report_json
        )

    finally:

        session.close()