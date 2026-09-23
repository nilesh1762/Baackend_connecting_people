from sqlalchemy import Column, Integer, String, Boolean,Identity
from src.utils.db import Base


class TaskModel(Base):
    __tablename__ = 'USER_TASK'
    id = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    title = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    is_completed = Column(Boolean, default=False)
    created_by = Column(String(100), nullable=True)

    def __repr__(self):
        return '%s,%s,%s,%s' % ( self.title,self.description,self.is_completed,self.created_by)
