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

from models.annotation.model import Datasets
from schemas.base import BaseResponse


# -------------------------------角色创建---------------------------------
class DataCreateRequest(
    pydantic_model_creator(
        cls=Datasets,
        name="DataCreateRequest",
        exclude=("nickname", "create_at", "update_at"),
        exclude_readonly=True,
    )
):
    """
    数据集创建请求
    """

    pass
    # menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


DataCreateResult = pydantic_model_creator(
    cls=Datasets, exclude=("Datas_users",), name="DataCreateResult"
)


class DataCreateResultDocs(DataCreateResult):
    menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


class DataCreateResponse(BaseResponse):
    """
    用户组创建响应
    """

    data: Optional[DataCreateResultDocs] = None


# # -------------------------------角色删除---------------------------------
class DataDeleteResponse(BaseResponse):
    """
    单角色删除响应
    """

    data: Optional[Dict] = {"Data_id": 1}


# -------------------------------角色更新---------------------------------
class DataUpdateRequest(
    pydantic_model_creator(
        cls=Datasets,
        name="DataUpdateRequest",
        optional=("name", "nickname"),
        exclude=("Datas_users",),
        exclude_readonly=True,
    )
):
    """
    单角色更新请求
    """

    menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


# 单用户更新结果
DataUpdateResult = pydantic_model_creator(
    cls=Datasets, exclude=("Datas_users",), name="DataUpdateResult"
)


class DataUpdateResultDocs(DataUpdateResult):
    menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


class DataUpdateResponse(BaseResponse):
    """
    单用户更新响应
    """

    data: Optional[DataUpdateResultDocs] = None


# # -------------------------------角色查询---------------------------------


# # 角色列表结果
DataQuerySet = pydantic_queryset_creator(
    cls=Datasets,
    name="DataQuerySet",
    computed=("file_count",),
)


class DataQueryResultDocs(BaseModel):
    result: Optional[List[DataCreateResultDocs]]


class DataQueryResponse(BaseResponse):
    """
    角色列表响应
    """

    data: Optional[DataQueryResultDocs] = None
