#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

@File ：__init__.py
@Author ：Cary
@Date ：2024/2/12 04:27
@Descripttion : ""
"""
from tortoise import Tortoise

from models.annotation.model import Datasets, File_Infos, Task_datas, Tasks
from models.auth.model import AuthMenus, AuthRoles, AuthUsers
from models.system.model import SystemSettings

Tortoise.init_models(["models"], "models")
