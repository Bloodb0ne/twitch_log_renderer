from string import Template
import os
import codecs
from tqdm import tqdm
from node_types import TextNode,EmoteNode,LinkNode,MentionNode,CheermoteNode
from rendering.basic_renderer import Renderer
import importlib.resources as pkg_resources

import assets


class HTMLRenderer(Renderer):
	defaultOptions = {
		'template_path':False
	}

	def __init__(self,options):
		self.options = {**HTMLRenderer.defaultOptions,**options}
		include_timestamps = self.options.get('include_timestamps',False)
		self.timestamp_format = self.options.get('timestamp_format',"[%H:%M:%S]")
		self.emoteWrapper = Template("<span class='emote'><img src='$url'></span>")
		self.badgeWrapper = Template("<span class='badge'><img src='$url' alt='$title'></span>")
		
		self.messageWrapper = Template(f'''
			<div class='msg'>
				{"<time datetime='$timestamp'>$ftimestamp</time>" if include_timestamps else ""}
				<span class='msg--uname' style='color:$color;'>$badges $username:</span>
				<div class='msg--container'>$text</div>
			</div>''')


	def renderNode(self,node):
		if isinstance(node,TextNode):
			return "<span class='txt'>{0}</span>".format(node.text)
		elif isinstance(node,LinkNode):
			return "<a href='{0}'>{0}</a>".format(node.text)
		elif isinstance(node,MentionNode):
			return "<span class='mention'>{0}</span>".format(node.text)
		elif isinstance(node,CheermoteNode):
			return "<span class='cheermote' style='color:{0};'><img src='{1}'>{2}</span>".format(node.color,node.url,node.amount)
		elif isinstance(node,EmoteNode):
			return self.emoteWrapper.substitute(url=node.url())
		return '' 
		
	def renderMessage(self,msg):
		return self.messageWrapper.substitute(
				timestamp = msg.timestamp.chat_time,
				ftimestamp = msg.timestamp.chat_time.strftime(self.timestamp_format),
				color = msg.user_color,
				username = msg.username.text,
				text = ''.join([self.renderNode(node) for node in msg.nodes]),
				badges = ''.join([self.badgeWrapper.substitute(url=node.url,title=node.title) for node in msg.badges])
			)
	def render(self,chatMessages):
		output_path = self.options['output_file']
		
		#Update options here or create an instance that has the options
		chatMessages.mergeNodes()
		print("[HTMLRenderer] Generating html from messages")
		result = ''.join([self.renderMessage(msg) for msg in tqdm(chatMessages.messages,disable=False)])
		
		html_template = "$content"
		if self.options.get('template_path',False):
			with codecs.open(templatePath, encoding='utf-8') as f:
				html_template = f.read()
		else:
			#Use Default Template
			html_template = pkg_resources.read_text(assets,'html_render_template.html')

		templ = Template(html_template)
		html_doc = templ.substitute(content=result)

		with codecs.open(output_path,mode='w+',encoding='utf-8') as f:
			f.write(html_doc)
