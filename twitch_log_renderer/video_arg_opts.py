from . import arg_helpers
from .rendering.video_renderer import VideoRenderer

def addVideoRenderArgs(video_render):
	video_render.add_argument('--transparent',
			action='store_true',
			help='Should the output encode transparency(if the codec doesnt support it creates a second video as a alpha mask)')
	video_render.add_argument('--encoder',
			choices=VideoRenderer.getEncoders(),
			default='h264',
			help='Encoder to use for the resulting video')
	video_render.add_argument('--width',
			default='350',
			type=int,
			help='Width of the video')
	video_render.add_argument('--height',
			default='600',
			type=int,
			help='Height of the video')
	video_render.add_argument('--fps',
			default='25',
			type=float,
			help='Framerate of the resulting video')
	video_render.add_argument('--line_height',
			default='26',
			type=int,
			help='Height of a chat line (not the whole message)')
	video_render.add_argument('--image_scale',
			default='1',
			type=arg_helpers.norm_float,
			help='Scale of images from [0,1]')
	video_render.add_argument('--txt_font',
			default='Arial',
			help='Font name of the text in the message')
	video_render.add_argument('--txt_color',
			default='#FFFFFF',
			type=arg_helpers.hex_color,
			help='Color of the text portion of the message')
	video_render.add_argument('--txt_font_size',
			default=12,
			type=float,
			help='Font size of the text elements')
	video_render.add_argument('--tstamp_color',
			default='#FFFFFF',
			type=arg_helpers.hex_color,
			help='Color of the timestamp of the message')
	video_render.add_argument('--uname_font',
			default='Arial',
			help='Font name of the usernames')
	video_render.add_argument('--uname_font_size',
			default=12,
			type=float,
			help='Font size of the usernames')
	video_render.add_argument('--bg',
			default='#FF000000',
			type=arg_helpers.hex_color,
			help='Chat background')
	video_render.add_argument('--even_bg',
			default='#222222',
			type=arg_helpers.hex_color,
			help='Message background of even messages')
	video_render.add_argument('--odd_bg',
			default='#18181B',
			type=arg_helpers.hex_color,
			help='Message background of even messages')
	video_render.add_argument('--sub_even_bg',
			default='#5C3773',
			type=arg_helpers.hex_color,
			help='Subscription Message background of even messages')
	video_render.add_argument('--sub_odd_bg',
			default='#613C78',
			type=arg_helpers.hex_color,
			help='Subscription Message background of even messages')
	video_render.add_argument('--highlight_bg_color',
			default='#2F214A',
			type=arg_helpers.hex_color,
			help='Message background of highlighted messages')
	video_render.add_argument('--highlight_sidebar_color',
			default='#8F49FF',
			type=arg_helpers.hex_color,
			help='Side background of highlighted messages')
	video_render.add_argument('--hide_sub_msg',
			action='store_true',
			help='Removes sub/subgift/resub messages (only twitchlog)')
	
	video_render.add_argument('--fadeout',
			default='1',
			type=arg_helpers.norm_float,
			help='Sets how fast a message fades (value 1 means it instantly fades)')