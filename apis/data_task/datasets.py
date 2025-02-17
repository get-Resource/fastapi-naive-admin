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
import shutil
import zipfile
from io import BytesIO
from typing import Annotated, Union

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from PIL import Image

from core.Exeption.Response import fail, success
from models.annotation.model import Datasets, File_Infos
from schemas.data_task import dataset_schema
from utils.config import settings

router = APIRouter(prefix="/datasets")
router_notDepends = APIRouter(prefix="/datasets")


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
            if ext != ".webp":
                media_type = "image/webp"
                # 将图像转换为WebP格式
                image_webp = Image.open(str(upload_dir))
                # file_like = BytesIO()
                # image_webp.save(file_like, format="WEBP")
                tmp_filename = str(upload_dir).replace(ext, ".webp")
                image_webp.save(tmp_filename, format="WEBP")
                file_like = open(tmp_filename, mode="rb")
                # os.remove(tmp_filename)
                # image_bytes_webp = image_bytes_webp.getvalue()
                # logger.warning(str(image_bytes_webp))
            else:
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
    # 确保上传目录的存在
    upload_dir = settings.STATIC_DIR.joinpath(
        datasets.name, str(datasets.create_at)
    )  # settings.STATIC_DIR 需要自己创建settings目录并且写入默认路径后导入

    # print(file)
    # 使用zipfile.ZipFile来打开这个file-like object
    tmp_file = upload_dir.joinpath(file.filename)
    os.makedirs(str(upload_dir), exist_ok=True)
    with open(str(tmp_file), "a+b") as buffer:
        shutil.copyfileobj(file.file, buffer)
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
    os.remove(str(tmp_file))
    # for file in files:
    #     fileinfo = await File_Infos.get_or_none(name=file.filename)

    #     if fileinfo is None:
    #         # 将上传的文件保存到服务本地
    #         path = upload_dir.joinpath(file.filename)
    #         print(path)
    #         with open(str(path), "wb") as f:
    #             # 一次读取1024 * 1024字节，循环读取写入
    #             # for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
    #             f.write(file.file.read())
    #         add_Data = await File_Infos.create(
    #             name=file.filename, path=str(path), datasets=datasets
    #         )
    form_add_Data = await dataset_schema.DataUpdateResult.from_tortoise_orm(datasets)
    result = form_add_Data.model_dump()
    # if not datasets:
    #     return fail(message="删除失败", data={"id": Data_id})
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
    "/query", summary="过滤用户列表", response_model=dataset_schema.DataCreateResponse
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
    # for Data in form_query_data.model_dump():
    #     if Data.get("menus"):
    #         Data["menus"] = [menus["id"] for menus in Data["menus"]]
    #     result.append(Data)

    data = {
        "result": result,
    }
    return success(message="查询成功", data=data)
