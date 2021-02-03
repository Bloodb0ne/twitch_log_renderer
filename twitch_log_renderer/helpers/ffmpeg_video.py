import ffmpeg
import os
import subprocess

class ffmpeg_output_pipe:
	encOpts = {
	'walpha':{
		'prores':{'pix_fmt':'yuva444p10le','codec':"prores_ks",'alpha_bits':8},
		'qtanim':{'pix_fmt':'argb','codec':"qtrle"},
		'png':{'pix_fmt':'rgba','codec':"png"},
		'vp8':{'pix_fmt':'yuva422p','codec':"libvpx"},
		'vp9':{'pix_fmt':'yuva422p','codec':"libvpx-vp9"}
	},
	'woalpha':{
		'nvenc':{'pix_fmt':'yuv422p','codec':"nvenc"},
		'h264':{'pix_fmt':'yuv444p','codec':"libx264"},
		'h265':{'pix_fmt':'yuv422p','codec':"libx265"},
		'vp8':{'pix_fmt':'yuv422p','codec':"libvpx"},
		'vp9':{'pix_fmt':'yuv422p','codec':"libvpx-vp9"}
		}
	}
	def getAvailableEncoders():
		alpha_encoders = ffmpeg_output_pipe.encOpts['walpha']
		normal_encoders = ffmpeg_output_pipe.encOpts['woalpha']
		return set(alpha_encoders.keys()) | set(normal_encoders.keys())
	
	def __init__(self,w,h,filename,fps=25,transparent=False,encoder='h264',removeAudio = True,quiet=False):
		self.width = w
		self.height = h
		self.out_filename = filename
		self.fps = float(fps)
		self.quiet = quiet

		alpha_encoders = ffmpeg_output_pipe.encOpts['walpha']
		normal_encoders = ffmpeg_output_pipe.encOpts['woalpha']
		#validate encoder
		supported_encoders = list(alpha_encoders.keys()) + list(normal_encoders.keys())
		if encoder not in supported_encoders:
			raise ValueError('Invalid encoder please choose on of the following {}'.format(supported_encoders))
		
		self.multi_output = False
		#Split Mask and Output
		if encoder in alpha_encoders:
			self.options = alpha_encoders[encoder]
		if encoder in normal_encoders:
			if transparent:
				self.multi_output = True
				root,ext = os.path.splitext(self.out_filename)
				#is this reliable enough ?
				self.key_out_filename = root+'_mask'+ext
			self.options = normal_encoders[encoder]

		#Set FPS
		self.options['r'] = self.fps

		#Remove audio track
		if removeAudio:
			self.options['an'] = None

	def __enter__(self):
		global_args = []
		ffinput = ffmpeg.input('pipe:',framerate=self.fps, format='rawvideo', pix_fmt='rgb32',hwaccel='auto',s='{}x{}'.format(self.width, self.height))

		if self.quiet:
			global_args = ['-hide_banner', '-nostats', '-loglevel', 'fatal']
		

		if self.multi_output:
			split = ffinput.filter_multi_output('split')
			raw_alpha = ffmpeg.filter_(split.stream(1),'lutrgb',**{'r':'maxval','g':'maxval','b':'maxval'})
			key_video = ffmpeg.overlay(split.stream(2),raw_alpha)
			out_key = key_video.output(self.key_out_filename)
			out_main = split.stream(3).output(self.out_filename,**self.options)
			
			self.proc = (
				ffmpeg
				.merge_outputs(out_main,out_key)
				.global_args(*global_args)
				.run_async(pipe_stdin=True)
			)

		else:

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
