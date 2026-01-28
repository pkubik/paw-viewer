# paw-viewer
A simple pyglet image viewer - a base for hacking out custom ndarray visualizations.

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
Click and drag the label up-right/left-down to increase/decrease the value.

## Notes

- There is not way to select a time range for now,
  so we always save [current frame, current frame + 8] as videos.
- Viewer itself accept both `uint8` and `float` types, because
  unification would be too slow.
