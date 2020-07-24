import skia

class AnimatedImage:
	def __init__(self,path):
		if isinstance(path,bytes):
			self.decGif = skia.Codec(path)
		else:
			with open(path,'br+') as f:
				self.decGif = skia.Codec(f.read())
		self.imageInfo = self.decGif.getInfo()
		self.fCount = self.decGif.getFrameCount()
		self.fInfos = self.decGif.getFrameInfo()
		self.fCurrIndex = 0
		self.tDuration = 0
		for info in self.fInfos:
			self.tDuration += info.fDuration
			info.fDuration = self.tDuration
		self.fImages = {}
		if self.tDuration == 0:
			self.loadStaticFrame()
		else:
			for i in range(0,self.fCount):
				self.getFrameAt(i)
	
	def isAnimated(self):
		return self.tDuration != 0
	
	def getFrame(self):
		return self.getFrameAt(self.fCurrIndex) if self.tDuration > 0 else self.fImages[0]

	def loadStaticFrame(self):
		if self.fImages.get(0,False) is not False:
			return self.fImages[0]

		rb = self.imageInfo.minRowBytes()
		bmap = skia.Bitmap()
		bmap.allocPixels(self.imageInfo)
		result = self.decGif.getPixels(self.imageInfo,bmap.getPixels(),bmap.rowBytes())
		if result == skia.Codec.Result.kSuccess:
			self.fImages[0] = skia.Image.MakeFromBitmap(bmap)
			return self.fImages[0]
		return False

	def getFrameAt(self,index):
		if self.fImages.get(index,False) is not False:
			return self.fImages[index]

		rb = self.imageInfo.minRowBytes()
		bmap = skia.Bitmap()
		bmap.allocPixels(self.imageInfo)
		
		reqFrame = self.fInfos[index].fRequiredFrame
		
		opts = skia.Codec.Options()
		opts.fFrameIndex = index
		opts.fPriorFrame = reqFrame if reqFrame != index - 1 else skia.Codec.kNoFrame
		
		
		if reqFrame != skia.Codec.kNoFrame:
			pmap = skia.Pixmap()
			if self.fImages.get(reqFrame,False):
				self.fImages.get(reqFrame).readPixels(pmap,0,0)
			bmap.writePixels(pmap)

		result = self.decGif.getPixels(self.imageInfo,bmap.getPixels(),bmap.rowBytes(),opts)

		if result == skia.Codec.Result.kSuccess:
			self.fImages[index] = skia.Image.MakeFromBitmap(bmap)
			return self.fImages[index]
		return False

	def seek(self,msec):
		if self.tDuration == 0: 
			return False
		msec = msec % self.tDuration

		lower = next((ind for ind,fi in enumerate(self.fInfos) if fi.fDuration >= msec ),0)
		prevIndex = self.fCurrIndex
		self.fCurrIndex = lower
		return self.fCurrIndex != prevIndex
