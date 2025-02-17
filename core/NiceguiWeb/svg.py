from nicegui import app, ui


content = '''<svg viewBox="0 0 32 32" width="32" height="32" fill="none" stroke="red" xmlns="http://www.w3.org/2000/svg">{symbol}</svg>'''
svg_content = {
    "rect": content.format(symbol='''
      <title>矩形区域形状</title>
      <rect width="20" height="12" x="6" y="10" stroke-width="2"></rect>
    '''),
    "circle": content.format(symbol='''
      <title>矩形区域形状</title>
      <circle r="10" cx="16" cy="16" stroke-width="2"></circle>
    '''),
    "ellipse": content.format(symbol='''
      <title>圆形区域形状</title>
          <ellipse rx="12" ry="8" cx="16" cy="16" stroke-width="2"></ellipse>
    '''),
    "polygon": content.format(symbol='''
      <title>多边形区域形状</title>
          <path d="M 15.25,2.2372 3.625,11.6122 6,29.9872 l 20.75,-9.625 2.375,-14.75 z" stroke-width="2"></path>
    '''),
    "quadrilateral": content.format(symbol='''
      <title>四边形区域形状</title>
          <path d="M 15.25,2.2372 3.625,11.6122 6,29.9872 l 20.75,-9.625 z" stroke-width="2"></path>
    '''),
    "point": content.format(symbol='''
      <title>关键点区域形状</title>
          <circle r="3" cx="16" cy="16" stroke-width="2"></circle>
    '''),
    "polyline": content.format(symbol='''
      <title>多段线区域形状</title>
          <path d="M 2,12 10,24 18,12 24,18" stroke-width="2"></path>
          <circle r="1" cx="2" cy="12" stroke-width="2"></circle>
          <circle r="1" cx="10" cy="24" stroke-width="2"></circle>
          <circle r="1" cx="18" cy="12" stroke-width="2"></circle>
          <circle r="1" cx="24" cy="18" stroke-width="2"></circle>
    '''),
}

