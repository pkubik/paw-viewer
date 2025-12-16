import argparse

from paw_viewer.io import auto_load_file
from paw_viewer.viewer import show_video_array


def main():
    parser = argparse.ArgumentParser(
        description="Paw Viewer - A simple ndarray image/video viewer"
    )
    parser.add_argument("file", type=str, help="Path to the file")
    parser.add_argument(
        "--fps", type=float, default=None, help="Frames per second for video playback"
    )
    parser.add_argument(
        "-o", "--outputs-root", type=str, default=None, help="Outputs root directory"
    )
    args = parser.parse_args()

    video, fps = auto_load_file(args.file)
    print(f"Loaded frames with shape: {video.shape}, FPS: {fps}")

    show_video_array(
        video,
        fps=args.fps if args.fps is not None else fps,
        outputs_root=args.outputs_root,
    )


if __name__ == "__main__":
    main()
