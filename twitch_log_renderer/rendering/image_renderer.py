import ffmpeg
import skia
import contextlib
import re
import os
import subprocess
import datetime
import math
import codecs
import html
import numpy as np
from tqdm import tqdm
from ..node_types import TextNode,EmoteNode,LinkNode,MentionNode,CheermoteNode,BadgeNode
from ..helpers.animated_image import AnimatedImage
from ..helpers.skia_rendering import skia_canvas,shapeStringToSkBlob
from ..helpers.ffmpeg_image import ffmpeg_image_pipe
from ..helpers.ffmpeg_video import ffmpeg_output_pipe
from ..helpers.drawing_options import DrawingOptions

from ..imaged_chat_message import ImagedChatMessage

def linesHeight(lines,full = False):
	if full:
		return sum([line.lheight for line in lines],0)
	else:
		return sum([line.lheight for line in lines if not line.shouldDelete])

class ImageRenderer:
	defaultOptions = {
		'width': 350,
		'height': 600
	}
	
	def __init__(self,options):
		self.options = {**ImageRenderer.defaultOptions,**options}
		self.chatWidth = self.options['width']
		self.chatHeight = 0
		self.current_frame_msgs = []
		
		self.lineHeight = self.options['line_height']
		self.scale = self.options['image_scale']
		#rendering options
		self.fps = self.options['fps']
		self.frame_dur = 1/self.fps
		
		draw_params = []
		self.drawOptions = DrawingOptions(**self.options)
		
	
		
	def renderSnapshot(self,msg,canvas,ms,line):
		frame = msg.snapshot(ms)
		
		w = frame.width()
		h = frame.height()
		src = skia.Rect.MakeXYWH(0,0,w,h)
		fW = w * msg.fade
		sW = (fW + w)
		sH = (line + h)
		
		dst = skia.Rect(fW,line,sW,sH)
		tempPaint = skia.Paint()
		tempPaint.setFilterQuality(skia.FilterQuality.kHigh_FilterQuality)
		canvas.drawImageRect(frame, src, dst, tempPaint)
	
	def render_frame(self,ms):
		with skia_canvas(self.chatWidth,self.chatHeight) as canvas:
			paint = skia.Paint()
			paint.setStyle(skia.Paint.kFill_Style)
			paint.setColor(self.options['bg'])
			canvas.drawRect(self.frame_rect, paint)

			line = 0
			for msg in self.current_frame_msgs:
				self.renderSnapshot(msg,canvas,ms,line)
				line += msg.lheight * self.lineHeight

			canvas.readPixels(skia.ImageInfo.MakeN32Premul(self.chatWidth,self.chatHeight),self.buffer)
	
	def getEncoders():
		return list(ffmpeg_image_pipe.encoders.keys())

	def getMaxAnimatedDuration(self):
		return sum([node.animationDuration() for node in self.current_frame_msgs if node.isAnimated()])

	def run(self,messages):
		self.current_frame_msgs = []
		width = self.options['width']
		outfile = self.options['output_file']
		# Define placeholder image for failed emotes and issue warnings about them
		trackedMessages = tqdm(messages.messages,unit='msg',unit_scale=True,desc='\033[92mPreparing\033[0m')
		self.chat_messages = [ImagedChatMessage(msg,width,self.drawOptions,self.options['include_timestamps']) for msg in trackedMessages]
		#Render them all 
		self.current_frame_msgs = self.chat_messages
		self.chatHeight = linesHeight(self.current_frame_msgs,True) * self.options['line_height'];

		self.buffer = np.zeros((self.chatHeight, self.chatWidth, 4), dtype=np.uint8)
		self.frame_rect = skia.Rect.MakeXYWH(0,0, self.options['width'],self.options['height'])
		
		duration = self.getMaxAnimatedDuration()

		#Simple datetime usage for duration management
		startTime = datetime.datetime.now()
		endTime = startTime + datetime.timedelta(milliseconds=duration)
		ticker = startTime
		deltaMS = 0

		#total duration would be the animation length
		totalMS = int((endTime - startTime) / datetime.timedelta(seconds=1) /self.frame_dur)
		
		
		ffopts = {
			'encoder':self.options['encoder'],
			'transparent':self.options['transparent'],
			'fps': self.fps,
			'quiet': True
		}
		
		renderAnimation = ffmpeg_image_pipe.isAnimatedEncoder(self.options['encoder'])

		if not renderAnimation:
			with ffmpeg_image_pipe(width,self.chatHeight,outfile,**ffopts) as ffproc:
				self.render_frame(deltaMS)
				ffproc.stdin.write(self.buffer.astype(np.uint8).tobytes())
		else:
			with ffmpeg_image_pipe(width,self.chatHeight,outfile,**ffopts) as ffproc:
				videoProgress = tqdm(total=totalMS,unit='frame',unit_scale=True,desc='\033[92mRendering\033[0m')
				while True:
					ticker = ticker + datetime.timedelta(seconds=self.frame_dur)
					
					if ticker > endTime: 
						break
					videoProgress.update(1)
					deltaMS = (ticker - startTime) / datetime.timedelta(milliseconds=1)
					self.render_frame(deltaMS)
					ffproc.stdin.write(self.buffer.astype(np.uint8).tobytes())
				videoProgress.close()