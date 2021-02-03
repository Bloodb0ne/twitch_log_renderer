from . import arg_helpers
from .rendering.image_renderer import ImageRenderer

def addImageRenderArgs(image_render):
	image_render.add_argument('--hide_sub_msg',
			action='store_true',
			help='Removes sub/subgift/resub messages (only twitchlog)')
	image_render.add_argument('--transparent',
			action='store_true',
			help='Should the output encode transparency(if the codec doesnt support it creates a second video as a alpha mask)')
	image_render.add_argument('--encoder',
			choices=ImageRenderer.getEncoders(),
			default='png',
			help='Encoder to use for the resulting video')
	image_render.add_argument('--width',
			default='350',
			type=int,
			help='Width of the video')
	image_render.add_argument('--height',
			default='0',
			type=int,
			help='Height of the video')
	image_render.add_argument('--line_height',
			default='26',
			type=int,
			help='Height of a chat line (not the whole message)')
	image_render.add_argument('--image_scale',
			default='1',
			type=arg_helpers.norm_float,
			help='Scale of images from [0,1]')
	image_render.add_argument('--txt_font',
			default='Arial',
			help='Font name of the text in the message')
	image_render.add_argument('--txt_color',
			default='#FFFFFF',
			type=arg_helpers.hex_color,
			help='Color of the text portion of the message')
	image_render.add_argument('--txt_font_size',
			default=12,
			type=float,
			help='Font size of the text elements')
	image_render.add_argument('--tstamp_color',
			default='#FFFFFF',
			type=arg_helpers.hex_color,
			help='Color of the timestamp of the message')
	image_render.add_argument('--uname_font',
			default='Arial',
			help='Font name of the usernames')
	image_render.add_argument('--uname_font_size',
			default=12,
			type=float,
			help='Font size of the usernames')
	image_render.add_argument('--bg',
			default='#FF000000',
			type=arg_helpers.hex_color,
			help='Chat background')
	image_render.add_argument('--even_bg',
			default='#222222',
			type=arg_helpers.hex_color,
			help='Message background of even messages')
	image_render.add_argument('--odd_bg',
			default='#18181B',
			type=arg_helpers.hex_color,
			help='Message background of even messages')
	image_render.add_argument('--sub_even_bg',
			default='#5C3773',
			type=arg_helpers.hex_color,
			help='Subscription Message background of even messages')
	image_render.add_argument('--sub_odd_bg',
			default='#613C78',
			type=arg_helpers.hex_color,
			help='Subscription Message background of even messages')
	image_render.add_argument('--highlight_bg_color',
			default='#2F214A',
			type=arg_helpers.hex_color,
			help='Message background of highlighted messages')
	image_render.add_argument('--fps',
			default='25',
			type=float,
			help='Framerate of the resulting GIF')