import random
from ..database import emote_database
from .twitch import Twitch

class User:
	default_user_color = '#53535f'
	unameColors = {}
	colors = ['#FF0000','#0000FF','#008000',
			'#B22222','#FF7F50','#9ACD32',
			'#FF4500','#2E8B57','#DAA520',
			'#D2691E','#5F9EA0','#1E90FF',
			'#FF69B4','#8A2BE2','#00FF7F']

	def color(username):
		if not User.unameColors.get(username,False):
			color = User.colors[random.randint(0,len(User.colors)-1)]
			User.unameColors[username] = color
		return User.unameColors[username]

	def fetchUsers(users,database = False):
		result = {}
		missing = []
		with emote_database(database) as conn:
			c = conn.cursor()
			par = ','.join(['?']*len(users))
			c.execute("SELECT id,username FROM users WHERE username in ({})".format(par),users)
			db_users = c.fetchall()

			for db_user in db_users:
				un = db_user[1]
				result[un] = db_user[0]
			missing = [u for u in users if u not in result]
		
		
		#Fetch and add from Twitch API		
		tw_users = Twitch().getUserIDs(missing)
		for user,uid in tw_users.items():
			User.addToDB(user,uid,database)
			result[user] = int(uid)
		return result
	
	def convertToUserIDs(lst,database = False):
		if not all([ch.isnumeric() for ch in lst]):
			ids = [ch for ch in lst if ch.isnumeric()]
			names = [ch for ch in lst if not ch.isnumeric()]
			d = User.fetchUsers(names,database)
			return ids + list(d.values())
		return lst
	
	def addToDB(username,uid,database = False):
		with emote_database(database) as conn:
			c = conn.cursor()
			c.execute("INSERT OR REPLACE INTO users(id,username) VALUES (?,?)",(uid,username))
			conn.commit()
