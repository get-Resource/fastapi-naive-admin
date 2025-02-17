#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：login_urls.py
@Author ：Cary
@Date ：2024/2/27 20:10
@Descripttion : ""
"""
from fastapi import APIRouter

from apis.data_task import annotation, annotation_task, datasets

dataRouters = APIRouter()
dataRouters.include_router(datasets.router)
dataRouters.include_router(annotation_task.router)
dataRouters.include_router(annotation.router)
