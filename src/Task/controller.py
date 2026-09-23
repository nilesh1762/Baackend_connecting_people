from sqlalchemy.orm import Session
import logging
from src.User.model import UserModel
from src.Task.model import TaskModel

def create_task(body, session):

    try:
        session.add(body)
        session.commit()
        session.refresh(body)

    except Exception as e:
        session.rollback()
        logging.error("Insert-Task Error", e)
        return {"status": "Error", "error": str(e)}

def get_task(db:Session, user: UserModel):
    task = db.query(TaskModel).filter(TaskModel.created_by == user.email)
    try:
        task = task.all()
        return task
    except Exception as e:
        logging.error("Get-Task Error", e)
        return {"status": "Error", "error": str(e)}


