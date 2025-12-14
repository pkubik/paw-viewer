from pathlib import Path

VERTEX_SHADER_PATH = Path(__file__).parent / "vertex.glsl"
FRAGMENT_SHADER_PATH = Path(__file__).parent / "fragment.glsl"
SLIDER_VERTEX_SHADER_PATH = Path(__file__).parent / "slider_vertex.glsl"
SLIDER_FRAGMENT_SHADER_PATH = Path(__file__).parent / "slider_fragment.glsl"
QUAD_INDICES = (0, 1, 2, 0, 2, 3)
QUAD_CORNER_COORDS = (0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0)


def load_shader(name: str) -> str:
    path = Path(__file__).parent / name
    return path.read_text()


def load_vertex_shader():
    return VERTEX_SHADER_PATH.read_text()


def load_fragment_shader():
    return FRAGMENT_SHADER_PATH.read_text()


def load_slider_vertex_shader():
    return SLIDER_VERTEX_SHADER_PATH.read_text()


def load_slider_fragment_shader():
    return SLIDER_FRAGMENT_SHADER_PATH.read_text()


def create_quad(x, y, width, height):
    x1 = -width / 2 + x
    y1 = -height / 2 + y
    x2 = width / 2 + x
    y2 = height / 2 + y
    return x1, y1, x2, y1, x2, y2, x1, y2


def create_quad_from_texture(texture):
    return create_quad(0, 0, texture.width, texture.height)
