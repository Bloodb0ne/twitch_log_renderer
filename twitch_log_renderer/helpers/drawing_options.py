import skia

class DrawingOptions:
	allowed_opts = ['txt_font','txt_font_size','txt_color','uname_font',
	'uname_font_size','even_bg','odd_bg','line_height','image_scale','tstamp_color',
	'sub_even_bg','sub_odd_bg','sub_txt_color','highlight_bg_color','highlight_sidebar_color','hide_sub_msg']
	def __init__(self,**kwargs):
		#Defaults
		self.txt_font='Arial',
		self.txt_font_size=12.0,
		self.uname_font='Arial',
		self.username_font_size=13.0
		self.even_bg = skia.ColorSetARGB(0xFF, 0x22, 0x22, 0x22)
		self.odd_bg = skia.ColorSetARGB(0xFF, 0x18, 0x18, 0x1B)
		self.txt_color = skia.ColorSetARGB(0xFF, 0xFF, 0xFF, 0xFF)
		#Sub messages
		self.sub_even_bg = skia.ColorSetARGB(0xFF, 0x5C, 0x37, 0x73)
		self.sub_odd_bg = skia.ColorSetARGB(0xFF, 0x61, 0x3C, 0x78)
		self.sub_txt_color = skia.ColorSetARGB(0xFF, 0x85, 0x7F, 0x7D)
		#Highlighted message
		self.highlight_bg_color = skia.ColorSetARGB(0xFF, 0x2F, 0x21, 0x4A)
		self.highlight_sidebar_color = skia.ColorSetARGB(0xFF, 0x8F, 0x49, 0xFF)
		

		self.__dict__.update((k, v) for k, v in kwargs.items() if k in DrawingOptions.allowed_opts)

		self.font_manager = skia.FontMgr.RefDefault()
		self.username_font_style = skia.FontStyle().Bold()
		self.text_font_style = skia.FontStyle().Normal()
		self.user_typeface = self.font_manager.matchFamilyStyle(self.uname_font, self.username_font_style)
		self.text_typeface = self.font_manager.matchFamilyStyle(self.txt_font, self.text_font_style)
		self.mention_typeface = self.font_manager.matchFamilyStyle(self.txt_font, skia.FontStyle().Bold())
		self.text_font = skia.Font(self.text_typeface, self.txt_font_size, 1.0, 0.0)
		self.text_font.setSubpixel(True)
		self.text_font.setHinting(skia.FontHinting.kFull)
		self.text_font.setEdging(skia.Font.Edging.kAntiAlias)
		self.mention_font = skia.Font(self.mention_typeface, self.txt_font_size, 1.0, 0.0)
		self.user_font = skia.Font(self.user_typeface, self.uname_font_size, 1.0, 0.0)
		self.user_font.setSubpixel(True)
		self.user_font.setHinting(skia.FontHinting.kFull)
		self.user_font.setEdging(skia.Font.Edging.kAntiAlias)
		#self.user_font.setForceAutoHinting(True)

		if not self.text_font.getTypeface():
			raise ValueError('Invalid font family specified')
		if not self.user_font.getTypeface():
			raise ValueError('Invalid font family specified')
		
		#Suggested line distance
		self.spacer = self.text_font.getSpacing()
		
		self.usrPaint = skia.Paint()
		self.usrPaint.setAntiAlias(False)
		self.txtPaint = skia.Paint()
		self.txtPaint.setAntiAlias(False)
		self.txtPaint.setColor(self.txt_color)

		self.tstampPaint = skia.Paint()
		self.tstampPaint.setAntiAlias(False)
		self.tstampPaint.setColor(self.tstamp_color)

		self.usrPaint.setStrokeWidth(1)
		self.txtPaint.setStrokeWidth(1)
		self.txtPaint.setFilterQuality(skia.FilterQuality.kHigh_FilterQuality)
		self.usrPaint.setFilterQuality(skia.FilterQuality.kHigh_FilterQuality)

	
	def drawScaledImage(self,image,scale,line,pos,canvas):
		w = image.width()
		h = image.height()
  
		of = round(line - (h * scale) / 2 - self.spacer / 4)

		#Destination
		nX = pos.x()
		nY = round(of + pos.y())
		sW = round(nX + w * scale)
		sH = round(nY + h * scale)
		dst = skia.Rect(nX,nY,sW,sH)
		
		tempPaint = skia.Paint()
		tempPaint.setFilterQuality(skia.FilterQuality.kHigh_FilterQuality)
		tempPaint.setAntiAlias(False)
		
		canvas.drawImageRect(image,skia.Rect(0,0,w,h),dst,tempPaint)
	
	def drawBackground(self,canvas,odd,rect):
		paint = skia.Paint()
		paint.setStyle(skia.Paint.kFill_Style)
		paint.setAntiAlias(True)
		if odd:
			paint.setColor(self.odd_bg)
		else:
			paint.setColor(self.even_bg)

		canvas.drawRect(rect, paint)

	def drawBackgroundSub(self,canvas,odd,rect):
		paint = skia.Paint()
		paint.setStyle(skia.Paint.kFill_Style)
		paint.setAntiAlias(True)
		if odd:
			paint.setColor(self.sub_odd_bg)
		else:
			paint.setColor(self.sub_even_bg)

		canvas.drawRect(rect, paint)

	def drawBackgroundHighlighted(self,canvas,odd,rect):
		paint = skia.Paint()
		paint.setStyle(skia.Paint.kFill_Style)
		paint.setAntiAlias(True)
		paint.setColor(self.highlight_bg_color)

		canvas.drawRect(rect, paint)
		#Sidebar
		paint.setColor(self.highlight_sidebar_color)
		canvas.drawRect(skia.Rect(0,0,5,rect.height()),paint)
