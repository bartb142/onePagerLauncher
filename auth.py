# app/auth.py
import os
from fastapi import Request, HTTPException

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", None)

if not ADMIN_PASSWORD:
    raise RuntimeError("Environment variable ADMIN_PASSWORD must be set.")

def is_logged_in(request: Request) -> bool:
    return request.cookies.get("admin") == "1"

def require_login(request: Request):
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
