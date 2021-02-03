import ffmpeg
import os
import subprocess

class ffmpeg_image_pipe:
	encoders = {
		'gif': {
			'pix_fmt':'rgb8',
			'codec':"gif",
			'filter_complex': '[0:v]split[x][z];[z]palettegen[y];[x]fifo[x];[x][y]paletteuse'
		},
		'png': {
			'pix_fmt':'rgba',
			'codec':"png"
		},
		'vp8':{
			'pix_fmt':'yuv422p',
			'codec':"libvpx"
		},
		'vp9':{
			'pix_fmt':'yuv422p',
			'codec':"libvpx-vp9"
		}
	}

	def getAvailableEncoders():
		return list(ffmpeg_image_pipe.encoders.keys())
	
	def isAnimatedEncoder(encoder):
		if encoder in ['gif','vp8','vp9']:
			return True
		else:
			return False
	
	def __init__(self,w,h,filename,fps=25,transparent=False,encoder='png',removeAudio = True,quiet=False):
		self.width = w
		self.height = h
		self.out_filename = filename
		self.fps = float(fps)
		self.quiet = quiet

		#validate encoder
		supported_encoders = list(ffmpeg_image_pipe.encoders.keys())
		if encoder not in supported_encoders:
			raise ValueError('Invalid encoder please choose on of the following {}'.format(supported_encoders))
		
		self.multi_output = False
		
		self.options = ffmpeg_image_pipe.encoders[encoder];
		
		#Set FPS
		self.options['r'] = self.fps

		#Remove audio track
		self.options['an'] = None

	def __enter__(self):
		global_args = []
		ffinput = ffmpeg.input('pipe:',framerate=self.fps, format='rawvideo', pix_fmt='rgb32',hwaccel='auto',s='{}x{}'.format(self.width, self.height))

		if self.quiet:
			global_args = ['-hide_banner', '-nostats', '-loglevel', 'fatal']
		

		self.proc =  (
				ffinput
				.output(self.out_filename, **self.options)
				.overwrite_output()
				.global_args(*global_args)
				.run_async(pipe_stdin=True)
			)
		return self.proc
	def __exit__(self, exc_type, exc_value, traceback):
		#Simple Cleanup
		self.proc.stdin.close()
		self.proc.wait()
