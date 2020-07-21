import skia
import os

class StaticImage:
	def __init__(self,path):
		with open(path,mode='br+') as f:
			self.image = skia.Image.DecodeToRaster(f.read())

	def width(self):
		return self.image.info().width()

	def height(self):
		return self.image.info().height()

class AnimatedImage:
	def __init__(self,path):
		with open(path,'br+') as f:
			self.decGif = skia.Codec(f.read())
			self.imageInfo = self.decGif.getInfo()
			self.fCount = self.decGif.getFrameCount()
			self.fInfos = self.decGif.getFrameInfo()
			self.tDuration = 0
			for info in self.fInfos:
				self.tDuration += info.fDuration
				info.fDuration = self.tDuration
			self.fImages = {}
			self.fCurrIndex = 0
			

	def getFrame(self):
		return self.getFrameAt(self.fCurrIndex) if self.tDuration > 0 else self.fImages[0]

	def getFrameAt(self,index):
		if self.fImages.get(index,False) != False:
			return self.fImages[index]

		rb = self.imageInfo.minRowBytes()
        #Carefull with the lifetime of this
		bmap = skia.Bitmap()
		bmap.allocPixels(self.imageInfo)

		opts = skia.Codec.Options()
		opts.fFrameIndex = index
		reqFrame = self.fInfos[index].fRequiredFrame

		if reqFrame != skia.Codec.kNoFrame:
			#copy image data from required frame
			pmap = skia.Pixmap()
			self.fImages[reqFrame].readPixels(pmap,0,0)
			bmap.installPixels(pmap)
			
		
		result = self.decGif.getPixels(self.imageInfo,bmap.getPixels(),bmap.rowBytes(),opts)

		if result == skia.Codec.Result.kSuccess:
			self.fImages[index] = skia.Image.MakeFromBitmap(bmap)
			return self.fImages[index]
		return False

	def seek(self,msec):
		msec = msec % self.tDuration

		lower = next((ind for ind,fi in enumerate(self.fInfos) if fi.fDuration >= msec ),0)
		prevIndex = self.fCurrIndex
		self.fCurrIndex = lower
		return self.fCurrIndex != prevIndex

def loadImage(path):
	extension = os.path.splitext(path)[1]
	if  extension == '.gif':
		return AnimatedImage(path)
	elif extension == '.png':
		return StaticImage(path)
