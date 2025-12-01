from pathlib import Path
import numpy as np


def load_video(video_path):
    import cv2

    cap = cv2.VideoCapture(video_path)
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)

    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return np.array(frames), fps


def load_image(image_path):
    import cv2
    image = cv2.imread(str(image_path))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


def auto_load_file(path: str | Path, default_fps: float = 30.0):
    path = Path(path)
    if path.suffix.lower() in ('.mp4', '.avi', '.mov', '.mkv'):
        return load_video(path)
    elif path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff'):
        image = load_image(path)
        return image[np.newaxis, ...], default_fps  # Add batch dimension for consistency
    elif path.suffix.lower() == '.npy':
        data = np.load(path)
        if data.ndim == 2:
            # Assume grayscale image, convert to RGB BHWC
            data = data[np.newaxis, ..., np.newaxis]
        elif data.ndim == 3:
            data = data[np.newaxis, ...]
        else:
            raise ValueError(f"Unsupported .npy data shape: {data.shape}")

        largest_dims = sorted(data.shape[1:])[-2:]
        if min(largest_dims) <= 4:
            print(f"Warning: The loaded .npy data has very small spatial dimensions {largest_dims}. Assuming channel-last format.")
            channel_axis = -1
        else:
            channel_axis = 1 if data.shape[1] in (1, 3, 4) else -1

        if data.shape[channel_axis] == 1:
            data = data.repeat(3, axis=channel_axis)
        elif data.shape[channel_axis] == 2:
            # Pad to 3 channels with 0s
            data = np.concatenate(
                [data, np.zeros(data.shape[:channel_axis] + (1,) + data.shape[channel_axis + 1:], dtype=data.dtype)],
                axis=channel_axis
            )
        elif data.shape[channel_axis] == 4:
            # For now, discard alpha channel
            data = data.take(indices=[0, 1, 2], axis=channel_axis)

        return data, default_fps
    else:
        raise ValueError("Unsupported file format")
