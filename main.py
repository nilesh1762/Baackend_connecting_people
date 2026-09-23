import importlib
import pkgutil
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, DBAPIError  # 🚀 IMPORT DATABASE EXCEPTIONS

# 🚀 IMPORT YOUR ERROR HANDLERS FROM YOUR UTILS FILE
from src.utils.error import (
    global_exception_handler, 
    sqlalchemy_integrity_handler, 
    sqlalchemy_db_handler
)

# Database layer bindings
from src.utils.db import Base, engine
# Explicit model registrations to bind schemas prior to engine generation
from src.Task.model import TaskModel 

# Static router imports
from src.Task.router import task_router

import src.User.Router as user_router_package 
from src.User.Router.WebsocketRouter.web_Scoket_router import ws_router as explicit_ws_router 
from src.User.Router.MediaRouter.get_user_media_route import gallery_router
from src.User.Router.MediaRouter.set_banner_media_route import banner_router
# 1. Initialize DB Metadata (Creates Oracle tables safely case-insensitively)
Base.metadata.create_all(bind=engine)

# 2. Instantiate the Singleton Core FastAPI Application Engine
app = FastAPI(
    title="Core Task and Engagement Engine",
    version="1.0.0"
)

# 🚀 STEP 2.5: REGISTER EXCEPTION HANDLERS INTO THE FASTAPI KERNEL
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(IntegrityError, sqlalchemy_integrity_handler)
app.add_exception_handler(DBAPIError, sqlalchemy_db_handler)

# 3. Apply Security Protocols (CORS Middleware Setup)
origins = [
     "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"                     
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       # Explicitly permits GET, POST, PUT, DELETE, PATCH, OPTIONS
    allow_headers=["*"],       # Explicitly permits authorization, tokens, content types
)

# 4. Mount Explicitly Imported Feature Modules
app.include_router(task_router, tags=["Tasks"])
app.include_router(explicit_ws_router)
app.include_router(gallery_router)
app.include_router(banner_router)
# 5. Execute Dynamic Autoloading Pipeline for Sub-module AppRouters
for _, module_name, _ in pkgutil.iter_modules(user_router_package.__path__):
    full_module_name = f"{user_router_package.__name__}.{module_name}"
    module = importlib.import_module(full_module_name)
    
    # Introspect internal module signatures for valid APIRouter instances
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if isinstance(attribute, APIRouter):
            app.include_router(attribute, tags=["Users"])

# 6. Global Base Application Endpoint Probe
@app.get("/")
def read_root():
    return {"status": "Application Engine is running successfully"}
