import http.client
from urllib.request import urlopen
from nicegui import app, ui
from fastapi import FastAPI, Request, HTTPException
import httpx
from core.NiceguiWeb.annotator import editor_annotator
from core.NiceguiWeb.api import check_user_jwt
from utils.config import settings
from fastapi.testclient import TestClient

def register_gui(fastapi_app: FastAPI) -> None:
    client = httpx.Client()
    @ui.page('/annotator')
    async def ui_page_annotator(request: Request,task_id,access_token=None,refresh_token=None,):
        base_url = str(request.base_url)
        if base_url[-1] == "/":
            base_url = base_url[:-1]
        client.base_url = base_url +settings.SYS_ROUTER_PREFIX
        app.storage.client["client"] = client
        user = await check_user_jwt(access_token,refresh_token,)
        ui.add_head_html('''
            <style>
                .my-red-label {
                    color: Crimson;
                    font-weight: bold;
                }
            </style>
        ''')
        if isinstance(user,dict):
            app.storage.user["UserInfo"] = user
            await editor_annotator(task_id,access_token,refresh_token,request)
        else:
            ui.label(f"{user},登录并传递有效的")

    ui.run_with(
        fastapi_app,
        mount_path='/gui',
        storage_secret=settings.SECRET_JWT_KEY,  # 注：设置密钥是可选的，但允许每个用户进行持久存储
    )
