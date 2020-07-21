import contextlib
import sqlite3
import os

@contextlib.contextmanager
def emote_database(customPath = False):
	if not os.path.isfile(customPath):
		createEmptyDatabase(customPath)
	conn = sqlite3.connect(customPath)
	yield conn
	conn.close() # is this considered cleanup

def createEmptyDatabase(file_path):
	try:
			conn = sqlite3.connect(file_path)
			conn.execute('''
			CREATE TABLE `badges` (
				`channel_id`	INTEGER,
				`set_name`	TEXT,
				`version`	TEXT,
				`url`	TEXT,
				`url2`	TEXT,
				`url4`	TEXT,
				`title`	TEXT,
				PRIMARY KEY(channel_id,set_name,version)
			);
			''')
			conn.execute('''
			CREATE TABLE `bttv_emotes` (
				`uid`	INTEGER,
				`emote_id`	TEXT,
				`code`	TEXT,
				`type`	TEXT,
				PRIMARY KEY(uid,emote_id,code)
			);
			''')
			conn.execute('''
			CREATE TABLE `cheermotes` (
				`channel_id`	INTEGER,
				`type`	TEXT,
				`min_bits`	INTEGER,
				`prefix`	TEXT,
				`color`	TEXT,
				`animated`	INTEGER,
				`theme`	TEXT,
				`scale`	REAL,
				`url`	TEXT,
				PRIMARY KEY(channel_id,type,min_bits,prefix,animated,theme,scale)
			);
			''')
			conn.execute('''
			CREATE TABLE `ffz_emotes` (
				`uid`	INTEGER,
				`emote_id`	INTEGER,
				`code`	TEXT,
				`url`	TEXT,
				`url2`	TEXT,
				`url3`	TEXT,
				PRIMARY KEY(uid,emote_id,code)
			);
			''')
			conn.execute('''
			CREATE TABLE `twitch_emotes` (
				`id`	INTEGER UNIQUE,
				`prefix`	text,
				`code`	text,
				`emote_set`	INTEGER,
				PRIMARY KEY(id,prefix,code)
			);
			''')
			conn.execute('''
			CREATE TABLE `users` (
				`id`	INTEGER,
				`username`	TEXT,
				PRIMARY KEY(id,username)
			);
			''')
			conn.commit()
			conn.close()
	except Exception as e:
		raise e