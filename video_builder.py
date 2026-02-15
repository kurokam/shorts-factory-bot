import os
import subprocess

def build_video(image_paths, audio_path, duration_per_scene):
    input_txt = "inputs.txt"

    with open(input_txt, "w") as f:
        for img in image_paths:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_scene}\n")

    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", input_txt,
        "-i", audio_path,
        "-vf", "scale=1080:1920",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "final.mp4"
    ])

    return "final.mp4"
