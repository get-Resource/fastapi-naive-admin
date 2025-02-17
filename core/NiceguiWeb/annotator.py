import logging
from os import remove

from nicegui import app, ui, events
import asyncio
from typing import Optional
from core.NiceguiWeb.api import get_task_api
from core.NiceguiWeb.component import Toggle
from core.NiceguiWeb.svg import svg_content

REGION_SHAPE = {"rect": '', "quadrilateral": '', "polygon": '',"point": '', }


def region_shape_button(*args,**parameter):

    toggle = Toggle(REGION_SHAPE,*args,**parameter).bind_value(app.storage.user,"toggle_value").props("padding=0")
    for i,option in enumerate(toggle._props['options']):
        svg_name = toggle._values[option.get("value")]
        toggle.add_slot(toggle._props['options'][i]["slot"],svg_content[svg_name])
    return toggle

async def init_annotator_storage_variable(task_id):
    """
    初始化注释器变量变量
    """
    # region 仅在当前页面访问期间存储数据。
    # 与存储在app.storage.tab中的数据不同-只要标签保持打开，
    # 它就会在页面更改甚至浏览器重新启动之间保持不变-如果用户关闭浏览器，
    # 重新加载页面或导航到另一个页面，则app.storage.client中的数据将被丢弃
    current_task_data = await get_task_api(task_id)
    if isinstance(current_task_data,dict):
        app.storage.client["current_task_data"] = current_task_data.get("data")

    # endregion
    # region 同一用户的所有选项卡之间共享。
    app.storage.user["current_shape"] = "rect"

    # endregion

async def search(e: events.ValueChangeEventArguments) -> None:
    """Search for cocktails as you type."""
    app.storage.client["ui_search_file"].classes('mt-2', remove='mt-24')  # move the search field up
    app.storage.client["ui_files"].clear()
    # store the http coroutine in a task so we can cancel it later if needed
    running_query = app.storage.client["current_task_data"].get("task_datas",None)
    with app.storage.client["ui_files"]:  # enter the context of the the results row
        for drink in running_query or []:  # iterate over the response data of the api
            ui.label(drink['file_info']['name']).classes('absolute-bottom text-subtitle2 text-center')
            # with ui.image(drink['strDrinkThumb']).classes('w-64'):
            #     ui.label(drink['strDrink']).classes('absolute-bottom text-subtitle2 text-center')
    running_query = None

async def editor_annotator(task_id,access_token,refresh_token,request):
    ui.page_title('梦注释器')
    await init_annotator_storage_variable(task_id)
    try:
        with ui.header(elevated=True).classes('items-center justify-between') as head:
            with head.props("reveal"):
                ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
            ui.label('HEADER')
        with ui.left_drawer(bottom_corner=True).style('background-color: #d7e3f4').props(':breakpoint="500" bordered no-swipe-open no-swipe-close ') as left_drawer:
            ui.label('区域形状')
            shape_rectangle = region_shape_button(on_change=None)

            # create a search field which is initially focused and leaves space at the top
            app.storage.client["ui_search_file"] = ui.input(on_change=search)
            ui_files = app.storage.client["current_task_data"].get("task_datas", None) or []
            base_url = str(app.storage.client["client"].base_url)
            for i,ui_file in enumerate(ui_files):
                ui_files[i]["label"] = ui_file["file_info"]["name"]
                # ui_files[i]["avatar"] = base_url + "data_task/datasets/file_stream?file_path=" + ui_file["file_info"]["path"]
            app.storage.client["ui_fdiles"] = ui.tree(ui_files, on_select=lambda e: ui.notify(e.value)).props("dense no-selection-unset")
            # t.select('A')
            ui.json_editor({'content': {'json': app.storage.client["current_task_data"]}},
                           on_select=lambda e: ui.notify(f'Select: {e}'),
                           on_change=lambda e: ui.notify(f'Change: {e}'))
        with ui.right_drawer(fixed=False).style('background-color: #ebf1fa').props('bordered') as right_drawer:
            ui.interactive_image('https://picsum.photos/id/565/640/360', cross=True, content='''
                <rect id="A" x="85" y="70" width="80" height="60" fill="none" stroke="red" pointer-events="all" cursor="pointer" />
                <rect id="B" x="180" y="70" width="80" height="60" fill="none" stroke="red" pointer-events="all" cursor="pointer" />
            ''').on('svg:pointerdown', lambda e: ui.notify(f'SVG clicked: {e.args}'))

        with ui.footer().style('background-color: #3874c8'):
            ui.label('FOOTER')
    except Exception as e:
        logging.error(e)