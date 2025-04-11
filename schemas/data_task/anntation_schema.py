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

from models.annotation.model import Datasets, Task_datas, Tasks
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


AnntationCreateResult = pydantic_model_creator(
    cls=Task_datas, exclude=("Datas_users",), name="AnntationCreateResult"
)


class AnntationCreateResultDocs(AnntationCreateResult):
    pass
    # menus: Optional[List[int]] = Field(default=None, description="菜单 id 列表")


class AnntationCreateResponse(BaseResponse):
    """
    用户组创建响应
    """

    data: Optional[AnntationCreateResultDocs] = None


# # -------------------------------角色删除---------------------------------
class AnntationDeleteResponse(BaseResponse):
    """
    单角色删除响应
    """

    data: Optional[Dict] = {"Task_id": 1}


# -------------------------------角色更新---------------------------------
class AnntationUpdateRequest(
    pydantic_model_creator(
        cls=Task_datas,
        name="AnntationUpdateRequest",
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
AnntationUpdateResult = pydantic_model_creator(
    cls=Task_datas,
    exclude={
        "worker": {"password", "roles"},
        "file_info": {"datasets"},
        "task": True,
    },
    name="AnntationUpdateResult",
)


class AnntationUpdateResultDocs(AnntationUpdateResult):
    pass


class AnntationUpdateResponse(BaseResponse):
    """
    单用户更新响应
    """

    data: Optional[AnntationUpdateResultDocs] = None


# # -------------------------------角色查询---------------------------------


# # 角色列表结果
AnntationQuerySet = pydantic_queryset_creator(
    cls=Task_datas,
    name="AnntationQuerySet",
    # computed=("file_count",),
)


class AnntationQueryRequest(BaseModel):  # 查询请求体
    prefetch: int = 0  # 数据预取，预分配任务数量


class AnntationQueryResultDocs(BaseModel):
    result: Optional[List[AnntationCreateResultDocs]]


class AnntationQueryResponse(BaseResponse):
    """
    角色列表响应
    """

    data: Optional[AnntationQueryResultDocs] = None

# 当前用户查询结果
Task_datasGetResult = pydantic_model_creator(cls=Task_datas, name="Task_datasGetResult", exclude=("task_datas",))


class Task_datasGetResponse(BaseResponse):
    """
    当前用户查询响应
    """

    data: Optional[Task_datasGetResult] = None # type: ignore


# region 注释更新


class Regions_model(BaseModel):  # 区域标注属性
    shape: str = None  # 坐标信息其中name 为形状类型，如 rect,polygon,point,ellipse,circle,polyline
    """  shape_attributes 例子
    "shape_attributes": {
        "name": "rect",
        "x": 607,
        "y": 1138,
        "width": 602,
        "height": 485
    },
    "shape_attributes": {
        "name": "polygon",
        "all_points_x": [
            706,
            900,
            1010,
            852
        ],
        "all_points_y": [
            552,
            497,
            528,
            653
        ]
    },
    "shape_attributes": {
        "name": "point",
        "cx": 938,
        "cy": 293
    },
    "shape_attributes": {
        "name": "ellipse",
        "cx": 283,
        "cy": 257,
        "rx": 53,
        "ry": 103,
        "theta": 0
    },
    "shape_attributes": {
        "name": "circle",
        "cx": 206,
        "cy": 1066,
        "r": 66
    },
    "shape_attributes": {
        "name": "polyline",
        "all_points_x": [
            780,
            1279,
            1289,
            936,
            653
        ],
        "all_points_y": [
            185,
            156,
            290,
            367,
            410
        ]
    },
}
    """
    label: str = ""  # 区域属性，其中 key 为属性名称，value为属性值
    transcription:str = "" # 文本抄写
    points: list = []  # 区域属性，其中 key 为属性名称，value为属性值


class anntation_UpdateRequest(BaseModel):  # 标注注释更新请求体
    file_attributes: dict = {}  # 文件属性标注，其中 key 为属性名称，value为属性值
    regions: List[Regions_model] = []  # 数据预取，预分配任务数量


# endregion
