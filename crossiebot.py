import logging
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

### Logger for bot updates ####

logging.basicConfig(filename = 'crossiebot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

###############################

########### Globals ###########

TOKEN = # <insert bot token>
GROUP_ID = # <insert chat id> to restrict spreadsheet access to a chosen chat
CREDS_JSON = # <insert .json credentials file>
CLUE_FILE = './clues.txt'
KOSHER_STICKER = 'CAACAgQAAxkBAAEBEg1fFGUi_BrhHa_wjtz2GKyeTRYmYAAC408xAAGV22IvqNvR8y8iGqYaBA'
CLUE_SHEET_LINK = 'https://docs.google.com/spreadsheets/d/1ioipi0GyoEYDEVolcy0Lu1wJBiKZgywQsizrVbLEWqY/edit#gid=94805756'
HELP_STRING = "I document the clues in this chat in this spreadsheet:" + CLUE_SHEET_LINK + "\n\n\
I respond to these commands:\n\
/start - I introduce myself\n\
/help - I show this message\n\
/kosher - I send the kosher sticker\n\
/splclue - I send all the text that follows this command to the spreadsheet. Use this for clues without enum or multi-line clues" 

################################

## Regexes for matching clues and emoji ##

'''
The regex for crossword clues works by matching 
the enumeration of the clue.
'''
clue_regex = re.compile(r""".+		# there should be some text before enum
			    (\s)*	# any number of spaces
			    \(		# opening parenthesis
			    [1-9]	# enum
			    ((\s)*	
			    [,|\-]*	# connectors
			    (\s)*
			    [0-9]+)*	# possibly more numbers
			    \)		# closing parenthesis""", re.X) 
'''
This regex matches the :grin: and :smile: emojis
'''
emoji_regex = re.compile(r'(\U0001F604)|(\U0001F601)')


##### Bot commands #####

def start(update, context):
	context.bot.send_message(chat_id = update.effective_chat.id, text = "Hello, I am crossie bot! I keep track of your clues.")
	logger.info(update.message.chat.id)
	
def help(update, context):
	context.bot.send_message(chat_id = update.effective_chat.id, text = HELP_STRING)

def kosher(update, context):
	context.bot.send_sticker(chat_id = update.effective_chat.id, sticker = KOSHER_STICKER)
	
def grin(update, context):
	context.bot.send_message(chat_id = update.effective_chat.id, text = u'\U0001F604')
	logger.info(update.message.text)

########################


### Function to write clues to a Google Sheet ####

def update_sheet(date, sender, clues, tabname, spl = False):
	scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

	creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_JSON, scope)
	client = gspread.authorize(creds)
	wsheet = client.open("CrossieClues").worksheet(tabname)

	data = wsheet.get_all_values()

	row_f = len(data) + 1
		
	if spl == False:
		row_l = len(data) + len(clues)
		
	else:
		row_l = row_f
		
	cells = wsheet.range(row_f, 1, row_l, 1)
	for cell in cells:
		cell.value = date
	wsheet.update_cells(cells)
	
	cells = wsheet.range(row_f, 2, row_l, 2)
	
	if spl == False:
		for i, cell in enumerate(cells):
			cell.value = clues[i]
			
	else:
		cells[0].value = clues
	wsheet.update_cells(cells)

	cells = wsheet.range(row_f, 3, row_l, 3)
	for cell in cells:
		cell.value = sender
	wsheet.update_cells(cells)

##############################################

## Function to extract clues from a message ##	
def get_clues(update, context):
	clues = []
	
	msg_str = update.message.text
	sender = update.message.from_user.first_name
	send_date = str(date.today())
	
	while True:
		match = clue_regex.search(msg_str)
		
		if match is None:
			break
			
		clues.append(match.group())
		_, last = match.span()
		msg_str = msg_str[last::]
	
	# writing to a local text file	
	f = open(CLUE_FILE, 'a')
	
	for clue in clues:
		f.write(send_date)
		f.write("\t")
		f.write(sender)
		f.write("\t")
		f.write(clue)
		f.write("\n")
		
	f.close()
	
	update_sheet(send_date, sender, clues, 'Clues')
	
	return 

#############################################


#### Function to record special clues without enumeration ####

def splclue(update, context):
	msg_str = update.message.text
	sender = update.message.from_user.first_name
	send_date = str(date.today())
	
	clue_str = re.split('/splclue\s*\n*', msg_str, re.I)[1]
	logger.info(clue_str)
	
	with open(CLUE_FILE, 'a') as f:
		f.write(send_date)
		f.write('\t')
		f.write(sender)
		f.write('\t')
		f.write(clue_str)
		f.write('\n')
		
	update_sheet(send_date, sender, clue_str, 'Special', spl = True)

###############################################################			

	
def main():

	updater = Updater(TOKEN, use_context=True)
	dp = updater.dispatcher
	
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('kosher', kosher))
	dp.add_handler(CommandHandler('splclue', splclue, filters=Filters.chat(GROUP_ID)))
	
	dp.add_handler(MessageHandler(Filters.regex(clue_regex) & Filters.chat(GROUP_ID), get_clues))
	dp.add_handler(MessageHandler(Filters.regex(emoji_regex), grin))
	
	updater.start_polling()
	
	updater.idle()

if __name__ == '__main__':
	main()
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
