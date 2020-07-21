import urllib.request
import urllib.parse
import json
from database import emote_database

class FFZ:
	def emoteURL(ident,scale = 1):
		if scale == 3: scale = 4
		return "https://cdn.frankerfacez.com/emoticon/{0}/{1}".format(ident,scale)
	
	def emotesToDatabase(uid,emotes,database = False):
		with emote_database(database) as conn:
			c = conn.cursor()
			for emote in emotes:
				tpl = (int(uid),int(emote['id']),emote['name'],emote['urls'].get('1',''),emote['urls'].get('2',''),emote['urls'].get('4',''))
				c.execute("INSERT OR REPLACE INTO ffz_emotes(uid,emote_id,code,url,url2,url3) VALUES (?,?,?,?,?,?)",tpl)
			conn.commit()
	
	def getFFZChannelEmotes(ch):
		try:
			if isinstance(ch,int) or ch.isnumeric():
				url = "https://api.frankerfacez.com/v1/room/id/%s"
			else:
				url = "https://api.frankerfacez.com/v1/room/%s"
			
			f = urllib.request.urlopen(url % ch)
			data = json.loads(f.read().decode('utf-8'))
			twitch_id = data['room']['twitch_id']
			current_set = data['room']['set']
			return data['sets'][str(current_set)]['emoticons']
		except Exception as e:
			raise e
		
		

	def getFFZGlobalEmotes():
		try:
			f = urllib.request.urlopen("https://api.frankerfacez.com/v1/set/global")
			data = json.loads(f.read().decode('utf-8'))
			sets = data['default_sets']
			emotes = []
			for s in sets:
				emotes.extend(data['sets'][str(s)]['emoticons'])
			return emotes
		except Exception as e:
			raise e