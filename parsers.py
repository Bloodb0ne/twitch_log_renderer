import node_types
import codecs
import re
import json
import functools
from tqdm import tqdm
import mmap
import os
from cachers import Emote
from providers.user import User
from chat_messages import ChatMessage,ChatMessageList

# A fast line counter
# Taken from:
# https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python/850962#850962
def get_num_lines(file_path):
	fp = open(file_path, "r+")
	buf = mmap.mmap(fp.fileno(), 0)
	lines = 0
	while buf.readline():
		lines += 1
	return lines

class LogParser:
	
	def parse(input_file,pure_content = False):
		if os.path.splitext(input_file)[1] == '.json':
			msgs = LogParser.twitchlog(input_file,pure_content)
		else:
			msgs = LogParser.rawlog(input_file,pure_content)
		return msgs

	def rawlog(input_file,pure_content = False):
		parsed_messages = ChatMessageList()
		line_splitter = r"^(\[[:\-\d\s]*\])?(\s*#\w*)?\s*([\w\s]*):(.*)$"
		with codecs.open(input_file, encoding='utf-8') as f:
			# print("[Parser] Parsing raw log messages")
			for n,line in enumerate(tqdm(f,total=get_num_lines(input_file),unit='msg',unit_scale=True,desc='\033[92mParsing  \033[0m')):
				if line[0] == '#': continue
				matches = re.search(line_splitter,line)
				timestamp = ""
				
				# We could handle Hosts,Timeouts as special ChatMessages
				# The issue is how to unify the rendering after that
				# 
				if matches is None:
					continue
				if len(matches.groups()) == 4:
					timestamp = matches.group(1)
					channel = matches.group(2)
					username = matches.group(3)
					text = matches.group(4)

				if timestamp:
					timestamp = timestamp.strip("[]")
				offset = 0
				
				msg = ChatMessage(username=username,content=text,timestamp=timestamp,user_color=User.color(username),pure=pure_content)
				parsed_messages.append(msg)
		return parsed_messages

	def twitchlog(input_file,pure_content = False):
		parsed_messages = ChatMessageList()
		with codecs.open(input_file, encoding='utf-8') as f:
			comments = json.loads(f.read())   
			action_messages =0
			#print("[Parser] Parsing twitch log messages")          
			for cmt in tqdm(comments,unit='msg',unit_scale=True,desc='\033[92mParsing  \033[0m'):
				username = cmt['commenter']['display_name']
				text = cmt['message']['body']
				offset = cmt['content_offset_seconds']
				timestamp =  cmt['created_at']

				#drop non chat messages
				if cmt['message']['is_action']:
					action_messages += 1
					continue
				
				#somehow grey names dont have a color LULW
				color = cmt['message'].get('user_color',User.default_user_color)
				emotes = cmt['message']['fragments']
				badges = cmt['message'].get('user_badges',[])
				Emote.toEmoteCache(emotes)
				msg = ChatMessage(timestamp,username,text,color,badges=badges,pure=pure_content)
				
				parsed_messages.append(msg)

		return parsed_messages
