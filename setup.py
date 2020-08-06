from setuptools import setup, find_packages, find_namespace_packages

setup(
	name="twitch_log_renderer",
	version="0.0.2",
	url="https://github.com/Bloodb0ne/twitch_log_renderer/",
	author="bloodb0ne",
	author_email="emilian.branzelov@gmail.com",
	description=("CLI tool for rendering twitch logs into image/video/html."),
	packages=find_packages(),
	package_dir={'twitch_log_renderer':'twitch_log_renderer'},
	entry_points={
		'console_scripts': [
			'twitch_log_renderer = twitch_log_renderer.__main__:main'
		]
	},
	include_package_data=True,
	install_requires=[
		"skia-python >= 85.0",
		"ffmpeg-python",
		"numpy",
		"tqdm"
	]
)
