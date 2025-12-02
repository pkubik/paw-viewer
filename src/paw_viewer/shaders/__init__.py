from pathlib import Path

VERTEX_SHADER_PATH = Path(__file__).parent / "vertex.glsl"
FRAGMENT_SHADER_PATH = Path(__file__).parent / "fragment.glsl"


def load_vertex_shader():
    return VERTEX_SHADER_PATH.read_text()


def load_fragment_shader():
    return FRAGMENT_SHADER_PATH.read_text()
