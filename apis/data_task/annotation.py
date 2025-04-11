#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：Datas_api.py
@Author ：Cary
@Date ：2024/2/8 16:36
@Descripttion : ""
"""

import os
from typing import Annotated, Union

from fastapi import APIRouter, Body, Query, Request, UploadFile
from tortoise import timezone

from core.Exeption.Response import fail, success
from models.annotation.model import Datasets, File_Infos, Task_datas, TaskStatusEnum, Tasks
from models.auth.model import AuthUsers
from schemas.data_task import anntation_schema
from utils.config import settings

router = APIRouter(prefix="/annotation")


# @router.post(
#     "/add", summary="添加创建任务", response_model=task_schema.TaskCreateResponse
# )
# async def task_add(create_content: task_schema.TaskCreateRequest):
#     """
#     添加创建任务
#     :param create_content:
#     :return:
#     """
#     get_Task = await Tasks.get_or_none(name=create_content.name)
#     if get_Task:
#         return fail(message=f"对象 {create_content.name} 已经存在!")
#     add_Task = await Tasks.create(**create_content.model_dump(exclude={"menus"}))
#     if not add_Task:
#         return fail(message="创建失败!")
#     # 序列化返回结果
#     form_add_Task = await task_schema.TaskUpdateResult.from_tortoise_orm(add_Task)
#     result = form_add_Task.model_dump()
#     # result["menus"] = menus
#     return success(message="创建成功!", data=result)


# @router.delete(
#     "/del/{Task_id}",
#     summary="删除任务",
#     response_model=task_schema.TaskDeleteResponse,
# )
# async def task_del(Task_id: int):
#     """
#     删除角色
#     :param Task_id:
#     :return:
#     """
#     delete_action = await Tasks.filter(pk=Task_id).delete()
#     if not delete_action:
#         return fail(message="删除失败", data={"id": Task_id})
#     return success(message="删除成功", data={"id": Task_id})


@router.patch(
    "/update/{anntation_id}",
    summary="更新标注",
    response_model=anntation_schema.AnntationUpdateResponse,
)
async def update_anntation(
    request: Request,
    anntation_id: int,
    update_content: anntation_schema.anntation_UpdateRequest,
):
    """
    更新用户
    :param request:
    :param task_id:
    :param update_content:
    :return:
    """
    # # 判断用户是否存在
    # if request.state.user_id == user_id and isinstance(update_content.user_status,
    #                                                    bool) and not update_content.user_status:
    #     return fail(message="您不能将自己禁用")
    get_anntation = await Task_datas.get_or_none(pk=anntation_id)
    if not get_anntation:
        return fail(message="注释任务不存在")
    get_anntation.annotation = update_content.model_dump()
    get_anntation.status = TaskStatusEnum.annotation  # 改为审核状态update_at
    get_anntation.update_at = int(timezone.now().timestamp())  # 改为审核状态
    await get_anntation.save()
    # 序列化
    form_update_anntation = (
        await anntation_schema.AnntationUpdateResult.from_tortoise_orm(get_anntation)
    )
    result = form_update_anntation.model_dump(
        exclude={
            "worker": {"password", "roles"},
            "file_info": {"datasets"},
            "task": True,
        }
    )
    return success(message="更新成功", data=result)


@router.get(
    "/list",
    summary="数据集列表",
    response_model=anntation_schema.AnntationQueryResponse,
)
async def annotation_list(
    request: Request
):
    """
    数据集列表
    """
    prefetch = 0
    user_id = request.state.user_id
    get_user = await AuthUsers.get_or_none(pk=user_id)
    if not get_user:
        return fail(message="用户不存在")
    # 查询结果
    query_data = Task_datas.filter(worker=get_user)

    # 序列化查询结果
    form_query_data = await anntation_schema.AnntationQuerySet.from_queryset(
        query_data
    )
    result = form_query_data.model_dump(
        exclude={
            "__all__": {  # 列表排除
                "worker": {"password", "roles"},
                "file_info": {"datasets"},
                "task": True,
            }
        }
        )

    data = {
        "result": result,
    }
    return success(message="查询成功", data=data)
