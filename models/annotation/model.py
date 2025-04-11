#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：model.py
@Author ：Cary
@Date ：2024/1/24 15:06
@Descripttion : ""
"""

from enum import IntEnum
from typing import Dict, Optional, Union

from tortoise import fields

from models.auth.model import AuthUsers
from models.base import BaseModel
from schemas.base import BaseResponse


class DataTypeEnum(IntEnum):
    image = 1
    video = 2
    audio = 3


class TaskStatusEnum(IntEnum):
    not_consulted = 0  # 未查阅
    annotation = 1  # 标注
    examine = 2  # 审核审查
    deliver = 3  # 交付
    train = 4  # 训练中
    test = 5  # 测试评估


class obj_attributes(BaseResponse):
    type: str = "radio"  # radio ,text
    description: str = ""
    options: Optional[dict] = None
    default_value: Optional[str] = None
    keyboard_shortcut: Optional[dict] = None


class label_attributes(BaseResponse):
    """
    用户组创建响应
    """

    region: Optional[Dict[str, obj_attributes]] = None
    file: Optional[Dict[str, obj_attributes]] = None


class File_Infos(BaseModel):
    """
    文件信息
    """

    name = fields.CharField(max_length=32, unique=True, description="文件名")
    path = fields.CharField(max_length=128, unique=True, description="存储路径")
    datasets: fields.ForeignKeyNullableRelation["Datasets"] = fields.ForeignKeyField(
        "models.Datasets", related_name="files", null=True
    )
    annotation: fields.OneToOneNullableRelation["Task_datas"]

    class Meta:
        table = "file_infos"
        table_description = "文件信息"
        indexes = (
            "name",
            "path",
        )


class Datasets(BaseModel):
    """
    数据集
    """

    name = fields.CharField(max_length=32, unique=True, description="名称")
    desc = fields.CharField(max_length=128, null=True, description="描述")
    data_type = fields.IntEnumField(
        enum_type=DataTypeEnum, default=1, description="数据类型(1=image,2=video)"
    )
    files: fields.ReverseRelation["File_Infos"]
    tasks: fields.ReverseRelation["Tasks"]  # 多对一

    # 计算关联文件数量数
    def file_count(self) -> int:
        return len(self.files)

    # 计算关联任务数量数
    def task_count(self) -> int:
        return len(self.tasks)

    class Meta:
        table = "datasets"
        table_description = "数据集"
        indexes = ("name", "data_type")


class Tasks(BaseModel):
    """
    标注任务
    """

    name = fields.CharField(max_length=32, unique=True, description="名称")
    desc = fields.CharField(max_length=128, null=True, description="描述")
    status = fields.IntEnumField(
        enum_type=TaskStatusEnum, default=0, description="任务状态"
    )
    attributes = fields.JSONField(
        default={}, description="标签元数据，定义任务标签,"
    )
    user_metadatas = fields.JSONField(
        default={}, description="记录用户所有数数据，比如标注到第几张,"
    )
    """
    {
        user_id : {"current_index": 0} # user_id的当前任务进度
    }
    """
    datasets: fields.ForeignKeyNullableRelation["Datasets"] = fields.ForeignKeyField(
        "models.Datasets", related_name="tasks", null=True
    )
    task_datas: fields.ReverseRelation["Task_datas"]  # 多对一

    class Meta:
        table = "tasks"
        table_description = "数据集"
        indexes = ("name", "status")


class Task_datas(BaseModel):
    """
    标注任务数据
    """

    status = fields.IntEnumField(
        enum_type=TaskStatusEnum, default=1, description="任务状态"
    )
    annotation = fields.JSONField(default={}, description="标注数据")
    worker: fields.OneToOneRelation["AuthUsers"] = fields.OneToOneField(
        "models.AuthUsers",
        default=None,
        on_delete=fields.OnDelete.CASCADE,
        related_name="task_data",
        null=True,
    )  # 一对一
    file_info: fields.OneToOneRelation["File_Infos"] = fields.OneToOneField(
        "models.File_Infos",
        default=None,
        on_delete=fields.OnDelete.CASCADE,
        related_name="annotation",
    )  # 一对一
    task: fields.ForeignKeyNullableRelation["Tasks"] = fields.ForeignKeyField(
        "models.Tasks",
        on_delete=fields.OnDelete.CASCADE,
        related_name="task_datas",
    )  # 多对一

    class Meta:
        table = "task_data"
        table_description = "数据集"
        indexes = ("status",)
Task_datas.delete