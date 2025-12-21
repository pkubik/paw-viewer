import argparse

from paw_viewer.io import auto_load_file
from paw_viewer.viewer import show_video_arrays


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

    videos, fps = auto_load_file(args.file)
    print(f"Loaded frames with {int(fps)}fps and shapes:")
    for name, video in videos.items():
        print(f"  {name}: {video.shape}")

    show_video_arrays(
        videos,
        fps=args.fps if args.fps is not None else fps,
        outputs_root=args.outputs_root,
    )


if __name__ == "__main__":
    main()
