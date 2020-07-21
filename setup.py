from setuptools import setup, find_namespace_packages

setup(
    name = "twitch_log_renderer",
    version = "0.0.1",
    description = ("CLI tool for rendering twitch logs into image/video/html."),
    packages=find_namespace_packages(include=['twitch_log_renderer.*']),
    install_requires=[
        "skia-python >= 85.0",
        "ffmpeg-python",
        "numpy",
        "tqdm"
    ]
)