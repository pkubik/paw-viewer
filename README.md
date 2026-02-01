# paw-viewer
A simple pyglet image viewer - a base for hacking out custom ndarray visualizations.

<img width="1060" height="499" alt="image" src="https://github.com/user-attachments/assets/74ed7c65-0ce7-4208-b6de-759d4b759dff" />

**Features**:
- Loading and displaying images and videos in popular formats
- Zoom with nearest neighbor interpolation
- Video playback with precise control
- Easy switching between multiple sources, e.g. your algorithm outputs and reference images
- Selecting regions for extracting cropped data to clipboard or a file
   - This includes small JSON text with crop definition (for use in QA automation configs)
- Controlling exposure and gamma
- Easy Python API for passing `numpy` arrays

### Video playback controls

<img width="1131" height="183" alt="image" src="https://github.com/user-attachments/assets/33c2a249-8800-4c1a-808b-1af944d79d77" />

### Multi-source files

<img width="962" height="293" alt="image" src="https://github.com/user-attachments/assets/cc85df01-c96c-4777-a8c1-ec89e33a53af" />

<img width="1188" height="354" alt="image" src="https://github.com/user-attachments/assets/157970c2-e14e-47ac-aff2-ddb20e72d373" />

## Core Concepts

This should be familiar to anyone working with computer vision applications.

1. A single image is represented as a multi-dimensional array of shape `[H, W, C]`.
   Once loaded, the viewer provides features like panning, zooming and cropping.
2. A video is a sequence of images with shape `[T, H, W C]`.
   This adds the time dimension that can be controlled with the slider on the bottom of the window,
   or fine-grained keyboard bindings (see below).
3. Multi-source image/video adds top-level grouping into a dictionary of arrays.
   A list of sources appears on the left and you can switch between them with keybindings.
   We assume that all sources contain matching frames from the sources that we would like to compare.
   For example: you may load an output of two algorithms, zoom into an a problematic region
   and repeatedly switch the sources judge whether there was an improvement.

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

## Python API

Please read the "Core Concepts" before proceeding.

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

The only nuance for the API is that static images are actually represented as 1-frame videos,
so their shape needs to be artificially expanded on the first dimension to match `[1, H, W, C]`.

**Btw. this is Python**

The code is not as simple as I originally imagined it to be, but it's still Python.
You may download and hack it to better match your needs.
That's especially useful if you'd like to format your crop definitions in a specific custom format.

## Controls

| Control                       | Action             |
|-------------------------------|--------------------|
| Left‑click + drag<br>**WASD** | Pan the image      |
| Mouse scroll<br>**R/F**       | Zoom in/out        |
| Right-click + drag            | Select crop region |
| Right-click                   | Cancel crop region |
| **Z/X**                       | Prev/next source   |
| **1/2/3.. 9** (1-9 numbers)   | Go to n-th source  |
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
- Loading 8GB video arrays may be slow, so don't panic if the program hangs for several seconds.
  I'd like to use some worker threads to load most of the frames in the background in the future.
  I recommend using **CTRL+X** for quickly building a list of interesting crops and saving them
  separately for faster access.
- Viewer itself accept both `uint8` and `float` types, because
  unification would be too slow.
- Numpy default type is `np.float64` (i.e. Python `float`).
  Not sure if there is a way to pass that directly to the shader,
  so you need to convert to `np.float32` first.

### On Python

So far I didn't hit any Python-specific limitations with this project.

- The critical code is implemented within C extensions anyway
- Python can totally handle the kinds of updates that I perform every frame, that is,
  intersecting mouse cursor with widget bounding boxes, handling uniforms, etc.
- The playback is stable for ~30fps playback, which is my typical use case,
  but it gets worse for larger values >60fps. I'm still not sure whether the cause is
  the Python even loop or suboptimal use of OpenGL (e.g. I bind a new texture every frame).
- The OpenGL bindings from `pyglet` allow to get deep enough.
  Translating certain C API concepts to Python may be tricky,
  but, surprisingly, that's one of few cases where I could actually rely on Copilot.
