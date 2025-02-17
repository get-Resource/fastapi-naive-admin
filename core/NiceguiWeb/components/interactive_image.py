from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union, cast

from typing_extensions import Self

from nicegui import optional_features
from nicegui.events import GenericEventArguments, Handler, MouseEventArguments, handle_event
from nicegui.logging import log
from nicegui.dataclasses import KWONLY_SLOTS
from nicegui.elements.image import pil_to_base64
from nicegui.elements.mixins.content_element import ContentElement
from nicegui.elements.mixins.source_element import SourceElement

try:
    from PIL.Image import Image as PIL_Image
    optional_features.register('pillow')
except ImportError:
    pass

@dataclass(**KWONLY_SLOTS)
class MouseEventArgs(MouseEventArguments):
    element_id: str = ""

class InteractiveCanvas(SourceElement, ContentElement, component='interactive_image.vue'):
    CONTENT_PROP = 'content'
    PIL_CONVERT_FORMAT = 'PNG'
    def __init__(self,
                 source: Union[str, Path, 'PIL_Image'] = '', *,  # noqa: UP037
                 content: str = '',
                 size: Optional[Tuple[float, float]] = None,
                 on_mouse: Optional[Handler[MouseEventArguments]] = None,
                 events: List[str] = ['click', 'dblclick','mouseover','mouseout','mousedown','mouseup','mousemove',],  # noqa: B006
                 cross: Union[bool, str] = False,
                 ) -> None:
        """Interactive Image

        Create an image with an SVG overlay that handles mouse events and yields image coordinates.
        It is also the best choice for non-flickering image updates.
        If the source URL changes faster than images can be loaded by the browser, some images are simply skipped.
        Thereby repeatedly updating the image source will automatically adapt to the available bandwidth.
        See `OpenCV Webcam <https://github.com/zauberzeug/nicegui/tree/main/examples/opencv_webcam/main.py>`_ for an example.

        The mouse event handler is called with mouse event arguments containing

        - `type` (the name of the JavaScript event),
        - `image_x` and `image_y` (image coordinates in pixels),
        - `button` and `buttons` (mouse button numbers from the JavaScript event), as well as
        - `alt`, `ctrl`, `meta`, and `shift` (modifier keys from the JavaScript event).

        You can also pass a tuple of width and height instead of an image source.
        This will create an empty image with the given size.

        :param source: the source of the image; can be an URL, local file path, a base64 string or just an image size
        :param content: SVG content which should be overlaid; viewport has the same dimensions as the image
        :param size: size of the image (width, height) in pixels; only used if `source` is not set
        :param on_mouse: callback for mouse events (contains image coordinates `image_x` and `image_y` in pixels)
        :param events: list of JavaScript events to subscribe to (default: `['click']`)
        :param cross: whether to show crosshairs or a color string (default: `False`)
        """
        super().__init__(source=source, content=content)
        self._props['events'] = events[:]
        self._props['cross'] = cross
        self._props['size'] = size
        self.current_shape = "quadrilateral"
        self.current_draw = {
            "draw": False, # 是否绘制状态
            "shape_attributes": {
                "name": "quadrilateral",
                # rect
                "point1": 0,
                "point2": 0,
                "width": 0,
                "height": 0,
                # quadrilateral or polygon  or polyline
                "all_points_x": [],
                "all_points_y": [],
                "cache_point": None,
                # circle
                # point :包括cx，cy
                "cx": 0,
                "cy": 0,
                "r": 0,
                # ellipse :包括cx，cy
                "rx": 0,
                "ry": 0,
                "theta": 0,
            },# x,y,w,h
            "region_attributes": {"shape_id":"shape_draw"}
        }
        self.current_region_attributes_name = "obj"
        self.current_region_attributes_value = "null"
        self.select_region_ids = []

        if on_mouse:
            self.on_mouse(on_mouse)
        self.on_mouse(self.handle_mouse)
        self.on('svg:pointermove', self.handle_mouse) # 移动
        self.on('svg:pointerdown', self.handle_mouse) # 按下
        self.on('svg:pointerup', self.handle_mouse) # 释放
        self.on('svg:pointerover', self.handle_mouse) # 指向
        self.on('svg:pointerout', self.handle_mouse) # 移出
        self.on('svg:pointerenter', self.handle_mouse) # 输入
        self.on('svg:pointerleave', self.handle_mouse) # 移开
        self.on('svg:pointercancel', self.handle_mouse) # 取消
        self.on('svg:pointerclick', self.handle_mouse) # 取消
        # 注释
        self.annotate_shape = []

    def set_source(self, source: Union[str, Path, 'PIL_Image']) -> None:  # noqa: UP037
        return super().set_source(source)

    def on_mouse(self, on_mouse: Handler[MouseEventArguments]) -> Self:
        """Add a callback to be invoked when a mouse event occurs."""
        def handle_mouse(e: GenericEventArguments) -> None:
            args = cast(dict, e.args)
            arguments = MouseEventArgs(
                sender=self,
                client=self.client,
                type=args.get('mouse_event_type', ''),
                image_x=args.get('image_x', 0.0),
                image_y=args.get('image_y', 0.0),
                button=args.get('button', 0),
                buttons=args.get('buttons', 0),
                alt=args.get('altKey', False),
                ctrl=args.get('ctrlKey', False),
                meta=args.get('metaKey', False),
                shift=args.get('shiftKey', False),
            )
            handle_event(on_mouse, arguments)
        self.on('mouse', handle_mouse)
        return self

    async def handle_mouse(self, event: Union[MouseEventArgs,GenericEventArguments]) -> None:
        """_summary_
        点击空白处，则绘制图形
        Args:
            event (Union[MouseEventArgs,GenericEventArguments]): _description_
        """
        # 转为 MouseEventArgs 统一处理
        if isinstance(event, GenericEventArguments):
            args = cast(dict, event.args)
            event = MouseEventArgs(
                sender=self,
                client=self.client,
                type=args.get('mouse_event_type', ''),
                element_id=args.get('element_id', ""),
                image_x=args.get('image_x', 0.0),
                image_y=args.get('image_y', 0.0),
                button=args.get('button', 0),
                buttons=args.get('buttons', 0),
                alt=args.get('altKey', False),
                ctrl=args.get('ctrlKey', False),
                meta=args.get('metaKey', False),
                shift=args.get('shiftKey', False),
            )
        self.current_draw['shape_attributes']["name"] = self.current_shape
        if event.ctrl:
            if event.type in ["pointerup", ] and not self.current_draw['draw'] and event.element_id != "": # 不在绘制状态,在svg上释放，即为选择并按ctrl，可以多选
                self.select_region_ids.append(event.element_id)
                self.update_svg()
        elif event.type in ["pointerup", ] and not self.current_draw['draw'] and event.element_id != "": # 不在绘制状态,在svg上释放，即为选择
            self.select_region_ids = [event.element_id]
            self.update_svg()
            
        elif self.current_shape == 'rect':
            if event.type in ["pointerdown", "mousedown"]: # 鼠标按下
                if not self.current_draw.get('draw', False): # 开始绘制
                    self.current_draw['draw'] = True
                    self.current_draw['shape_attributes']["point1"] = [event.image_x, event.image_y]
            if event.type in ["pointermove", "mousemove","pointerup", "mouseup"]: # 鼠标移动
                if self.current_draw.get('draw', False): # 如果是绘制状态
                    self.current_draw['draw'] = True
                    self.current_draw['shape_attributes']["point2"] = [event.image_x, event.image_y]
                    self.update_svg()
            if event.type in ["pointerup", "mouseup"]: # 鼠标释放
                if self.current_draw.get('draw', False): # 如果是绘制状态
                    shape_attributes = dict(filter(lambda x: x[0] in ["name","point1","point2",], self.current_draw['shape_attributes'].items()))
                    region_attributes = {}
                    region_attributes[self.current_region_attributes_name] = self.current_region_attributes_value
                    self.add_region("rect",shape_attributes,region_attributes)
                    self.current_draw['draw'] = False
                    self.current_draw['shape_attributes']["point2"] = [event.image_x, event.image_y]
        elif self.current_shape in ["quadrilateral","polygon",]:
            if event.type in ["click"]: # 鼠标按下
                if not self.current_draw.get('draw', False): # 开始绘制
                    self.current_draw['draw'] = True
                self.current_draw['shape_attributes']['all_points_x'].append(event.image_x)
                self.current_draw['shape_attributes']['all_points_y'].append(event.image_y)
                if self.current_shape == "quadrilateral" and len(self.current_draw['shape_attributes']['all_points_x']) == 4:
                    shape_attributes = dict(filter(lambda x: x[0] in ["name","all_points_x","all_points_y",], self.current_draw['shape_attributes'].items()))
                    region_attributes = {}
                    region_attributes[self.current_region_attributes_name] = self.current_region_attributes_value
                    self.add_region("quadrilateral",shape_attributes,region_attributes)
                    self.current_draw['draw'] = False
                    self.current_draw['shape_attributes']['all_points_x'] = []
                    self.current_draw['shape_attributes']['all_points_y'] = []
                    self.current_draw['shape_attributes']["cache_point"] = None
                self.update_svg()
            elif event.type in ["pointermove", "mousemove",]: # 鼠标移动
                if self.current_draw.get('draw', False): # 如果是绘制状态
                    self.current_draw['shape_attributes']["cache_point"] = [event.image_x, event.image_y]
                    self.update_svg()

    def add_region(self,name,shape_attributes,region_attributes,shape_id = -1):
        # if name == "rect":
        region_attributes["shape_id"] = str(shape_id)
        annotate_shape = {
            "shape_attributes": shape_attributes,
            "region_attributes": region_attributes
        }
        if shape_id != "temp_draw":
            self.annotate_shape.append(annotate_shape)
            # self.add_region_update(annotate_shape)

    def clear_current_draw(self,) -> None:
        shape_attributes = {
            # rect
            "point1": 0,
            "point2": 0,
            "width": 0,
            "height": 0,
            # quadrilateral or polygon  or polyline
            "all_points_x": [],
            "all_points_y": [],
            "cache_point": None,
            # circle
            # point :包括cx，cy
            "cx": 0,
            "cy": 0,
            "r": 0,
            # ellipse :包括cx，cy
            "rx": 0,
            "ry": 0,
            "theta": 0,
        }
        self.current_draw['shape_attributes'].update(shape_attributes)
    def update_svg(self, ) -> None:

        self.content = ""
        for i,annotate_shape in enumerate(self.annotate_shape):
            annotate_shape["region_attributes"]["shape_id"] = str(i)
            svg = self.gen_svg_content(**annotate_shape)
            self.content += svg
        if self.current_draw['draw']:
            svg = self.gen_svg_content(**self.current_draw)
            self.content += svg

    def gen_svg_content(self,shape_attributes,region_attributes,**kwargs) -> str:
        name = shape_attributes["name"]
        shape_id = region_attributes["shape_id"]
        svg = ""
        if name == "rect":
            stroke = kwargs.get("stroke","yellow")
            font_size = kwargs.get("font-size",20)
            x = min(shape_attributes["point1"][0],shape_attributes["point2"][0])
            x_max = max(shape_attributes["point1"][0],shape_attributes["point2"][0])
            y = min(shape_attributes["point1"][1],shape_attributes["point2"][1])
            y_max = max(shape_attributes["point1"][1],shape_attributes["point2"][1])
            width = x_max - x
            height = y_max - y
            text_y = y - 5
            label = f"{self.current_region_attributes_name}: {self.current_region_attributes_value}"
            svg += f"""
            <g id="{shape_id}">
                <text id="{shape_id}" x="{x}" y="{text_y}" font-family="Times New Roman" font-size="{font_size}" fill="{stroke}" pointer-events="none" user-select="none">{label}</text>
                <rect id="{shape_id}" x="{x}" y="{y}" rx="0" ry="0" width="{width}" height="{height}" fill="none" stroke-width="0.2rem" stroke="{stroke}" pointer-events="all"/>
            </g>
            """
        if name in ["quadrilateral","polygon",]:
            stroke = kwargs.get("stroke","yellow")
            font_size = kwargs.get("font-size",20)
            all_points_x = shape_attributes["all_points_x"][:]
            all_points_y = shape_attributes["all_points_y"][:]
            px = min(all_points_x)
            py = min(all_points_y)
            if shape_attributes.get("cache_point",None) is not None:
                all_points_x.append(shape_attributes["cache_point"][0])
                all_points_y.append(shape_attributes["cache_point"][1])
            points = " ".join([f"{x},{y}" for x,y in zip(all_points_x,all_points_y)])
            text_y = py - 5
            label = f"{self.current_region_attributes_name}: {self.current_region_attributes_value}"
            svg += f"""
            <g id="{shape_id}">
                <text id="{shape_id}" x="{px}" y="{text_y}" font-family="Times New Roman" font-size="{font_size}" fill="{stroke}" pointer-events="none" user-select="none">{label}</text>
                <polygon id="{shape_id}" points="{points}" fill="none" stroke-width="0.2rem" stroke="{stroke}" pointer-events="all"/>
            </g>
"""

        return svg