from .twitch import Twitch
from ..database import emote_database

class Badges:
	
	def getBadges(channel_id,scale = 1,database = False):
		'''
		Return all badges for the channel including global badges
		'''
		result = {}
		scale += 1
		if scale > 4: 
			scale = 4
		with emote_database(database) as conn:
			cur = conn.cursor()
			cur.execute("SELECT set_name,version,url,url2,url4,title FROM badges where channel_id = ? or channel_id = 0",(channel_id,))
			#format them into a hashmap with keys for the badge_name
			entries = cur.fetchall()
			for entry in entries:
				badge_name = entry[0]
				version = entry[1]
				url = entry[scale]
				title = entry[5]
				if not result.get(badge_name,False):
					result[badge_name] = {}
				result[badge_name][version] = (url,title)
			return result

	def toDatabase(channel_id,badges,database = False):
		with emote_database(database) as conn:
			c = conn.cursor()
			for bset in badges:
				setname = bset
				versions = badges[bset]['versions']
				for v in versions:
					url = versions[v].get('image_url_1x','')
					url2 = versions[v].get('image_url_2x','')
					url4 = versions[v].get('image_url_4x','')
					title = versions[v].get('title','')
					tpl = (channel_id,setname,v,url,url2,url4,title)
					c.execute("INSERT OR REPLACE INTO badges VALUES (?,?,?,?,?,?,?)",tpl)
			conn.commit()
		#Insert into database
