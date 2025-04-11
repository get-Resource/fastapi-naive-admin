#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：Datas_api.py
@Author ：Cary
@Date ：2024/2/8 16:36
@Descripttion : ""
"""

import math
import os
from asyncio import Lock
from typing import Annotated, Union

from fastapi import (
    APIRouter,
    FastAPI,
    File,
    Form,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from loguru import logger
from tortoise import timezone

from core.Exeption.Response import fail, success
from models.annotation.model import Datasets, File_Infos, Task_datas, Tasks
from models.auth.model import AuthUsers
from schemas.auth import users_schema
from schemas.data_task import anntation_schema, task_schema
from utils.config import settings

router = APIRouter(prefix="/annotation_task")
lock = Lock()

@router.post(
    "/add", summary="添加创建任务", response_model=task_schema.TaskCreateResponse
)
async def task_add(create_content: task_schema.TaskCreateRequest):
    """
    添加创建任务
    :param create_content:1
    :return:
    """
    get_Task = await Tasks.get_or_none(name=create_content.name)
    if get_Task:
        return fail(message=f"对象 {create_content.name} 已经存在!")
    # print(await task_schema.TaskUpdateResult.from_tortoise_orm(get_Task))
    # get_Datasets = await Datasets.get_or_none(pk=create_content.datasets_id)
    # if not get_Datasets:
    #     return fail(message=f"数据集 {create_content.name} 不存在!")
    add_Task = await Tasks.create(**create_content.model_dump(exclude={"menus"}))
    if add_Task.datasets is not None:
        datasets: Datasets = await add_Task.datasets
        for file in await datasets.files:
            await Task_datas.create(file_info=file, task=add_Task)
    if not add_Task:
        return fail(message="创建失败!")
    # add_Task.datasets = get_Datasets
    # await add_Task.save()
    # 序列化返回结果
    form_add_Task = await task_schema.TaskUpdateResult.from_tortoise_orm(add_Task)
    result = form_add_Task.model_dump()
    return success(message="创建成功!", data=result)


@router.delete(
    "/del/{Task_id}",
    summary="删除任务",
    response_model=task_schema.TaskDeleteResponse,
)
async def task_del(Task_id: int):
    """
    删除角色
    :param Task_id:
    :return:
    """
    delete_action = await Tasks.filter(pk=Task_id).delete()
    if not delete_action:
        return fail(message="删除失败", data={"id": Task_id})
    return success(message="删除成功", data={"id": Task_id})


@router.patch(
    "/set/{task_id}", summary="更新任务", response_model=task_schema.TaskUpdateResponse
)
async def Task_set(
    request: Request, task_id: int, update_content: task_schema.TaskUpdateRequest
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
    get_task = await Tasks.get_or_none(pk=task_id)
    if not get_task:
        return fail(message="用户不存在")
    get_task.user_metadatas[str(request.state.user_id)] = update_content.user_metadatas
    get_task.update_at = int(timezone.now().timestamp())  # 改为审核状态
    await get_task.save()
    # update_task = await get_task.update_from_dict(
    #     update_content.model_dump(
    #         exclude_unset=True, exclude={"datasets", "task_datas", "user_metadatas","update_at"}
    #     )
    # )
    # await update_task.save()
    # 序列化
    form_update_task = await task_schema.TaskUpdateResult.from_tortoise_orm(get_task)
    result = form_update_task.model_dump()
    return success(message="更新成功", data=result)


@router.get(
    "/query", summary="过滤用户列表", response_model=task_schema.TaskQueryResponse
)
async def auth_task_query(
    name: str = Query(None),
    desc: str = Query(None),
    data_type: str = Query(None),
    update_at: int = Query(None),
    create_at: int = Query(None),
    limit: int = 10,
    page: int = 1,
    order_by: str = "create_at",
):
    """
    过滤用户
    """
    # 序列化查询参数
    query = {}
    if name:
        query.setdefault("name", name)
    if desc:
        query.setdefault("desc", desc)
    if data_type:
        query.setdefault("data_type", data_type)
    if update_at:
        query.setdefault("email", update_at)
    if create_at:
        query.setdefault("user_type", create_at)
    # 查询结果
    query_data = Tasks.filter(**query).all()
    # 结果总数
    query_total = await query_data.count()
    if not query_total:
        return success(message="查询结果为空!")
    # 分页总数
    page_total = math.ceil(query_total / limit)
    if page > page_total:
        return fail(message="输入页数大于分页总数!")

    # 分页排序
    query_result = query_data.limit(limit).offset(limit * (page - 1)).order_by(order_by)

    form_query_data = await task_schema.TaskQuerySet.from_queryset(query_result)
    # 过滤角色使user['roles']中只包含关联角色的id
    result = form_query_data.model_dump()
    # 序列化查询结果
    result = {
        "result": result,
        "total": query_total,
        "page_total": page_total,
        "page": page,
        "limit": limit,
    }
    return success(message=f"查询成功", data=result)


@router.get(
    "/get/{task_id}", summary="任务数据", response_model=task_schema.TaskGetResponse
)
async def task_annotation_get(
    request: Request,
    task_id: int,
):
    """
    查询用户
    :return:
    """
    # lock.acquire()
    async def get_prefetch_task(get_task,prefetch_count = 5):
        async with lock:
            task_datas = await get_task.task_datas.all()
            tmep_task_data = []
            for task_data in task_datas:
                worker = await task_data.worker

                if worker is None:
                    try:
                        task_data.worker = get_user
                        await task_data.save()
                        
                        tmep_task_data.append(task_data)
                        if len(tmep_task_data) >= prefetch_count:
                            break
                    except Exception as e:
                        print(e)
            return tmep_task_data
    result = []
    try:
        get_user = await AuthUsers.get_or_none(pk=request.state.user_id)
        if not get_user:
            return fail(message="用户不存在")
        get_task = await Tasks.get_or_none(pk=task_id)
        if not get_task:
            return fail(message="任务不存在")
        format_task = await task_schema.TaskGetResult.from_tortoise_orm(get_task)
        task = format_task.model_dump(exclude={"datasets": {"files"},"task_datas":False})
        task_datas = await get_task.task_datas.filter(worker=get_user).all() # 过滤出当前用户的任务数据
        if task_datas is None:
            task_datas = await get_prefetch_task(get_task,5)
            
        task_datas = [await anntation_schema.Task_datasGetResult.from_tortoise_orm(item) for item in task_datas]
        task["task_datas"] = [item.model_dump(exclude_unset=True, exclude={"file_info": {"datasets"},"task": {"datasets":{"files"},"user_metadatas":{}},}) for item in task_datas] # 返回单独的任务注释数据

        task["user_metadatas"] = task["user_metadatas"].get(
            str(get_user.id), {}
        ) # 获取用户当前任务数据进度
        result = task
        if isinstance(get_task.user_metadatas,dict): # 过滤出当前用户的任务数据
            if get_task.user_metadatas.get(str(get_user.id), None) is None:
                get_task.user_metadatas[str(get_user.id)] = {}
            if get_task.user_metadatas[str(get_user.id)].get("current_view_index",None) is None:
                get_task.user_metadatas[str(get_user.id)]["current_view_index"] = 0
            await get_task.save()
    except Exception as e:
        logger.exception(e)
        pass
            # 释放锁
            # lock.release()
    return success(message="任务查询成功", data=result)


@router.get("/list", summary="数据集列表", response_model=task_schema.TaskQueryResponse)
async def task_list():
    """
    数据集列表
    """

    # 查询结果
    query_data = Tasks.all().order_by("id")
    # 序列化查询结果
    form_query_data = await task_schema.TaskQuerySet.from_queryset(query_data)
    result = form_query_data.model_dump(exclude={"datasets": {"files"}})
    data = {
        "result": result,
    }
    return success(message="查询成功", data=data)
