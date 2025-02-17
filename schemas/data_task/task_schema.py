#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：Datas_schema.py
@Author ：Cary
@Date ：2024/1/24 23:31
@Descripttion : ""
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from models.annotation.model import Datasets, Tasks
from schemas.base import BaseResponse


# -------------------------------角色创建---------------------------------
class TaskCreateRequest(
    pydantic_model_creator(
        cls=Tasks,
        name="TaskCreateResult",
        exclude=("nickname", "create_at", "update_at", "task_datas"),
        exclude_readonly=True,
    )
):
    """
    数据集创建请求
    """

    pass
    # menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


TaskCreateResult = pydantic_model_creator(
    cls=Tasks, exclude=("Datas_users",), name="TaskCreateResult"
)


class TaskCreateResultDocs(TaskCreateResult):
    pass
    # menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


class TaskCreateResponse(BaseResponse):
    """
    用户组创建响应
    """

    data: Optional[TaskCreateResultDocs] = None


# # -------------------------------角色删除---------------------------------
class TaskDeleteResponse(BaseResponse):
    """
    单角色删除响应
    """

    data: Optional[Dict] = {"Task_id": 1}


# -------------------------------角色更新---------------------------------
class TaskUpdateRequest(
    pydantic_model_creator(
        cls=Tasks,
        name="TaskUpdateRequest",
        optional=("name", "nickname"),
        exclude=("Datas_users",),
        exclude_readonly=True,
    )
):
    """
    单角色更新请求
    """

    pass
    menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


# 单用户更新结果
TaskUpdateResult = pydantic_model_creator(
    cls=Tasks, exclude=("Datas_users",), name="TaskUpdateResult"
)


class TaskUpdateResultDocs(TaskUpdateResult):
    menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


class TaskUpdateResponse(BaseResponse):
    """
    单用户更新响应
    """

    data: Optional[TaskUpdateResultDocs] = None


# # -------------------------------角色查询---------------------------------


# # 角色列表结果
TaskQuerySet = pydantic_queryset_creator(
    cls=Tasks,
    name="TaskQuerySet",
    computed=(),
)


class TaskQueryRequest(BaseModel):  # 查询请求体
    prefetch: int = 0  # 数据预取，预分配任务数量


class TaskQueryResultDocs(BaseModel):
    result: Optional[List[TaskCreateResultDocs]]


class TaskQueryResponse(BaseResponse):
    """
    角色列表响应
    """

    data: Optional[TaskQueryResultDocs] = None


# 当前用户查询结果
TaskGetResult = pydantic_model_creator(cls=Tasks, name="TaskGetResult", exclude=("",))


class TaskGetResponse(BaseResponse):
    """
    当前用户查询响应
    """

    data: Optional[TaskGetResult] = None # type: ignore
