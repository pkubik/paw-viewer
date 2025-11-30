from paw_viewer.viewer import load_video, show_video_array


def main():
    video, fps = load_video("A:\\Dev\\pyglet.mp4")
    print(f"Video loaded with shape: {video.shape}, FPS: {fps}")
    show_video_array(video, fps=fps)


if __name__ == "__main__":
    main()
