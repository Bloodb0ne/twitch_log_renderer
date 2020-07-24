import re
from .database import emote_database
from .node_types import EmoteNode,TextNode,CheermoteNode
from .providers.badges import Badges
from .providers.cheermotes import Cheermotes

class CheermoteCache:
	"""Cheermote cache"""
	matcher = re.compile("^$")
	cheermotes = {}
	databasePath = ''
	def getCheermote(prefix,amount):
		try:
			return [chm for chm in CheermoteCache.cheermotes if chm[0] == prefix and chm[1] <= amount][-1]
		except Exception as e:
			return False
	
	def update(channel_id,scale = 1,animated=True,theme='Dark'):
		CheermoteCache.cheermotes = Cheermotes.getCheermotes(channel_id,scale,animated,theme,database=CheermoteCache.databasePath)
		#Create matcher
		prefixes = "|".join([cheermote[0] for cheermote in CheermoteCache.cheermotes])
		CheermoteCache.matcher = re.compile(r'({0})(\d+)'.format(prefixes))

	def isCheermote(txt):
		match = CheermoteCache.matcher.match(txt.title())
		
		if match:
			prefix = match.group(1)
			amount = int(match.group(2))

			chm = CheermoteCache.getCheermote(prefix,amount)
			if not chm: 
				return False
			return CheermoteNode(prefix,chm[4],chm[2],amount)
		return False	

class BadgeCache:
	"""Caching of badges"""
	badges = {}
	databasePath = ''
	def update(channel_id,scale = 1):
		BadgeCache.badges = Badges.getBadges(channel_id,scale,database=BadgeCache.databasePath)
	
	def get(setname,version):
		return BadgeCache.badges.get(setname,{}).get(version,False)

class WordCache:
	"""Reducing repeatable queries for words"""
	wordCache = {}
	def isCached(s):
		return WordCache.wordCache.get(s,False)
	def cache(s,node = False):
		if node:
			WordCache.wordCache[s] = node
		else:
			WordCache.wordCache[s] = TextNode(s)
		return WordCache.wordCache[s]


class Emote:
	"""Manage emote caching and finding"""
	emoteCache = {}
	databasePath = ""
	def isCached(code):
		return Emote.emoteCache.get(code,False)
	
	
	def canBeTwitchEmote(str):
		'''
		Filtering words because emotes have a <prefix><Name>
		 *doesnt start with a number
		 *has a number or uppercase letter separating prefix and name
		 *only ASCII alphanumeric
		'''
		return bool(re.match(r"^[a-z]+[a-z0-9]+[A-Z0-9]+[\w]*$",str))

	#Caching Twitch emotes using the json data in the log
	def toEmoteCache(fragments):
		for frag in fragments:
			code = frag['text']

			if frag.get('emoticon',False):
				_id = frag['emoticon']['emoticon_id']
				Emote.emoteCache[code] = EmoteNode((_id,"TWITCH",""))

	def tryFind(code,only3rdParty = True):
		with emote_database(Emote.databasePath) as c:
			if only3rdParty:
				full = False
			else:
				full = Emote.canBeTwitchEmote(code)
			if not full:
				query = '''SELECT emote_id,"BTTV","" FROM bttv_emotes WHERE code = '{0}' UNION
					SELECT emote_id,"FFZ",url FROM ffz_emotes WHERE code = '{0}' '''.format(code)
			else:
				query = '''SELECT emote_id,"BTTV","" FROM bttv_emotes WHERE code = '{0}' UNION
						SELECT emote_id,"FFZ",url FROM ffz_emotes WHERE code = '{0}' UNION
						SELECT id,"TWITCH","" FROM twitch_emotes WHERE code = '{0}' '''.format(code)
			res = c.execute(query)
			emote = res.fetchone()
			
			return emote

	def cache(code,obj):
		Emote.emoteCache[code] = EmoteNode(obj)
		return Emote.emoteCache[code]
