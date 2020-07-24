import skia
import html
import requests
from .animated_image import AnimatedImage
from .skia_rendering import shapeStringToSkBlob

class TextBlobCache:
	assets = {}
	def add(hash,value):
		TextBlobCache.assets[hash] = value
	
	def get(hash):
		return TextBlobCache.assets.get(hash,False)

	def cache(txt,font,font_manager,multi_run = False):
		txt = html.unescape(txt)
		if not TextBlobCache.assets.get(txt,False):
			if multi_run:
				txtBlob,width = shapeStringToSkBlob(txt,font,font_manager)
			else:
				txtBlob = skia.TextBlob.MakeFromString(txt, font)
				width = font.measureText(txt)
			TextBlobCache.add(txt,(txtBlob,width))
		return TextBlobCache.get(txt)
	
class ImageCache:
	assets = {}
	def add(hash,value):
		ImageCache.assets[hash] = value
	
	def get(hash):
		return ImageCache.assets.get(hash,False)
	
	def cache(path):
		if not ImageCache.assets.get(path,False):
			#handle local data paths? (already part of  AnimatedImage)
			try:
				r = requests.get(path)
			except Exception as e:
				raise ValueError('Failed to fetch image from url: %s' %path)
			skImg = AnimatedImage(r.content)
			ImageCache.add(path,skImg)
		return ImageCache.get(path)
