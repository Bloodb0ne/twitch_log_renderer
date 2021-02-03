import skia
from .helpers.skia_rendering import skia_canvas
from .chat_messages import ChatMessage
from .helpers.drawing_options import DrawingOptions
from .colors import strToHexList
from .node_types import TextNode,LinkNode,MentionNode,BadgeNode,CheermoteNode,EmoteNode

class ImagedChatMessage():
	'''
		Encapsulates a chat message that can be rendered to an image
	'''
	def __init__(self,message:ChatMessage,width:int,dOptions:DrawingOptions,timestamped = False):
		self.msg = message
		self.timestamped = timestamped
		self.width = width
		
		self.drawOptions = dOptions
		self.lh = self.drawOptions.line_height
		self.scale = self.drawOptions.image_scale
		# Any other way specify this
		self.fade = 0
		self.shouldDelete = False
		# Fading
		self.endFade = None
		self.startFade = None
		
		self.fitToWidth()  #measures nodes to add positional information
		
		self.has_animated_nodes = any([node.isAnimated for node in self.msg.nodes])
		self.height = self.lheight * self.lh
		self.rect = skia.Rect.MakeXYWH(0,0,self.width,self.height)
		self.snapshot_ = None
	
	def isAnimated(self):
		return self.has_animated_nodes
	
	def animationDuration(self):
		animated = [anode for anode in self.msg.nodes if isinstance(anode,EmoteNode) or isinstance(anode,CheermoteNode)]
		return sum([node.image.tDuration for node in animated],0)
		

	def snapshot(self,ms = 0):
		''' Create an image snapshot of the chat message at a certain time'''
		if not self.snapshot_ or self.isAnimated():
			with skia_canvas(self.width,self.height) as canvas:
				if self.msg.isSubscription():
					self.drawOptions.drawBackgroundSub(canvas,self.msg.index % 2,self.rect)
				elif self.msg.isHighlightedNotice():
					self.drawOptions.drawBackgroundHighlighted(canvas,self.msg.index % 2,self.rect)
				else:
					self.drawOptions.drawBackground(canvas,self.msg.index % 2,self.rect)
					
				#draw custom backgrounds for highlight and sub messages
				self.render(canvas,ms)
				self.snapshot_ = canvas.getSurface().makeImageSnapshot()
		return self.snapshot_
	
	def renderNode(self,node,canvas,pos = skia.Point(0,0),line=0,msec = 0):
		if isinstance(node,TextNode):
			
			if node.stype == 'username':
				canvas.drawTextBlob(node.text_blob, pos.x(),line+pos.y(),self.drawOptions.usrPaint)
			elif node.stype == 'timestamp':
				canvas.drawTextBlob(node.text_blob, pos.x(),line+pos.y(),self.drawOptions.tstampPaint)
			else:
				canvas.drawTextBlob(node.text_blob, pos.x(),line+pos.y(),self.drawOptions.txtPaint)

		elif isinstance(node,LinkNode):
			canvas.drawTextBlob(node.text_blob, pos.x(),line+pos.y(),self.drawOptions.txtPaint)
		elif isinstance(node,MentionNode):
			canvas.drawTextBlob(node.text_blob, pos.x(),line+pos.y(),self.drawOptions.txtPaint)
		elif isinstance(node,CheermoteNode):
			node.image.seek(msec)
			frame = node.image.getFrame()
			self.drawOptions.drawScaledImage(frame,self.scale,line,pos,canvas)
		elif isinstance(node,BadgeNode):
			node.image.seek(msec)
			frame = node.image.getFrame()
			self.drawOptions.drawScaledImage(frame,self.scale,line,pos,canvas)
		elif isinstance(node,EmoteNode):
			node.image.seek(msec)
			frame = node.image.getFrame()
			self.drawOptions.drawScaledImage(frame,self.scale,line,pos,canvas)
	
		
	def render(self,canvas,ms):
		#Mid position
		mline = self.lh/2 + self.drawOptions.spacer/4
		midline = round(mline)
		textMidline = round(mline + 2)
		
		#Draw timestamp
		if self.timestamped:
			self.renderNode(self.msg.ftimestamp,canvas,self.timestampPos,textMidline,ms)
		
		#Draw badges
		for node,pos in zip(self.msg.badges,self.badgePos):
			self.renderNode(node,canvas,pos,midline,ms)
		
		#Draw username
		clr_t = strToHexList(self.msg.user_color)
		self.drawOptions.usrPaint.setColor(skia.ColorSetARGB(0xFF, *clr_t))
	
		# Ability to change font of the caching
		canvas.drawTextBlob(self.msg.username.text_blob, self.usernamePos.x(),textMidline, self.drawOptions.usrPaint)
		
		#Draw content nodes
		for node,pos in zip(self.msg.nodes,self.contentPos):
			self.renderNode(node,canvas,pos,textMidline,ms)
	
	def isVisible(self,time):
		return self.msg.timestamp.isVisible(time)

	def fitToWidth(self):
		if self.msg.isHighlightedNotice():
			offset = 10 #offset the messages so they are not at the edge
		else:
			offset = 5
		x = offset

		# Measure timestamp
		if self.timestamped:
			self.msg.ftimestamp.cache(self.drawOptions)
			self.timestampPos = skia.Point(x,0)
			nl = x + self.msg.ftimestamp.width
			x += nl + 3
		
		# Measure badges
		self.badgePos = []
		for bn in self.msg.badges:
			if not bn: 
				continue #badges might be missing
			bn.cache(self.drawOptions,self.scale)
			self.badgePos.append(skia.Point(x,0))
			x += bn.width + 5
				
		# Cache and Measure username
		self.msg.username.text += ": "
		self.msg.username.cache(self.drawOptions)
		self.usernamePos = skia.Point(x,0)
		x += self.msg.username.width
		# Measure message content
		line = 1
		self.contentPos = []
		
		for n in self.msg.nodes:
			# Cache node
			n.cache(self.drawOptions,scale=self.scale)  # what scale
			oX = 0
			oY = 0
			nl = n.width
			
			#This should be a nice solution to new line handling
			if x + nl > self.width or (hasattr(n,'newline') and n.newline):
				line += 1
				oX = offset
				x = nl
			else:
				oX = x + offset
				x += nl

			oY = (line-1)* self.lh
			self.contentPos.append(skia.Point(oX,oY))
		self.lheight = line
