from providers.twitch import Twitch
from database import emote_database

class Cheermotes:
	
	def getCheermotes(channel_id,scale = 1,animated=True,theme='Dark',database = False):
		'''
		Return all badges for the channel including global badges
		'''
		with emote_database(database) as conn:
			cur = conn.cursor()
			cur.execute("""SELECT prefix,min_bits,color,animated,url 
			FROM cheermotes where 
			(channel_id = ? or channel_id = 0) and 
			animated = ? and 
			theme = ? and 
			scale = ?""",(channel_id,animated,theme,scale))
			#format them into a hashmap with keys for the cheer_name
			return cur.fetchall()
	
	def toDatabase(channel_id,cheermotes,database = False):
		#Ugly shite
		with emote_database(database) as conn:
			c = conn.cursor()
			for chmote in cheermotes:
				prefix = chmote['prefix']
				tiers = chmote['tiers']
				chType = chmote['type']
				if chType == 'channel_custom':
					chID = channel_id
				else:
					chID = 0
				for tier in tiers:
					color = tier['color']
					min_bits = tier['min_bits']
					limages = tier['images']['light']
					dimages = tier['images']['dark']
					for anim in dimages['animated']:
						scale = anim
						url = dimages['animated'][anim]
						tpl = (chID,chType,min_bits,prefix,color,True,"Dark",scale,url)
						c.execute("INSERT OR REPLACE INTO cheermotes VALUES (?,?,?,?,?,?,?,?,?)",tpl)
					for anim in dimages['static']:
						scale = anim
						url = dimages['static'][anim]
						tpl = (chID,chType,min_bits,prefix,color,False,"Dark",scale,url)
						c.execute("INSERT OR REPLACE INTO cheermotes VALUES (?,?,?,?,?,?,?,?,?)",tpl)
					for anim in limages['animated']:
						scale = anim
						url = dimages['animated'][anim]
						tpl = (chID,chType,min_bits,prefix,color,True,"Light",scale,url)
						c.execute("INSERT OR REPLACE INTO cheermotes VALUES (?,?,?,?,?,?,?,?,?)",tpl)
					for anim in limages['static']:
						scale = anim
						url = dimages['static'][anim]
						tpl = (chID,chType,min_bits,prefix,color,False,"Light",scale,url)
						c.execute("INSERT OR REPLACE INTO cheermotes VALUES (?,?,?,?,?,?,?,?,?)",tpl)
			conn.commit()