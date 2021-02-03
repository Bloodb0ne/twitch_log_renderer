import json
import datetime
import argparse
import os
import re
import numpy as np
import itertools
from .parsers import LogParser
from .rendering import HTMLRenderer, VideoRenderer,ImageRenderer
from .cachers import BadgeCache, CheermoteCache, Emote
from .providers import BTTV, FFZ, Twitch, User, Cheermotes, Badges

from . import arg_helpers
from . import image_arg_opts
from . import video_arg_opts


def getParserOptionals(parser):
	return [
		key.option_strings 
		for key in parser._actions 
		if isinstance(key,argparse._StoreTrueAction)
	]

def prepareLog(args):
	channel_ids = User.convertToUserIDs(args.channel, args.db_path)
	# Load assets
	theme = 'Dark'
	animated = True
	scale = 1.0
	
	Emote.databasePath = args.db_path
	BadgeCache.databasePath = args.db_path
	CheermoteCache.databasePath = args.db_path
	
	BadgeCache.update(channel_ids[0],1)
	CheermoteCache.update(channel_ids[0], scale, animated, theme)
	
	# Parse Log, needs a better name
	msgs = LogParser.parse(args.input_file)

	# Filter messages by time
	nStart,nEnd = arg_helpers.transformTimeRange(
		msgs.minTime, 
		msgs.maxTime, 
		args.start, 
		args.end)
	
	msgs.filterByDateRange(start_date=nStart, end_date=nEnd)
	msgs.removeSubMessages(args.hide_sub_msg)

	if args.include_timestamps:
		msgs.addFormattedTimestamps(args.timestamp_format)
	
	return msgs

def main():
	parser = argparse.ArgumentParser(add_help=True,
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="""
	Download and render twitch logs to different output formats
	the whole process uses a database to store information about assets
	such as emotes,cheermotes,badges that can easily be downloaded based on 
	channel names. Twitch logs ( those associated with VODs ) do not require the 
	download of all twitch emotes because they are described in the log
	Raw Logs captured by third parties require the download of all twitch emotes to
	be rendered.

	\033[1m Downloading assets: \033[0m
		All commands require a database specified by the --database flag, specifying
		a file for the database, if the file does not exist the database structure will be created
		automatically.
		\033[1mUsage:\033[0m
		Downloading all emotes/cheermotes/badges ( including global) to the database file emotes.db
			\033[1m download emotes \033[92mtwitch ffz bttv\033[0m --global --database \033[92memotes.db\033[0m --channel \033[92mforsen nymn \033[0m
		For additional help use:
			\033[1m download emotes --help \033[0m

	\033[1m Downloading Twitch VOD logs: \033[0m
		Interface to download the chat replay logs from a vod
		\033[1m download log \033[92m<vod>\033[0m --output \033[92mchat_log.json \033[0m
		Where <vod> can be just the ID of the vod or the whole url
		Example values:
			\033[1mhttps://www.twitch.tv/videos/12345678
			www.twitch.tv/videos/12345678
			twitch.tv/videos/12345678
			12345678\033[0m
	
	\033[1m Rendering: \033[0m

		Render to html:

			Create a HTML document based on a template that includes styling.
			Default template is provided, but a custom template file can be supplied
			Check the documentation on how to create a custom template.
			\033[1m html --help\033[0m

		Render to video 🎞️:

			Create a full video based on timestamps in the log
			\033[1m video --help\033[0m

		Render to image:

			Create a snapshot of chat, can be a static or animated to preserve
			animated gif emotes. Output formats can be a gif,webm,png,jpg
			\033[1m image --help\033[0m
	""")

	subparsers = parser.add_subparsers(dest='cli_action')
	downloaders = subparsers.add_parser('download',help='Download emotes or emote data or logs',add_help=True)
	actions = downloaders.add_subparsers(dest='download_action')

	# Emote download options
	emote_download = actions.add_parser("emotes",help="emotes [twitch,bttv,ffz] --database <path_to_database>")
	emote_download.add_argument('provider',
		choices=['twitch','bttv','ffz'],
		nargs='+',
		help='List of providers [twitch,bttv,ffz] non-twitch providers require channel_name/channel_id')
	emote_download.add_argument('--database',
		help='Path to emote database',dest='db_path'
		,required=True)
	emote_download.add_argument('--channel',
		help='Channel Name or Channel ID',dest='channel',nargs='+',default=[])
	emote_download.add_argument('--globals',
		help='Should Global Provider emotes be downloaded',dest='global_emotes',action='store_true')

	# Log download options
	log_downloader = actions.add_parser('log',help="download log <vod_id>")
	log_downloader.add_argument('vod',
		help='VOD ID / VOD URL')
	log_downloader.add_argument('--output',
		required=True,
		help='Destination path for the log file')

	# Log information
	log_inspector = subparsers.add_parser('inspect',help="Show information about a log file")
	log_inspector.add_argument('input_file',help='File path of a log file')


	# Rendering 

	html_render = subparsers.add_parser('html',help="Create an html file from a log",
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="""
		Create a HTML document based on a template that includes styling.
		Default template is provided, but a custom template file can be supplied
		Check the documentation on how to create a custom template.
		\033[1m html --help\033[0m
	""")
	arg_helpers.addDefaultRenderArgs(html_render)

	html_render.add_argument('--template_path',
			help="Path to the template to use for creating the HTML document",
			default=False)

	# Rendering to video
	video_render = subparsers.add_parser('video',help="Create an video file from a log",
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="""
		Create a full video 🎞️  based on timestamps in the log
		\033[1m video --help\033[0m
	""")

	arg_helpers.addDefaultRenderArgs(video_render)
	video_arg_opts.addVideoRenderArgs(video_render)

	#Rendering to image
	image_render = subparsers.add_parser('image',help="Create an image file from a log",
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="""
		Create a snapshot of chat, can be a static or animated to preserve
		animated gif emotes. Output formats can be a gif,webm,png
		\033[1m image --help\033[0m
	""")
	
	image_arg_opts.addImageRenderArgs(image_render)
	arg_helpers.addDefaultRenderArgs(image_render)


	pargs,unknown = parser.parse_known_args()

	#Select flags so we can properly filter them
	#otherwise we cant properly split the arguments
	flags = np.array([getParserOptionals(image_render),
					getParserOptionals(video_render)]).flatten()

	configArgs = None
	if 'config' in pargs and pargs.config:
		configArgs = arg_helpers.mergeConfigOptions(os.sys.argv[1:], pargs.config,flags)

	args = parser.parse_args(configArgs)



	# Clips
	# https://api.twitch.tv/kraken/clips/<slug>

	if args.cli_action == 'download':
		if args.download_action == 'emotes':
			print('Download emotes from', args.provider)
			
			channel_ids = User.convertToUserIDs(args.channel, args.db_path)
			
			if 'twitch' in args.provider:
				if args.global_emotes:
					emotes = Twitch().downloadTwitchEmotes()
					Twitch.emotesToDatabase(emotes, args.db_path)
				# Download cheermotes and badges
				gbadges = Twitch.downloadGlobalBadges()
				Badges.toDatabase(0, gbadges, args.db_path)
				for ch in channel_ids:
					cbadges = Twitch.downloadChannelBadges(ch)
					cheermotes = Twitch().downloadCheermotes(ch)
					Cheermotes.toDatabase(ch, cheermotes, args.db_path)
					Badges.toDatabase(ch, cbadges, args.db_path)
				print('Downloading Twitch emotes')
					
			if 'bttv' in args.provider:
				if args.global_emotes:
					gemotes = BTTV.getBTTVGlobalEmotes()
					BTTV.emotesToDatabase(gemotes, 0, args.db_path)

				for ch in channel_ids:
					emotes = BTTV.getBTTVChannelEmotes(ch)
					BTTV.emotesToDatabase(emotes, ch, args.db_path)

				print('Downloading BTTV emotes')
				
			if 'ffz' in args.provider:
				if args.global_emotes:
					gemotes = FFZ.getFFZGlobalEmotes()
					FFZ.emotesToDatabase(0, gemotes, args.db_path)
				
				for ch in channel_ids:
					emotes = FFZ.getFFZChannelEmotes(ch)
					FFZ.emotesToDatabase(ch, emotes, args.db_path)
				
				print('Downloading FFZ emotes')

		elif args.download_action == 'log':
			vod_id = arg_helpers.getVODIdentifier(args.vod)
			
			try:
				messages = Twitch().downloadVODLog(vod_id)
				if len(messages) == 0:
					raise ValueError("Invalid VOD id selected")
				with open(args.output, mode="w+", encoding='utf-8') as f:
					json.dump(messages, f)
			except Exception as e:
				raise e

	elif args.cli_action == 'html':

		msgs = prepareLog(args)

		# Invoke Renderer
		HTMLRenderer(vars(args)).render(msgs)

	elif args.cli_action == 'video':

		msgs = prepareLog(args)

		# Invoke Renderer
		VideoRenderer(vars(args)).run(msgs)

	elif args.cli_action == 'image':

		msgs = prepareLog(args)

		# Invoke Renderer
		ImageRenderer(vars(args)).run(msgs)
	

	elif args.cli_action == 'inspect':
		# Parse without emotes
		msgs = LogParser.parse(args.input_file, True)
		
		print('----------------------------------------------')
		print('Found {0} messages'.format(len(msgs.messages)))
		if msgs.minTime == msgs.maxTime:
			print("Untimed log messages")
		elif len(msgs.messages) > 0:
			print('Start time	', msgs.messages[0].timestamp)
			print('End time	', msgs.messages[-1].timestamp)
			print("Duration	", msgs.maxTime - msgs.minTime)
		print('----------------------------------------------')


if __name__ == '__main__':
	main()
