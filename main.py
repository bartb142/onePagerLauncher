# app/main.py
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException


from auth import require_login, ADMIN_PASSWORD

BASE_DIR = Path('/app/').resolve()
SITES_DIR = BASE_DIR / "sites"
SITES_DIR.mkdir(exist_ok=True)

app = FastAPI()
# Serve all site static files under /static/<slug>/...
app.mount("/static", StaticFiles(directory=str(SITES_DIR)), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def generate_slug() -> str:
    return uuid.uuid4().hex[:6]


# ----------
# PUBLIC
# ----------
@app.get("/p/{slug}", response_class=HTMLResponse)
def serve_page(slug: str):
    site_dir = SITES_DIR / slug
    index_path = site_dir / "index.html"
    if not index_path.exists():
        return HTMLResponse("Page not found", status_code=404)

    html = index_path.read_text(encoding="utf-8")

    # Replace relative asset paths "css/..." and "imgs/..." to absolute /static/<slug>/...
    # Handles double or single quoted attributes and simple occurrences.
    html = html.replace('href="css/', f'href="/static/{slug}/css/')
    html = html.replace("href='css/", f"href='/static/{slug}/css/")
    html = html.replace('src="imgs/', f'src="/static/{slug}/imgs/')
    html = html.replace("src='imgs/", f"src='/static/{slug}/imgs/")

    # Also handle <link rel="stylesheet" href="styles.css"> (no css/ prefix)
    # If you expect bare filenames, you might want to expand further. For now we encourage users to use css/ and imgs/ dirs.
    return HTMLResponse(html)


# ----------
# ADMIN - login
# ----------
@app.exception_handler(HTTPException)
async def auth_exception_handler(request, exc: HTTPException):
    # Only handle 401 (unauthenticated)
    if exc.status_code == 401:
        return RedirectResponse("/admin/login")
    # For anything else, rethrow the exception
    raise exc

@app.get("/", response_class=HTMLResponse)
def root_page(request: Request):
    return RedirectResponse("/admin/login")

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
def admin_login_submit(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse("/admin", status_code=302)
        response.set_cookie("admin", "1", httponly=True, secure=False)  # set secure=True in prod with https
        return response
    return RedirectResponse("/admin/login?error=1", status_code=302)


@app.get("/admin/logout")
def admin_logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("admin")
    return response

# ----------
# ADMIN - upload:
# ----------
@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):
    require_login(request)
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def handle_upload(
    request: Request,
    html_file: Optional[UploadFile] = File(None),
    css_files: List[UploadFile] = File([]),
    img_files: List[UploadFile] = File([]),
    custom_slug: Optional[str] = Form(None),
):

    slug = custom_slug.strip() if custom_slug else generate_slug()
    # basic validation for slug
    slug = slug.replace("/", "_")
    site_dir = SITES_DIR / slug
    if site_dir.exists():
        return HTMLResponse("Slug already exists. Choose a different slug.", status_code=400)

    (site_dir / "css").mkdir(parents=True, exist_ok=True)
    (site_dir / "imgs").mkdir(parents=True, exist_ok=True)

    # index.html required
    if html_file is None:
        return HTMLResponse("index.html is required", status_code=400)

    index_path = site_dir / "index.html"
    with index_path.open("wb") as f:
        f.write(await html_file.read())

    # save css files
    for css in css_files:
        target = site_dir / "css" / css.filename
        with target.open("wb") as f:
            f.write(await css.read())

    # save img files
    for img in img_files:
        target = site_dir / "imgs" / img.filename
        with target.open("wb") as f:
            f.write(await img.read())

    return templates.TemplateResponse("success.html", {"request": request, "slug": slug})

# ----------
# ADMIN - dashboard: list pages
# ----------
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    require_login(request)
    slugs = sorted([p.name for p in SITES_DIR.iterdir() if p.is_dir()])
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "slugs": slugs})


# ----------
# ADMIN - edit page (show current index, assets)
# ----------
@app.get("/admin/edit/{slug}", response_class=HTMLResponse)
def admin_edit_page(request: Request, slug: str):
    require_login(request)
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return HTMLResponse("Not found", status_code=404)

    index_html = (site_dir / "index.html").read_text(encoding="utf-8") if (site_dir / "index.html").exists() else ""
    css_files = sorted([p.name for p in (site_dir / "css").iterdir()]) if (site_dir / "css").exists() else []
    img_files = sorted([p.name for p in (site_dir / "imgs").iterdir()]) if (site_dir / "imgs").exists() else []

    return templates.TemplateResponse("edit_page.html", {
        "request": request,
        "slug": slug,
        "index_html": index_html,
        "css_files": css_files,
        "img_files": img_files,
    })


# ----------
# ADMIN - update index.html content (keep same URL)
# ----------
@app.post("/admin/edit/{slug}")
async def admin_save_edit(request: Request, slug: str, html_content: str = Form(...)):
    require_login(request)
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return HTMLResponse("Not found", status_code=404)
    (site_dir / "index.html").write_text(html_content, encoding="utf-8")
    return RedirectResponse(f"/admin/edit/{slug}", status_code=302)


# ----------
# ADMIN - upload additional assets to existing page
# ----------
@app.post("/admin/upload_assets/{slug}")
async def admin_upload_assets(
    request: Request,
    slug: str,
    css_files: List[UploadFile] = File([]),
    img_files: List[UploadFile] = File([]),
):
    require_login(request)
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return HTMLResponse("Not found", status_code=404)

    css_dir = site_dir / "css"
    img_dir = site_dir / "imgs"
    css_dir.mkdir(exist_ok=True)
    img_dir.mkdir(exist_ok=True)

    for css in css_files:
        target = css_dir / css.filename
        with target.open("wb") as f:
            f.write(await css.read())

    for img in img_files:
        target = img_dir / img.filename
        with target.open("wb") as f:
            f.write(await img.read())

    return RedirectResponse(f"/admin/edit/{slug}", status_code=302)


# ----------
# ADMIN - delete a single asset
# ----------
@app.post("/admin/delete_asset/{slug}")
def admin_delete_asset(request: Request, slug: str, file_type: str = Form(...), filename: str = Form(...)):
    require_login(request)
    site_dir = SITES_DIR / slug
    folder = site_dir / ("css" if file_type == "css" else "imgs")
    target = folder / filename
    if target.exists():
        target.unlink()
    return RedirectResponse(f"/admin/edit/{slug}", status_code=302)


# ----------
# ADMIN - delete entire page
# ----------
@app.post("/admin/delete_page/{slug}")
def admin_delete_page(request: Request, slug: str):
    require_login(request)
    site_dir = SITES_DIR / slug
    if site_dir.exists() and site_dir.is_dir():
        shutil.rmtree(site_dir)
    return RedirectResponse("/admin", status_code=302)
