#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：Datas_api.py
@Author ：Cary
@Date ：2024/2/8 16:36
@Descripttion : ""
"""

import asyncio
import json
import math
from operator import not_
import os
import shutil
import zipfile,time
from io import BytesIO
from typing import Annotated, Union

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from PIL import Image

from core.Exeption.Response import fail, success
from core.Security.auth_jwt import ws_check_user_jwt
from models.annotation.model import Datasets, File_Infos
from schemas.data_task import dataset_schema
from utils.config import settings
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
import math
import os
from asyncio import Lock
import anyio
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
router = APIRouter(prefix="/datasets")
router_notDepends = APIRouter(prefix="/datasets")
lock = Lock()


@router_notDepends.get("/file_stream", dependencies=None)
async def download_files_stream(
    file_path=Query(),
):
    try:
        upload_dir = settings.STATIC_DIR.joinpath(file_path)
        print(file_path)
        print(upload_dir)

        root, ext = os.path.splitext(file_path)
        if ext in (".jpg", ".png", ".jpg"):
            # if ext != ".webp":
            #     media_type = "image/webp"
            #     # 将图像转换为WebP格式
            #     image_webp = Image.open(str(upload_dir))
            #     # file_like = BytesIO()
            #     # image_webp.save(file_like, format="WEBP")
            #     # tmp_filename = str(upload_dir).replace(ext, ".webp")
            #     # image_webp.save(tmp_filename, format="WEBP")
            #     # file_like = open(tmp_filename, mode="rb")
            #     # os.remove(tmp_filename)
            #     # image_bytes_webp = image_bytes_webp.getvalue()
            #     # logger.warning(str(image_bytes_webp))
            # else:
            media_type = "image/" + ext[1:]
            file_like = open(str(upload_dir), mode="rb")
        elif file_path.endswith(".mp4"):
            media_type = "video/mp4"
        else:
            return {"": 4001}
        return StreamingResponse(file_like, media_type=media_type)
    except FileNotFoundError as e:
        return {str(e): 4001}
    except Exception as e:
        logger.error(e)


@router.post(
    "/add", summary="添加数据集", response_model=dataset_schema.DataCreateResponse
)
async def datasets_add(create_content: dataset_schema.DataCreateRequest):
    """
    创建角色
    :param create_content:
    :return:
    """
    get_Data = await Datasets.get_or_none(name=create_content.name)
    if get_Data:
        return fail(message=f"对象 {create_content.name} 已经存在!")
    # # 创建角色
    add_Data = await Datasets.create(**create_content.model_dump(exclude={"menus"}))
    if not add_Data:
        return fail(message="创建失败!")
    # 序列化返回结果
    form_add_Data = await dataset_schema.DataUpdateResult.from_tortoise_orm(add_Data)
    result = form_add_Data.model_dump()
    # result["menus"] = menus
    return success(message="创建成功!", data=result)


@router.post(
    "/addfiles",
    summary="添加数据集文件",
    response_model=dataset_schema.DataDeleteResponse,
)
async def updataset_file(
    file: Annotated[
        UploadFile,
        File(
            title="文件",
            description="可以多个图像或视频类型文件; 记录打包成一个zip上传,目前只支持 jpg和mp4",
            content_type=["image/*", "video/*", "application/zip"],
        ),
    ],
    data_id: int = Form(...),
):
    """
    添加数据集文件
    :param Data_id:
    :return:
    """
    datasets = await Datasets.get_or_none(pk=data_id)
    if datasets is None:
        return fail(message="数据集不存在")
    # 确保上传目录的存在
    upload_dir = settings.STATIC_DIR.joinpath(
        datasets.name, str(datasets.create_at)
    )  # settings.STATIC_DIR 需要自己创建settings目录并且写入默认路径后导入

    # print(file)
    # 使用zipfile.ZipFile来打开这个file-like object
    if file.filename is None:
        file.filename = str(time.time())
    tmp_file = upload_dir.joinpath(file.filename)
    os.makedirs(str(upload_dir), exist_ok=True)
    with open(str(tmp_file), "a+b") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        with zipfile.ZipFile(str(tmp_file), "r") as z:
            # 遍历zip文件中的所有文件
            for name in z.namelist():
                # 解压文件到当前工作目录
                fileinfo = await File_Infos.get_or_none(name=name)
                if fileinfo is None:
                    relative_path = os.path.join(
                        datasets.name, str(datasets.create_at), name
                    )
                    z.extract(name, str(upload_dir))
                    add_Data = await File_Infos.create(
                        name=name, path=relative_path, datasets=datasets
                    )
        if os.path.exists(str(tmp_file)):
            os.remove(str(tmp_file))
    except zipfile.BadZipFile:
        # 如果不是有效的 ZIP 文件，判断是否为视频或图片
        file_ext = os.path.splitext(file.filename)[1].lower()
        video_extensions = ['.mp4', '.avi', '.mov']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        fileinfo = await File_Infos.get_or_none(name=file.filename)
        if fileinfo is None:

            if file_ext in video_extensions or file_ext in image_extensions:
                relative_path = os.path.join(
                    datasets.name, str(datasets.create_at), file.filename
                )
                # 直接创建文件信息记录
                await File_Infos.create(
                    name=file.filename, path=relative_path, datasets=datasets
                )
            else:
                logger.warning(f"不支持的文件类型: {file.filename}")
        else:
            logger.warning(f"已经存在相同文件名: {file.filename}")
    finally:
        pass
    form_add_Data = await dataset_schema.DataUpdateResult.from_tortoise_orm(datasets)
    result = form_add_Data.model_dump()
    return success(message="添加成功", data=result)


@router.delete(
    "/del/{Data_id}",
    summary="删除数据集",
    response_model=dataset_schema.DataDeleteResponse,
)
async def datasets_del(Data_id: int):
    """
    删除角色
    :param Data_id:
    :return:
    """
    delete_action = await Datasets.filter(pk=Data_id).delete()
    if not delete_action:
        return fail(message="删除失败", data={"id": Data_id})
    return success(message="删除成功", data={"id": Data_id})


@router.get(
    "/query", summary="查询数据集列表", response_model=dataset_schema.DataCreateResponse
)
async def auth_users_query(
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
    query_data = Datasets.filter(**query).all()
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

    form_query_data = await dataset_schema.DataQuerySet.from_queryset(query_result)
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
    "/list", summary="数据集列表", response_model=dataset_schema.DataQueryResponse
)
async def datasets_list():
    """
    数据集列表
    """

    # 查询结果
    query_data = Datasets.all().order_by("id")

    # 序列化查询结果
    form_query_data = await dataset_schema.DataQuerySet.from_queryset(query_data)

    # 过滤菜单使Data[menus]中只包含关联菜单的id
    result = form_query_data.model_dump()
    data = {
        "result": result,
    }
    return success(message="查询成功", data=data)

# region ws         
async def update_user_metadatas_current_index(get_task,user_id,current_index):
    if get_task.user_metadatas.get(str(user_id), None) is None:
        get_task.user_metadatas[str(user_id)] = {}
    get_task.user_metadatas[str(user_id)]["current_view_index"] = current_index
    get_task.update_at = int(timezone.now().timestamp())  # 更新修改时间
    await get_task.save()
    # form_update_task = await task_schema.TaskUpdateResult.from_tortoise_orm(get_task)
    # result = form_update_task.model_dump()
    # return success(message="更新成功", data=result)
    
async def get_prefetch_task(get_user,get_task,prefetch_count = 5):
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
async def get_new_task_data(get_user,get_task):
    task_datas = await get_task.task_datas.filter(worker=get_user).all() # 过滤出当前用户的任务数据
    task_id = get_task.id
    if task_datas is None:
        task_datas = await get_prefetch_task(get_user,get_task,10)
    else:
        not_anntations = [item for item in task_datas if item.status == 0]
        new_number = 10 - len(not_anntations)
        print(not_anntations)
        task_datas = []
        if new_number > 0:
            task_datas = await get_prefetch_task(get_user,get_task,new_number)
            # task_datas.extend(new_task_data)
            
        pass
        
    task_datas = [await anntation_schema.Task_datasGetResult.from_tortoise_orm(item) for item in task_datas]
    task_datas = [item.model_dump(exclude_unset=True, exclude={"file_info": {"datasets"},"task": {"datasets":{"files"},"user_metadatas":{}},}) for item in task_datas] # 返回单独的任务注释数据
    task = {
        "op":"get_task_data",
        "task_id":task_id,
        "task_datas":task_datas,
         
    }
    return task

async def update_annotation(annotation_id,annotation_data):
    regions = annotation_data
    # for annotation in annotation_data:
    #     region = {
    #         "region_attributes":{
    #             "id":annotation["id"],
    #             "obj":annotation["label"],
    #         },
    #         "shape_attributes":{
    #             "name":annotation["type"],
    #         },
    #     }
    #     if annotation["type"] == "rect":
    #         pointList = annotation["pointList"]
    #         x = pointList[0]["x"]
    #         y = pointList[0]["y"]
    #         width = pointList[1]["x"] - x
    #         height = pointList[1]["y"] - y
    #         region["shape_attributes"]["x"] = x
    #         region["shape_attributes"]["y"] = y
    #         region["shape_attributes"]["width"] = width
    #         region["shape_attributes"]["height"] = height
    #     elif annotation["type"] in ["quad","polygon"]:
    #         pointList = annotation["pointList"]
    #         all_points_x = [point["x"] for point in pointList]
    #         all_points_y = [point["y"] for point in pointList]
    #         region["shape_attributes"]["all_points_x"] = all_points_x
    #         region["shape_attributes"]["all_points_y"] = all_points_y
        
    #     regions.append(region)
    await Task_datas.filter(pk=annotation_id).update(annotation=regions,status=1,update_at=int(timezone.now().timestamp()))
    task = {
        "op":"update_annotation",
        "annotation_id":annotation_id,
        "message":"更新成功",
    }
    return task
async def send_task_progress_to_all_channels(task:Tasks):
    task_datas = await task.task_datas.all()
    not_anntations = [item for item in task_datas if item.status == 0] # 没有注释的数据
    not_workers = [item for item in task_datas if item.worker is None] # 没有分配任务的
    total = len(task_datas) # 总任务数量
    not_anntations_number = len(not_anntations) # 没有注释的数据
    progress = total - not_anntations_number # 已完成的任务数量
    undistributed = len(not_workers) # 未分配的任务数量
    print(active_channels)
    for websocket, task_id in active_channels.items():
        if task.id == task_id:  # 确保只向当前任务的频道发送消息
            # 构建消息内容，包含任务进度
            message = {
                "op": "task_progress",
                "task_id": task_id,
                "total": total,
                "progress": progress,
                "undistributed": undistributed,
            }
            print(message)
            # await websocket.send_json(message)
            await websocket.app.state.broadcast.publish(channel="chatroom", message=json.dumps(message))
            # 发送消息到 WebSocket 客户端
    pass
    
# 用于存储所有活跃的频道
active_channels = dict()
# WebSocket 端点，接收 user_id 参数
@router_notDepends.websocket("/ws/{user_id}/{task_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, task_id: int):
    global active_channels
    get_user = await AuthUsers.get_or_none(pk=user_id)
    if not get_user:
        return
        # return fail(message="用户不存在")
    get_task = await Tasks.get_or_none(pk=task_id)
    if not get_task:
        return
    await websocket.accept()
    channel = f"chatroom"  # 为每个用户创建一个独立的频道
    broadcast = websocket.app.state.broadcast
    active_channels[websocket] = task_id  # 将新的频道添加到活跃频道集合中
    try:
        # 创建一个任务组
        async with anyio.create_task_group() as task_group:
            # 定义接收消息的任务
            async def receive_messages():
                async for message in websocket.iter_json():
                    print(message)
                    op = message.get("op")
                    if op == "get_task_data":
                        current_index = message.get("current_index")
                        result = await get_new_task_data(get_user,get_task)
                        await update_user_metadatas_current_index(get_task,user_id,current_index)
                    if op == "update_annotation":
                        annotation_id = message.get("annotation_id")
                        annotation_data = message.get("data")
                        result = await update_annotation(annotation_id,annotation_data)
                    await send_task_progress_to_all_channels(get_task)
                    # 发布消息到广播频道
                    await websocket.send_json(result)
                    # await broadcast.publish(channel=channel, message=message)

            # 定义发送消息的任务
            async def send_messages():
                async with broadcast.subscribe(channel=channel) as subscriber:
                    async for event in subscriber:
                        # 发送消息到 WebSocket 客户端
                        await websocket.send_json(json.loads(event.message))
            # 启动接收和发送消息的任务
            task_group.start_soon(receive_messages)
            task_group.start_soon(send_messages)
    except WebSocketDisconnect:
        logger.error(f"User {user_id} disconnected")
        del active_channels[websocket]  # 用户断开连接时，从活跃频道集合中移除该频道
    finally:
        logger.error(f"User {user_id} disconnected")
        # await websocket.close()