import urllib.request
import urllib.parse
import json
import sqlite3
import tempfile
import requests
import re
from ..database import emote_database

class Twitch():
	def __init__(self,client_id = False):
		if client_id:
			self.client_id = client_id
		else:
			self.client_id = "y9hqjjt4l4wjtya7l4m9vphquy5vcg"

	def emoteURL(ident,scale = 1):
		return "https://static-cdn.jtvnw.net/emoticons/v1/{0}/{1}.0".format(ident,scale)
	
	def downloadTwitchEmotes(self):
		emoteData = None
		r = requests.get("https://api.twitch.tv/v5/chat/emoticon_images",{'client_id':self.client_id},stream=True)
		with tempfile.TemporaryFile(mode="w+b") as tmp_file:
			for chunk in r.iter_content(chunk_size=128):
				tmp_file.write(chunk)
			tmp_file.seek(0)
			emoteData = json.loads(tmp_file.read())
		return emoteData

	def emotesToDatabase(emotes,database = False):
		with emote_database(database) as conn:
			c = conn.cursor()
			for emote in emotes['emoticons']:
				if emote['emoticon_set'] == 0: 
					continue
				prefix = re.match(r"([a-z0-9]*)(.*)",emote['code']).group(1)
				tpl = (emote['id'],prefix,emote['code'],emote['emoticon_set'])
				c.execute("INSERT OR IGNORE INTO twitch_emotes VALUES (?,?,?,?)",tpl)
			conn.commit()

	def downloadVODLog(self,vod_id):
		comments = []

		params = {'client_id':self.client_id}
		while True:
			r = requests.get("https://api.twitch.tv/v5/videos/{}/comments".format(vod_id),params)
			data = r.json()
			nextCursor = data.get('_next',False)
			comments.extend(data.get('comments',[]))
			if nextCursor:
				params = {'client_id':self.client_id,'cursor': nextCursor}
			else:
				break
		
		return comments

	def downloadGlobalBadges():
		f = urllib.request.urlopen("https://badges.twitch.tv/v1/badges/global/display")
		data = json.loads(f.read().decode('utf-8'))
		return data.get('badge_sets',[])
	
	def downloadChannelBadges(channel_id):
		# f = urllib.request.urlopen("https://badges.twitch.tv/v1/badges/channels/{0}/display".format(channel_id))
		# data = json.loads(f.read().decode('utf-8'))
		r = requests.get("https://badges.twitch.tv/v1/badges/channels/{0}/display".format(channel_id))
		data = r.json()
		return data.get('badge_sets',[])
	
	def downloadCheermotes(self,channel_id):
		params = {'client_id':self.client_id,'channel_id':channel_id}
		# f = urllib.request.urlopen("https://api.twitch.tv/v5/bits/actions?{0}".format(params))
		# data = json.loads(f.read().decode('utf-8'))
		r = requests.get("https://api.twitch.tv/v5/bits/actions",params)
		data = r.json()
		return data.get('actions',[])
	
	def getUserIDs(self,user_logins):
		if len(user_logins) == 0: 
			return {}
		
		user_logins = ','.join(user_logins)
		params = urllib.parse.urlencode({'client_id':self.client_id,'login':user_logins})
		f = urllib.request.urlopen("https://api.twitch.tv/v5/users?{0}".format(params))
		data = json.loads(f.read().decode('utf-8'))
		result = {}
		for user in data.get('users',[]):
			name = user['name']
			result[name] = user['_id']
		return result
