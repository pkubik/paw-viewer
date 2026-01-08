from pathlib import Path
import logging

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


def same_exr_windows(exr_header) -> bool:
    return np.all(
        np.all(v1 == v2)
        for v1, v2 in zip(exr_header["dataWindow"], exr_header["displayWindow"])
    )


def load_exr(path: str | Path) -> dict:
    import OpenEXR

    exr = OpenEXR.File(str(path))
    exr_header = exr.header()
    if not same_exr_windows(exr_header):
        logging.warning(
            "The EXR file has different dataWindow and displayWindow. Cropping is not implemented."
        )

    view_names = exr_header.get("multiView", [""])
    main_view_name = view_names[0]

    channel_letters = {}
    for spec in exr_header["channels"]:
        match spec.name.split("."):
            case prefix, channel:
                channel_letters.setdefault(prefix, []).append(channel)
            case channel:
                channel_letters.setdefault(main_view_name, []).append(channel)

    images = {}
    for name, view in exr.channels().items():
        match name.split("."):
            case prefix, channels:
                if channels != "".join(channel_letters[prefix]):
                    logging.warning(f"Skipping incomplete EXR channel {name}")
                    continue
                images[prefix] = view.pixels
            case (prefix_or_channels,):
                if prefix_or_channels in view_names:
                    prefix = prefix_or_channels
                    images[prefix] = view.pixels
                else:
                    images[main_view_name] = view.pixels

    images = {
        name: (255 * view ** (1 / 2.2)).clip(0, 255).astype(np.uint8)
        for name, view in images.items()
    }

    return images


def auto_adjust_array(data: np.ndarray) -> np.ndarray:
    """
    Automatically:
        - permute array to THWC format
        - repeat RGB values for grayscale images
        - pad with 0s for 2-channel images
        - add alpha channel if there are less than 4 channels
    """
    if data.ndim == 2:
        # Assume grayscale image, convert to 1HW1
        data = data[np.newaxis, ..., np.newaxis]
    elif data.ndim == 3:
        last_dim_looks_like_channels = data.shape[-1] <= 4
        if last_dim_looks_like_channels:
            # Add batch dim 1: 1HWC
            data = data[np.newaxis, ...]
        else:
            data = data[..., np.newaxis]
    elif data.ndim == 4:
        pass
    else:
        raise ValueError(f"Unsupported .npy data shape: {data.shape}")

    largest_dims = sorted(data.shape[1:])[-2:]
    if min(largest_dims) <= 4:
        print(
            f"Warning: The loaded .npy data has very small spatial dimensions {largest_dims}. Assuming channel-last format."
        )
        channel_axis = -1
    else:
        channel_axis = 1 if data.shape[1] in (1, 3, 4) else -1

    if data.shape[channel_axis] == 1:
        data = data.repeat(3, axis=channel_axis)
    elif data.shape[channel_axis] == 2:
        # Pad to 3 channels with 0s
        padding_shape = list(data.shape)
        padding_shape[channel_axis] = 1
        data = np.concatenate(
            [
                data,
                np.zeros(
                    padding_shape,
                    dtype=data.dtype,
                ),
            ],
            axis=channel_axis,
        )

    # We made sure we have at least 3 channels
    # Now, ensure there is an alpha channel
    if data.shape[channel_axis] == 3:
        # For now, discard alpha channel
        padding_shape = list(data.shape)
        padding_shape[channel_axis] = 1
        data = np.concatenate(
            [
                data,
                255
                * np.ones(
                    padding_shape,
                    dtype=data.dtype,
                ),
            ],
            axis=channel_axis,
        )

    return data.astype(np.uint8)


def auto_load_file(path: str | Path, default_fps: float = 30.0):
    path = Path(path)
    fps = default_fps
    if path.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv"):
        image, fps = load_video(path)
        images = {"": image}
    elif path.suffix.lower() == ".exr":
        images = load_exr(path)
    elif path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
        image = load_image(path)
        image = image[np.newaxis, ...]  # Add batch dimension for consistency
        images = {"": image}
    elif path.suffix.lower() in (".npy", ".npz"):
        image_or_dict = np.load(path)
        if isinstance(image_or_dict, np.ndarray):
            images = {"": image_or_dict}
        else:
            images = image_or_dict
    else:
        raise ValueError("Unsupported file format")

    images = {name: auto_adjust_array(image) for name, image in images.items()}
    return images, fps


def copy_array_to_clipboard(image: np.ndarray):
    # Load dynamically to make it optional
    try:
        import copykitten as ck
    except ImportError:
        print("Failed to load `copykitten`. Make sure to install extra dependencies.")
        return

    if np.issubdtype(image.dtype, np.floating):
        image *= 255
    ck.copy_image(
        image.astype(np.uint8).tobytes(),
        width=image.shape[1],
        height=image.shape[0],
    )
