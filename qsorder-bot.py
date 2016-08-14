# -*- coding: utf-8 -*-

import config
import telebot
import logging


from bs4 import *
import urllib.request
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

#globals
bot = telebot.TeleBot(config.token)
commands = {}

def get_url_soup(url):
	print("retrieving " + url)
	html = urllib.request.urlopen(url).read()
	soup = BeautifulSoup(html, "html.parser")
	return soup

def search_global(call):
	# bot.send_message(message.chat.id, "Looking for QSOs with " + message.text.upper())
	url = 'http://qsorder-k3it.rhcloud.com/global/' +  call.upper()
	try:
		soup = get_url_soup(url)
	except:
		return "Invalid request"
	tags = soup('a')
	if len(tags) > 0:
		msg_text = []
		txt = 'Found *' + call.upper() + '* audio in the following log(s):\n\n'
		for tag in tags:
			de_call = tag.contents[0].string
			num_qsos = tag.span.text
			search_path = re.search(r"'(.*?)'",tag.get('onclick',None)).group(1)
			command = search_path.split('/')[3]
			qso_url = 'http://qsorder-k3it.rhcloud.com' + search_path

			commands[command] = qso_url

			msg_text.append(de_call + " (" + num_qsos + "): /" + command)
			#if (int(num_qsos) > 1):
				#msg_text += 's\n'
			#else:
				#msg_text += '\n'
		for i in sorted(msg_text):
			txt += i + '\n'
	else:
		txt = "No Audio Found for " + call.upper()
	return txt
		


@bot.message_handler(commands=['start', 'help', 'hello'])
def handle_start(message):
    bot.send_message(message.chat.id, message.from_user.first_name + 
    	', welcome to the QSO audio search.  For more info visit [QSORDER website.](http://qsorder-k3it.rhcloud.com/) Enter a call sign to begin:',
    	 parse_mode="Markdown") 


@bot.message_handler(regexp=".+_de_.+")
def handle_message(message):
	bot.send_message(message.chat.id, 'Retrieving audio: ' + message.text.strip('/'))
	try:
		url = commands[message.text.strip('/')]
		soup = get_url_soup(url)
	except:
		bot.send_message(message.chat.id, 'Could not parse ' + message.text)
		return

	rows = soup('tr')
	txt = ''
	for row in rows[1:]:
		cols = row.find_all('td')

		dxcall = cols[0].text
		decall = cols[1].text
		utc = cols[2].text
		band  = cols[3].text
		mode  = cols[4].text
		contest = cols[5].text
		link  = '[Download](' + cols[6].audio.source['src'] + ')'

		txt += "*DX Call:* " + dxcall + '\n'
		txt += "*DE Call:* " + decall + '\n'
		txt += "*UTC:* " + utc + '\n'
		txt += "*Band/Mode:* " +  band + ' ' + mode + '\n'
		txt += "*Contest:* " + contest + '\n'
		txt +=  link  + '\n\n'
	
		print(txt)
		bot.send_message(message.chat.id, txt, parse_mode="Markdown")
		txt = ''


@bot.message_handler(content_types=["text"])
def process_Call(message):
	if (len(message.text.split()) > 1 ):
		bot.send_message(message.chat.id, message.from_user.first_name + ", one callsign at a time please.")
	else:
		txt = search_global(message.text.replace('/', '-'))
		bot.send_message(message.chat.id, txt)
			

if __name__ == '__main__':
     bot.polling(none_stop=True)

