# paw-viewer
A simple pyglet image viewer - a base for hacking out custom ndarray visualizations.

## Base Usage

There is a CLI with some logic to automatically load and interpret some selected file formats,
such as:
- PNG
- MP4
- EXR (including multi-view)
- NPY - there are some automatic checks to detect channel-first vs. channel-last
- NPZ - a dictionary of numpy arrays

### Quick Start

If you've just downloaded the repo:

```
uv run paw res/bridge480p.mp4
```

If you want to try without installation:

```
uvx --from git+https://github.com/pkubik/paw-viewer.git paw res/bridge480p.mp4
```

If you want to first install the package:

```
pip install git+https://github.com/pkubik/paw-viewer.git
paw res/bridge480p.mp4
```

## API

Use `show_video_array` to run the UI on an arbitrary 4D numpy array:

```
import paw_viewer as paw
array = np.random.rand(10, 256, 256, 4).astype(np.float32)
paw.show_video_array(array)
```

Use `show_video_arrays` to run the UI on a dictionary of 4D numpy arrays:

```
paw.show_video_arrays(
    {
        "original": array,
        "negative": 1. - array,
    }
)
```

## Controls

| Control                       | Action             |
|-------------------------------|--------------------|
| Left‑click + drag<br>**WASD** | Pan the image      |
| Mouse scroll<br>**R/F**       | Zoom in/out        |
| Right-click + drag            | Select crop region |
| Right-click                   | Cancel crop region |
| **Z/X**                       | Prev/next source   |
| **SPACE**                     | Start/stop playback |
| **CTRL+A**<br>**CTRL+D**      | Go to prev/next frame |
| **CTRL+S**                    | Go to start frame  |
| **CTRL+E**                    | Go to end frame    |
| **CTRL+Z**<br>**CTRL+X**      | Go to prev/next source |
| **CTRL+X**                    | Copy cropped region coordinates to clipboard as JSON |
| **CTRL+C**                    | Copy cropped image region to clipboard |
| **CTRL+N**                    | Save croppped region as numpy array (.npy) |
| Click/drag on the slider      | Select frame       |
| **CTRL+Q**                    | Quit               |

### Scalar widgets

Some scalars, like `exposure` and `gamma` are controlled by Blender-like scalar widget.
Click with left mouse button and drag the label up-right/left-down to increase/decrease the value.
Click with right mouse button to reset the scalar to its initial value.

## Notes

- This can actually handle a dictionary of arrays with different sizes,
  but all arrays will be stretched to match the first one.
  This is intended to compare different resolution versions of the same image.
  See `res/demo-multi-size.npz` for reference.
- There is not way to select a time range for now,
  so we always save [current frame, current frame + 8] as videos.
- Viewer itself accept both `uint8` and `float` types, because
  unification would be too slow.
- Numpy default type is `np.float64` (i.e. Python `float`).
  Not sure if there is a way to pass that directly to the shader,
  so you need to convert to `np.float32` first.
