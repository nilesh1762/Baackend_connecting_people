from typing import Optional

from fastapi import APIRouter
from src.utils.helper import is_authenticated
from src.User.model import UserModel
from src.Task import controller
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from src.utils.db import init_db
from sqlalchemy.orm import Session
from src.Task.model import TaskModel

task_router = APIRouter(prefix="/tasks", )

class Task(BaseModel):
    title: str
    description: str
    is_completed: bool = False

@task_router.post("/create_task", status_code=status.HTTP_201_CREATED)
def create_task(
    body: Task,
    user: UserModel = Depends(is_authenticated),
    db: Session = Depends(init_db),

):
    db_task = TaskModel(**body.model_dump(), created_by=user.email)
    # task_dict = {}
    # task_list=[]
    # task_dict["title"] = body.title
    # task_dict["description"] = body.description
    # task_dict["is_completed"] = body.is_completed
    # task_list.append(task_dict)
    task_create = controller.create_task(db_task, db)
    return {"Response": "Task created successfully", "Task": body, "Status": 200}

@task_router.get("/get_task")
def get_task(db:Session = Depends(init_db), user: UserModel = Depends(is_authenticated),):
    task = controller.get_task(db, user)
    
    return {"Response": "Task retrieved successfully", "Task": task, "Status": 200}
