import urllib.request
import urllib.parse
import json
from ..database import emote_database

class BTTV:
	def emoteURL(ident,scale = 1):
		return "https://cdn.betterttv.net/emote/{0}/{1}x".format(ident,scale)
	
	def getBTTVChannelEmotes(ch_id):
		try:
			f = urllib.request.urlopen("https://api.betterttv.net/3/cached/users/twitch/%s" % ch_id)
			data = json.loads(f.read().decode('utf-8'))
			channelEmotes = data['channelEmotes']
			sharedEmotes = data['sharedEmotes']
			return channelEmotes + sharedEmotes
		except Exception as e:
			raise e

	def getBTTVGlobalEmotes():
		try:
			f = urllib.request.urlopen("https://api.betterttv.net/3/cached/emotes/global")
			return json.loads(f.read().decode('utf-8'))
		except Exception as e:
			raise e

	def emotesToDatabase(emotes,uid = 0,database_path = False):
		with emote_database(database_path) as conn:
			c = conn.cursor()
			for emote in emotes:
				tpl = (uid,emote['id'],emote['code'].replace("'","''"),emote['imageType'])
				c.execute("INSERT OR REPLACE INTO bttv_emotes(uid,emote_id,code,type) VALUES (?,?,?,?)",tpl)
			conn.commit()
