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
from ..helpers.ffmpeg_video import ffmpeg_output_pipe
from ..helpers.drawing_options import DrawingOptions

from ..imaged_chat_message import ImagedChatMessage

def linesHeight(lines,full = False):
	if full:
		return sum([line.lheight for line in lines],0)
	else:
		return sum([line.lheight for line in lines if not line.shouldDelete])

class VideoRenderer:
	defaultOptions = {
		'width': 350,
		'height': 600
	}
	
	def __init__(self,options):
		self.options = {**VideoRenderer.defaultOptions,**options}
		self.chatWidth = self.options['width']
		self.chatHeight = self.options['height']
		self.buffer = np.zeros((self.chatHeight, self.chatWidth, 4), dtype=np.uint8)
		self.current_frame_msgs = []
		self.rOffset = 0
		self.lineHeight = self.options['line_height']
		self.maxLines = math.floor(self.chatHeight/self.lineHeight)
		self.scale = self.options['image_scale']
		#rendering options
		self.fps = self.options['fps']
		self.frame_dur = 1/self.fps
		self.frame_rect = skia.Rect.MakeXYWH(0,0, self.options['width'],self.options['height'])
		draw_params = []
		self.drawOptions = DrawingOptions(**self.options)
		
	def topLineHeight(self,isTotal = False):
		if len(self.current_frame_msgs) != 0:
			for ind,line in enumerate(self.current_frame_msgs):
				if line.shouldDelete == isTotal:
					return (line.lheight,ind)
		return (0,0)
	
	def isTopFading(self):
		if len(self.current_frame_msgs) != 0:
			return self.current_frame_msgs[0].lheight * self.lineHeight
		return 0
	
	def pushNewMsgs(self,time):
		visibleMessages = [msg for msg in self.chat_messages if msg.isVisible(time)]
		for msg in visibleMessages:
			self.current_frame_msgs.append(msg)
		
		cnt = len(visibleMessages)
		self.chat_messages = self.chat_messages[cnt:]

		return sum([msg.lheight for msg in visibleMessages],0)

	def removeFadedMsgs(self):
		#Increase the fade 
		fading = [msg for msg in self.current_frame_msgs if msg.shouldDelete]
		
		for msg in fading:
			msg.fade += self.options['fadeout']
		
		#Crop the lines
		self.current_frame_msgs = [msg for msg in self.current_frame_msgs if msg.fade >= 0 and msg.fade < 1]

	def removeOutsideMsgs(self,dist,tick_time):
		self.removeFadedMsgs()
		for msg in self.current_frame_msgs:
			if msg.endFade and tick_time >= msg.endFade:
				msg.shouldDelete = True
		
		lnm = linesHeight(self.current_frame_msgs)
		total = abs(self.maxLines - lnm)
		#Offset lines that push current added outside of the frame
		if lnm > self.maxLines:
			inu = self.chatHeight - linesHeight(self.current_frame_msgs) * self.lineHeight
			self.rOffset = abs(inu)
		else:
			self.rOffset = 0
		
		
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
		with skia_canvas(self.options['width'],self.options['height']) as canvas:
			paint = skia.Paint()
			paint.setStyle(skia.Paint.kFill_Style)
			paint.setColor(self.options['bg'])
			canvas.drawRect(self.frame_rect, paint)

			line = 0
			for msg in self.current_frame_msgs:
				self.renderSnapshot(msg,canvas,ms,line-self.rOffset)
				line += msg.lheight * self.lineHeight

			canvas.readPixels(skia.ImageInfo.MakeN32Premul(self.options['width'],self.options['height']),self.buffer)
			
		
	def getEncoders():
		return ffmpeg_output_pipe.getAvailableEncoders()

	def getMessageDuration(self,index,linesLeft):
		for msg in self.chat_messages[index+1:]:
			linesLeft -= msg.lheight
			if linesLeft <= 0:
				return msg.msg.timestamp.chat_time
				#Keeping some comments about delay calc for the future
				# print((msg.endTime - msg.msg.timestamp.chat_time)/ datetime.timedelta(seconds=1))
				#msg.startFade = msg.endTime - datetime.timedelta(seconds=fadeDuration)
	def calculateFadeout(self):
		fadeDuration = 1/self.options['fadeout'] * self.frame_dur
		for ind,msg in enumerate(self.chat_messages):
			linesLeft  = self.maxLines - msg.lheight
			endTime = self.getMessageDuration(ind,self.maxLines)
			if endTime:
				msg.endFade = endTime - datetime.timedelta(seconds=fadeDuration)
			
		
	def run(self,messages):
		self.current_frame_msgs = []
		width = self.options['width']
		height = self.options['height']
		outfile = self.options['output_file']
		# Define placeholder image for failed emotes and issue warnings about them
		trackedMessages = tqdm(messages.messages,unit='msg',unit_scale=True,desc='\033[92mPreparing\033[0m')
		self.chat_messages = [ImagedChatMessage(msg,width,self.drawOptions,self.options['include_timestamps']) for msg in trackedMessages]
		
		self.calculateFadeout()
		
		startTime = messages.minTime
		endTime = messages.maxTime
		ticker = startTime
		deltaMS = 0

		totalMS = int((endTime - startTime) / datetime.timedelta(seconds=1) /self.frame_dur)
		
		
		ffopts = {
			'encoder':self.options['encoder'],
			'transparent':self.options['transparent'],
			'fps': self.fps,
			'quiet': True
		}

		with ffmpeg_output_pipe(width,height,outfile,**ffopts) as ffproc:
			videoProgress = tqdm(total=totalMS,unit='frame',unit_scale=True,desc='\033[92mRendering\033[0m')
			while True:
				ticker = ticker + datetime.timedelta(seconds=self.frame_dur)
				
				if ticker > endTime: 
					break
					
				try:
					deltaMS = (ticker - startTime) / datetime.timedelta(milliseconds=1)
					videoProgress.update(1)
					dist = self.pushNewMsgs(ticker)
					self.removeOutsideMsgs(dist,ticker)
					self.render_frame(deltaMS)
					ffproc.stdin.write(self.buffer.astype(np.uint8).tobytes())
				except Exception as e:
					print(e)
					raise e
		videoProgress.close()
