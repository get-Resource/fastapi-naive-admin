# !/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@File ：routers.py
@Author ：Cary
@Date ：2024/2/3 16:17
@Descripttion : "路由总入口"
"""
from fastapi import APIRouter, Depends, Security

from apis.auth.auth_urls import authRouters
from apis.data_task.data_task_urls import dataRouters
from apis.data_task.datasets import router_notDepends
from apis.login.login_urls import loginRouters
from apis.system.system_url import systemRouters
from apis.test.test_url import testRouters
from core.Security.auth_jwt import check_user_jwt
from utils.config import settings

Routers = APIRouter(prefix=settings.SYS_ROUTER_PREFIX)

# 登录
Routers.include_router(loginRouters, tags=["login"])
# 权限
Routers.include_router(
    authRouters, prefix="/auth", dependencies=[Security(check_user_jwt)], tags=["auth"]
)
# 系统
Routers.include_router(
    systemRouters,
    prefix="/system",
    dependencies=[Security(check_user_jwt)],
    tags=["system"],
)
Routers.include_router(
    dataRouters,
    prefix="/data_task",
    dependencies=[Security(check_user_jwt)],
    tags=["data_task"],
)
Routers.include_router(
    router_notDepends,
    prefix="/data_task",
    tags=["data_task"],
)

# 供前端测试接口
Routers.include_router(
    testRouters, prefix="/test", dependencies=[Security(check_user_jwt)], tags=["test"]
)
