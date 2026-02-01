import argparse
import logging

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
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (e.g., -v, -vv, -vvv)",
    )
    args = parser.parse_args()

    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname).1s] %(message)s")

    videos, fps = auto_load_file(args.file)
    print(f"Loaded frames with {int(fps)}fps and shapes:")
    for name, video in videos.items():
        print(f"  {name or '<unnamed>'}: {video.shape}")

    show_video_arrays(
        videos,
        fps=args.fps if args.fps is not None else fps,
        outputs_root=args.outputs_root,
    )


if __name__ == "__main__":
    main()
