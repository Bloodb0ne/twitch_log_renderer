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
		
		self.height = self.lheight * self.lh
		self.rect = skia.Rect.MakeXYWH(0,0,self.width,self.height)
		self.snapshot_ = None
		# Snapshot should be created on demand for speed ?
	
	def isAnimated(self):
		return any([node.isAnimated for node in self.msg.nodes])
	
	def snapshot(self,ms = 0):
		''' Create an image snapshot of the chat message at a certain time'''
		if not self.snapshot_ or self.isAnimated():
			with skia_canvas(self.width,self.height) as canvas:
				self.drawOptions.drawBackground(canvas,self.msg.index % 2,self.rect)
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
		midline = self.lh/2 + self.drawOptions.spacer/4
		
		#Draw timestamp
		if self.timestamped:
			self.renderNode(self.msg.ftimestamp,canvas,self.timestampPos,midline,ms)
		
		#Draw badges
		for node,pos in zip(self.msg.badges,self.badgePos):
			self.renderNode(node,canvas,pos,midline,ms)
		
		#Draw username
		clr_t = strToHexList(self.msg.user_color)
		self.drawOptions.usrPaint.setColor(skia.ColorSetARGB(0xFF, *clr_t))
		
		# Ability to change font of the caching
		canvas.drawTextBlob(self.msg.username.text_blob, self.usernamePos.x(),midline, self.drawOptions.usrPaint)
		
		#Draw content nodes
		for node,pos in zip(self.msg.nodes,self.contentPos):
			self.renderNode(node,canvas,pos,midline,ms)
	
	def isVisible(self,time):
		return self.msg.timestamp.isVisible(time)

	def fitToWidth(self):
		x = 0

		# Measure timestamp
		if self.timestamped:
			self.msg.ftimestamp.cache(self.drawOptions)
			self.timestampPos = skia.Point(0,0)
			nl = self.msg.ftimestamp.width
			x += nl + 5
		
		# Measure badges
		self.badgePos = []
		for bn in self.msg.badges:
			bn.cache(self.drawOptions,self.scale)
			self.badgePos.append(skia.Point(x,0))
			x += bn.width + 3
				
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
			
			if x + nl > self.width:
				line += 1
				oX = 0
				x = nl
			else:
				oX = x
				x += nl

			oY = (line-1)* self.lh
			self.contentPos.append(skia.Point(oX,oY))
		self.lheight = line
