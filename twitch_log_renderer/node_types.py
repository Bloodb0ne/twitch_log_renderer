import re
from .colors import strToHexList
from .helpers.asset_helpers import TextBlobCache,ImageCache
from .helpers.drawing_options import DrawingOptions
from .providers import BTTV,FFZ,Twitch


class BasicNode(type):
	def __new__(cls,name,bases, d):
		c = super().__new__(cls, name, bases, d)
		c.x = 0
		c.y = 0
		c.width = 0
		c.height = 0
		c.isAnimated = False
		c.stype = None
		return c

class TextNode(metaclass=BasicNode):
	def __init__(self,text,stype = None):
		self.text = text
		self.stype = stype
		self.newline = re.match(r"\u000D|\u000A|\u0085|\u000B|\u000C|\u2028|\u2029",text)
	
	def cache(self,drawOptions:DrawingOptions,**kwargs):
		'''Cache the text blob and measure the text width'''
		# Maybe create Username and Timestamp nodes eliminating this logic
		if self.stype == 'username':
			blob,width = TextBlobCache.cache(self.text,drawOptions.user_font,drawOptions.font_manager,True)
		elif self.stype == 'timestamp':
			blob,width = TextBlobCache.cache(self.text,drawOptions.text_font,drawOptions.font_manager,False)
		else:
			blob,width = TextBlobCache.cache(self.text,drawOptions.text_font,drawOptions.font_manager,True)
		self.width = width
		self.text_blob = blob

class LinkNode(metaclass=BasicNode):
	def __init__(self,txt):
		self.text = txt
	
	def cache(self,drawOptions:DrawingOptions,**kwargs):
		'''Cache the text blob and measure the text width'''
		blob,width = TextBlobCache.cache(self.text,drawOptions.text_font,drawOptions.font_manager,False)
		self.text_blob = blob
		self.width = width

class MentionNode(metaclass=BasicNode):
	def __init__(self,txt):
		self.text = txt
	
	def cache(self,drawOptions:DrawingOptions,**kwargs):
		'''Cache the text blob and measure the text width'''
		blob,width = TextBlobCache.cache(self.text,drawOptions.mention_font,drawOptions.font_manager,True)
		self.text_blob = blob
		self.width = width

class BadgeNode(metaclass=BasicNode):
	def __init__(self,url,title):
		self.url = url
		self.title = title
	
	def cache(self,drawOptions:DrawingOptions,scale = 1):
		'''Load the image and cache it '''
		#TODO: Use a local image cache so we dont do so much requests
		imageFrame = ImageCache.cache(self.url)
		self.isAnimated = imageFrame.isAnimated()
		self.width = imageFrame.imageInfo.width() * scale
		self.image = imageFrame

class CheermoteNode(metaclass=BasicNode):
	def __init__(self,prefix,url,color,amount):
		self.prefix = prefix
		self.url = url
		self.color = color
		self.amount = amount
	
	def cache(self,drawOptions:DrawingOptions,scale = 1):
		'''Load the image and cache it '''
		#TODO: Use a local image cache so we dont do so much requests
		imageFrame = ImageCache.cache(self.url)
		self.isAnimated = imageFrame.isAnimated()
		self.width = imageFrame.imageInfo.width() * scale
		self.image = imageFrame

class EmoteNode(metaclass=BasicNode):
	def __init__(self,tpl):
		self.id = tpl[0]
		self.provider = tpl[1]
		self.path = tpl[2]

	def url(self,scale = 1):
		if self.provider == "TWITCH":
			return Twitch.emoteURL(self.id,scale)
		elif self.provider == "BTTV":
			return BTTV.emoteURL(self.id,scale)
		elif self.provider == "FFZ":
			return FFZ.emoteURL(self.id,scale)
		else:
			return ""
	
	def cache(self,drawOptions:DrawingOptions,scale = 1):
		'''Load the image and cache it '''
		#TODO: Use a local image cache so we dont do so much requests
		imageFrame = ImageCache.cache(self.url())
		self.isAnimated = imageFrame.isAnimated()
		self.width = imageFrame.imageInfo.width() * scale
		self.image = imageFrame
