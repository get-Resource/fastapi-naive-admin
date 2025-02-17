import logging

import httpx
import time
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, Request, HTTPException
from pydantic import ValidationError
from utils.config import settings
from utils.password_tools import jwt_decode, get_password_hash, random_str
from loguru import logger
from nicegui import run
from nicegui import app, ui

# openssl rand -hex 32
SECRET_KEY = settings.SECRET_JWT_KEY
ALGORITHM = settings.SECRET_JWT_ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = settings.SECRET_JWT_EXP
REFRESH_TOKEN_EXPIRE_MINUTES = settings.SECRET_REJWT_EXP

async def check_user_jwt(access_token,refresh_token,expired_in=0):
    """
    权限验证
    :param token:
    :param req:
    :return:
    """
    jwt_validation_error = HTTPException(status_code=401,
                                         headers={"WWW-Authenticate": f"Bearer {access_token}"}, detail="无效凭证!")
    jwt_expires_error = HTTPException(status_code=401,
                                      headers={"WWW-Authenticate": f"Bearer {access_token}"}, detail="凭证已过期!")
    try:
        # token解密
        payload = jwt_decode(access_token)
        if payload:
            # 用户ID
            user_id = payload.get("user_id", None)
            # 用户名
            username = payload.get("username", None)
            # 无效用户信息
            if user_id is None or username is None:
                raise jwt_validation_error
            # 查询redis是否存在jwt
            now = int(time.mktime(datetime.now().timetuple()))
            expires_in = payload.get("exp", 0)
            expired = expires_in - now
            if expired <= 0:
                raise jwt_expires_error
            payload["access_token"] = access_token
            payload["refresh_token"] = refresh_token
            payload["expired_in"] = expires_in
            # app.storage.user["UserInfo"] = payload
            return payload
        else:
            raise jwt_validation_error
    except (HTTPException, jwt.ExpiredSignatureError) as e:
        data = {
          "access_token": access_token,
          "expired_in": expired_in,
          "refresh_token": refresh_token,
        }
        data = await refreshToken_api(data)
        if isinstance(data, dict):
            app.storage.user["UserInfo"] = data.get("data", {})
            return data
        raise jwt_expires_error
    except (JWTError, ValidationError):
        logger.error("无效凭证!")
    except RuntimeError as e:
        logger.error(e)
    except Exception as e:
        logger.exception(e)
    user_access_token = app.storage.user.get("UserInfo",{}).get("access_token","")
    if user_access_token != access_token:
        refresh_token = app.storage.user.get("UserInfo",{}).get("refresh_token","")
        expires_in = app.storage.user.get("UserInfo",{}).get("expires_in",0)
        return await check_user_jwt(user_access_token,refresh_token,expires_in)
    return "无效凭证!"

# 客户端请求
async def client_request(*args,**kwargs):
    check_jwt = kwargs.pop("check_jwt",False)
    base_err = f"args:{args}, kwargs:{kwargs}"
    user_access_token = app.storage.user.get("UserInfo",{}).get("access_token")
    refresh_token = app.storage.user.get("UserInfo",{}).get("refresh_token")
    expires_in = app.storage.user.get("UserInfo",{}).get("expires_in",0)
    if check_jwt: await check_user_jwt(user_access_token, refresh_token, expires_in)
    try:
        client: httpx.Client = app.storage.client["client"]
        headers = kwargs.get("headers",{})
        headers["Authorization"] = "Bearer " + app.storage.user.get("UserInfo",{}).get("access_token")
        kwargs["headers"] = headers
        res = await run.io_bound(client.request,*args,**kwargs)
        if res.status_code == 200:
            return res.json()
        return base_err +f"status_code: {res.status_code}: {res.text}"
    except Exception as e:
        logging.error(e)
        return base_err + str(e)

async def refreshToken_api(refresh_data):
    # 更新toke
    url = f"{settings.SYS_ROUTER_REFRESH}"
    result = await client_request("post",url,json=refresh_data,check_jwt=False)
    if isinstance(result,dict):
        return result
    return result

async def get_task_api(user_id):
    result = await client_request("get",f"/data_task/annotation_task/get/{user_id}")
    if isinstance(result,dict):
        return result
    return result
