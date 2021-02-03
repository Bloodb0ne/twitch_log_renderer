import re
import datetime
import skia
import argparse
import json
import itertools
import os
from .colors import colors


def hex_color(v):
	#check for named color 
	if v in colors:
		v = colors[v]
	opaque = r"^#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})$"
	alpha = r"^#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})$"
	oClr = re.match(opaque,v)
	aClr = re.match(alpha,v)
	if oClr:
		v = (int(oClr.group(1),16), int(oClr.group(2),16), int(oClr.group(3),16))
		return skia.ColorSetARGB(0xFF, *v)
	if aClr:
		v = (int(aClr.group(1),16),int(aClr.group(2),16),int(aClr.group(3),16),int(aClr.group(4),16))
		return skia.ColorSetARGB(*v)
	raise argparse.ArgumentTypeError("{} does not represent a hex color value or named color".format(v))

def norm_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))

    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]"%(x,))
    return x

def stringToDelta(dur_str):
	if not isinstance(dur_str,str):
		return None
	matcher = r"((?P<h>\d+)h)?((?P<m>\d+)m)?((?P<s>\d+)s(?P<ms>\d{1,4})?)?"
	m = re.match(matcher,dur_str)
	if m:
		h,m,s,ms = (int(c) if c else 0 for c in m.group('h','m','s','ms'))
		return datetime.timedelta(hours=h,minutes=m,seconds=s,microseconds=ms)
	else:
		return None

def stringWithTime(s):
	if not isinstance(s,str):
		return None
	matcher = r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)(.(?P<ms>\d+))?"
	m = re.match(matcher,s)
	if m:
		h,m,s,ms = (int(c) if c else 0 for c in m.group('h','m','s','ms'))
		return datetime.time(hour=h,minute=m,second=s,microsecond=ms)
	else:
		return None

def stringWithDatetime(s):
	if not isinstance(s,str):
		return None
	matcher = r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})[T ](?P<h>\d+):(?P<m>\d+):(?P<s>\d+)(.(?P<ms>\d+))?"
	m = re.match(matcher,s)
	if m:
		day,month,year,h,m,s,ms = (int(c) if c else 0 for c in m.group('day','month','year','h','m','s','ms'))
		return datetime.datetime(year,month,day,hour=h,minute=m,second=s,microsecond=ms)
	else:
		return None

def valid_timestring(t):
	# cant use any because a 0 timedelta is considered False
	validFormats = [stringToDelta(t),stringWithTime(t),stringWithDatetime(t)]
	isValid = len([x for x in validFormats if x is not None])
	if isValid:
		return t
	raise argparse.ArgumentTypeError("{} is not a valid timestring should be ( HH:MM:SS or MM-DD-YYYY HH:MM:SS or XhXmXs.XXXX )".format(t))

def transformTimeRange(start,end,tstr_start="",tstr_end = ""):
	#Try duration
	tdEnd = stringToDelta(tstr_end)
	if tdEnd:
		end = start + tdEnd
	tdStart = stringToDelta(tstr_start)
	if tdStart:
		start += tdStart
	#Try time only timestamp
	res = stringWithTime(tstr_start)
	if res:
		start = datetime.datetime.combine(start.date(),res)
	res = stringWithTime(tstr_end)
	if res:
		end = datetime.datetime.combine(end.date(),res)
	#Try timedate timestamp
	res = stringWithDatetime(tstr_start)
	if res:
		start = res
	res = stringWithDatetime(tstr_end)
	if res:
		end = res

	return (start,end)

def valid_date_type(arg_date_str):
	"""custom argparse *date* type for user dates values given from the command line"""
	try:
		return datetime.datetime.strptime(arg_date_str, "%d-%m-%Y")
	except ValueError:
		msg = "Given Date ({0}) not valid! Expected format, YYYY-MM-DD!".format(arg_date_str)
		raise argparse.ArgumentTypeError(msg)

def valid_path(arg_path):
	if os.path.isfile(arg_path):
		return arg_path
	else:
		raise argparse.ArgumentTypeError('Invalid ({0}) path selected'.format(arg_path))


def mergeConfigOptions(cli_args,cfg_path,flags = []):
	try:
		with open(cfg_path,mode='r+') as cfg:
			new_args = json.loads(cfg.read())
	except Exception as e:
		raise ValueError('Invalid filepath/Invalid JSON configuration')
	
	#split into a dict
	cargs = {}
	key = None
	for c in cli_args:
		isOption = c.startswith('--') and c not in flags
		if isOption and not key:
			key = c
		elif not isOption and key:
			cargs[key] = c
			key = None
		else:
			cargs[c]=None

	# Override config options
	for k,v in new_args.items():
		if k not in cargs:
			if v is False:
				cargs[k] = None
			else:
				cargs[k] = str(v)

	#Flatten parameter list
	return list(itertools.chain.from_iterable(
	[
		(k,) if not v else (k,v)
		for k,v in cargs.items()
	]))

def getVODIdentifier(val):
	if val.isnumeric():
		return val
	else:
		m = re.match(r"(https://)?(www\.)?twitch\.tv\/videos\/(?P<id>\d+)",val)
		if m:
			return m.group('id')
		else:
			raise ValueError("Invalid VOD identifier specified")

def addDefaultRenderArgs(args_parser):
	args_parser.add_argument('--database',
		help='Path to emote database',dest='db_path'
		,required=True)
	args_parser.add_argument('--channel',
		help='The channel the input log belongs to',
		metavar='Id / Name',
		required=True,nargs=1)
	args_parser.add_argument('--input',
		help='Input log file',
		metavar='<path>',
		dest='input_file',
		required=True)
	args_parser.add_argument('--output',
		help='Output log file',
		metavar='<path>',
		dest='output_file',
		required=True)
	args_parser.add_argument('--start',
		type=valid_timestring,
		help='Starting timestamp of the log to use')
	args_parser.add_argument('--end',
		type=valid_timestring,
		help='End timestamp of the log to use')
	args_parser.add_argument('--include_timestamps',
		action='store_true',
		help='Should the timestamp be shown in the log')
	args_parser.add_argument('--include_badges',
		action='store_true',
		help='Should the user badges be shown in the log')
	args_parser.add_argument('--timestamp_format',
		help='Valid datetime format for strptime()',default="[%H:%M]")
	args_parser.add_argument('--emote_overrride',
		help='JSON config describing emotes and urls for them',
		metavar='<path>')
	args_parser.add_argument('--config',
		help='JSON config with predefined arguments to load',
		default=None,
		metavar='<path>')
