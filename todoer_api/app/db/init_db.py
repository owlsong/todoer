# import logging
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import base  # noqa: F401
from app.task_data import TASKS
from app.core.config import get_logger

logger = get_logger(__name__)
# logger = logging.getLogger(__name__)

FIRST_SUPERUSER = "admin@todoer.com"

# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# for more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)
    if FIRST_SUPERUSER:
        user = crud.user.get_by_email(db, email=FIRST_SUPERUSER)
        if not user:
            user_in = schemas.UserCreate(
                first_name="Admin",
                surname="User",
                email=FIRST_SUPERUSER,
                is_superuser=True,
            )
            user = crud.user.create(db, obj_in=user_in)  # noqa: F841
            logger.info(f"Create initial superuser id={user.id}")
        else:
            logger.warning(
                "Skipping creating superuser. User with email "
                f"{FIRST_SUPERUSER} already exists. "
            )

        db_tasks = crud.task.get_multi(db, limit=5)
        if 0 == len(db_tasks):
            for task in TASKS:
                task_in = schemas.TaskCreate(
                    project=task["project"],
                    summary=task["summary"],
                    description=task["description"],
                    status=task["status"],
                    assignee_id=user.id,
                    tags="init-data",
                )
                crud.task.create(db, obj_in=task_in)
    else:
        logger.warning(
            "Skipping creating superuser.  FIRST_SUPERUSER needs to be "
            "provided as an env variable. "
            "e.g.  FIRST_SUPERUSER=admin@api.coursemaker.io"
        )
