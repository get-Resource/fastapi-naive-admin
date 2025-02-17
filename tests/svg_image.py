import cv2
from nicegui import app, ui
from core.NiceguiWeb import components


async def svg_events(e):
    element_id = e.args.get("element_id")
    javascript = f" document.getElementById('{element_id}');"
    print(javascript)
    element = await ui.run_javascript(javascript, timeout=5.0)
    # print(e)


@ui.page("/")
def page():
    interactive_image = components.InteractiveCanvas(
        "https://picsum.photos/id/565/640/360",
        cross=True,
        content="""
    """,
    ).on("svg:pointerdown", svg_events)


ui.run(port=1080)
