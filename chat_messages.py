import datetime
import re
import html
import functools
from cachers import WordCache,Emote
from providers.user import User
from node_types import TextNode,EmoteNode,BadgeNode,LinkNode,MentionNode
from cachers import BadgeCache,CheermoteCache
from helpers.skia_rendering import skia_canvas

link_regx = r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w\-_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)"
mention_regx = r"^@\w*$"
def isLink(txt):
	if re.match(link_regx,txt):
		return True
	return False

def isMention(txt):
	if re.match(mention_regx,txt):
		return True
	return False

class Subscriptable(type):
    def __getitem__(cls, x):
        return getattr(cls, x)

    def __new__(cls, name, parents, dct):
        dct["__getitem__"] = cls.__getitem__
        return super().__new__(cls, name, parents, dct)

class ChatTimestamp:
	def __init__(self,time_str):
		#TwitchTimestamp 2020-05-20T15:02:54.18Z
		#RawTimestamp 00:00:09
		#RawTimestamp 2017-05-22 01:01:14
		self.no_date = False
		if not time_str:
			self.chat_time = datetime.datetime.min
		else:
			for fmt in ("%H:%M:%S","%Y-%m-%d %H:%M:%S",'%Y-%m-%dT%H:%M:%SZ','%Y-%m-%dT%H:%M:%S.%fZ'):
				try:
					self.chat_time = datetime.datetime.strptime(time_str, fmt)
					if self.chat_time.year <= 1900:
						self.no_date = True
					break
				except ValueError as e:
					self.chat_time = False
			if not self.chat_time:
				raise ValueError("Timestamp %s is in the wrong format." % time_str)
	
	def __str__(self):
		if self.no_date:
			return str(self.chat_time.time())
		return str(self.chat_time)

	def isVisible(self,time):
		return bool(self.chat_time <= time)

	def isVisibleBetween(self,start_time,end_time):
		return bool(self.chat_time >= start_time) and bool(self.chat_time <= end_time)

def parseBadge(badge):
	# print(badge)
	b = BadgeCache.get(badge['_id'],badge['version'])
	if not b:
		return False
	return BadgeNode(b[0],b[1])

def parseNode(word,isTwitchLog=False):
	if isinstance(word,re.Match): 
		emoteCode = word.group(0)
	else:
		emoteCode = word

	emoteCode = html.escape(emoteCode)
	
	#Ignore already cached words
	word = WordCache.isCached(emoteCode)
	if word:
		return word

	#Add cheermotes
	foundCheermote = CheermoteCache.isCheermote(emoteCode)
	if foundCheermote:
		return WordCache.cache(emoteCode,foundCheermote)

	if( len(emoteCode) < 3): 
		word = WordCache.isCached(emoteCode)
		if word:
			return word
		else:
			return WordCache.cache(emoteCode)
	
	#Ignore already cached emotes
	emote = Emote.isCached(emoteCode)
	if emote:
		return emote
	
	#cache mentions as mention nodes? only @something
	if isMention(emoteCode):
		return WordCache.cache(emoteCode,MentionNode(emoteCode))
	
	#cache link as LinkNode
	if isLink(emoteCode):
		return WordCache.cache(emoteCode,LinkNode(emoteCode))
	
	#cant be an emote only text
	if len(emoteCode) >= 150:
		WordCache.cache(emoteCode)
		return TextNode(emoteCode)
	
	#Dont search for any twitch emote after a certain len
	if len(emoteCode) > 50:
		isTwitchLog = True

	emote = Emote.tryFind(emoteCode,isTwitchLog)
	if emote:
		return Emote.cache(emoteCode,emote)
	else:
		return WordCache.cache(emoteCode)


class ChatMessage(metaclass=Subscriptable):
	'''Chat Message container'''
	def __init__(self,timestamp,username,content,user_color=User.default_user_color,badges=[],nonTwitch = False,pure = False):
		self.timestamp = ChatTimestamp(timestamp)
		self.content = content
		self.user_color = user_color
		self.username = TextNode(username,'username')

		#Ignores searching for Twitch emotes in the log, because we cache them beforehand
		emoteFinder = functools.partial(parseNode,isTwitchLog = not nonTwitch)
		if not pure:
			self.badges = [parseBadge(badge) for badge in badges] 
			elems = re.findall(r"([\d\w\S]*|\s*)",self.content)
			self.nodes = [emoteFinder(x) for x in elems]
	
	def mergeTextNodes(self):
		'''
		Groups adjacent text nodes into a single node, if you want to 😎
		'''
		mergedNodes = list()
		currentText = ""
		for node in self.nodes:
			if isinstance(node,TextNode):
				currentText += node.text
			else:
				mergedNodes.append(TextNode(currentText))
				currentText = ""
				mergedNodes.append(node)
		if len(currentText):
			mergedNodes.append(TextNode(currentText))
		self.nodes = mergedNodes



class ChatMessageList:
	def __init__(self):
		self.messages = []
		self.minTime = datetime.datetime.min
		self.maxTime = datetime.datetime.max

	def len(self):
		return len(self.messages)
	
	def mergeNodes(self):
		for msg in self.messages:
			msg.mergeTextNodes()
	
	def map(self,func):
		for msg in self.messages:
			func(msg)

	def hasTimestamps(self):
		return all([msg.timestamp for msg in self.messages])

	def addFormattedTimestamps(self,frmt):
		if self.hasTimestamps():
			for msg in self.messages:
				time_string = msg.timestamp.chat_time.strftime(frmt)
				msg.ftimestamp = TextNode(time_string,'timestamp')

	def filterByDateRange(self,start_date=datetime.datetime.min,end_date = datetime.datetime.max):
		if self.hasTimestamps():
			if start_date < self.minTime or end_date > self.maxTime:
				raise ValueError('Range outside of message bounds.')
			#Work with only time without the date portion ?
			self.messages = [msg for msg in self.messages 
				if msg.timestamp.isVisibleBetween(start_date,end_date)]

			#Update range dates
			if start_date is not datetime.datetime.min:
				self.minTime = start_date
			
			if end_date is not datetime.datetime.max:
				self.maxTime = end_date

	def append(self,message):
		if isinstance(message,ChatMessage):
			#update time
			if message.timestamp:
				if self.minTime == datetime.datetime.min:
					self.minTime = self.maxTime = message.timestamp.chat_time
				else:
					self.maxTime = message.timestamp.chat_time
			index = len(self.messages)
			message.index = index
			self.messages.append(message)
	
	def front_pop(self):
		if len(self.messages):
			#update time
			self.messages.pop(0)
			self.minTime = self.topMessage().timestamp.chat_time
			return True
		return False
	
	def topMessage(self):
		return self.messages.get(0,False)
	
	def time_range(self):
		return [self.minTime,self.maxTime]