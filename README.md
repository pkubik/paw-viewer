# paw-viewer
A simple pyglet image viewer - a base for hacking out custom ndarray visualizations.

## Controls

| Control                       | Action             |
|-------------------------------|--------------------|
| Left‑click + drag<br>**WASD** | Pan the image      |
| Mouse scroll<br>**R/F**       | Zoom in/out        |
| Right-click + drag            | Select crop region |
| Right-click                   | Cancel crop region |
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
