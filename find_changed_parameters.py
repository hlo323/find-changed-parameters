#!/usr/bin/env python

import pymongo
import sys
import datetime
import re
import argparse
import doctest

connection = connection = pymongo.MongoClient('localhost', 27017)

games = connection.moblab.games
playlists = connection.moblab.playlists
templates = connection.moblab.templates
creator_games = []
f = open("output.txt", 'w')
date_after = datetime.datetime(1, 1, 1, 0, 0, 0, 0)

def filter_creators(collection):
	"""
	Returns a list of all the game IDs played by Moblab creators
	
	Args:
		collection: The collection that needs to be filtered
	
	>>> test = connection.moblab.test
	>>> test.insert({"_id" : "0011d817-9bdf-49d1-9911-dce4ce22abe4","className" : "com.moblab.playlist.Playlist","name" : "Asset Markets","description" : "","creator" : "yzhen@wesleyancollege.edu","items" : ["1b13558d-e6e6-4041-b370-bcfdab8a3f27"]})
	'0011d817-9bdf-49d1-9911-dce4ce22abe4'
	>>> filter_creators(test)
	[]
	>>> test.drop()
	"""
	list = []
	query = {"$and" : [{"$or" : [{"creator": {"$not" : re.compile('@')}}, {"creator" : {"$regex" : "@moblab.com"}}]}, {"creator": {"$exists" : True}}], "items" : {"$exists" : True}}
	cur = collection.find(query)

	for item in cur:
		game_ids = item["items"]
		list.extend(game_ids)
	return list
		
def compare_parameter(one_parameter):
	"""
	List parameter information for all the games of the same type that have changed the specific parameter
	
	Writes the parameter name, default value, changed values, and creators who changed 
	the parameter to the output file. 
	
	Args:
		one_parameter: A list of all the games that have changed one specific parameter. 
			Information about the games are contained in tuples with each tuple containing 
			the parameter name, template value, game value, and game id
			
	>>> compare_parameter([('deposit', 100, 10, '000c7f7d-01fa-4f1f-a551-1a4d7a424289'), ('deposit', 100, 30, '000cc343-f3bf-4612-87de-991d7c92d60c')]) is None
	True
	"""
	parameter_name = one_parameter[0][0]
	template_value = one_parameter[0][1]
	if template_value == None:
		f.write("\n\tParameter not in template: " + parameter_name + "*")
	else:
		f.write("\n\tParameter: " + str(parameter_name) + "\n\tDefault Value: " + str(template_value))
		one_parameter.sort(key= lambda tup: tup[2])
		previous_value = ""
		changed_creators = set()
		
		for item in one_parameter:
			game_id = item[3]
			cursor = playlists.find({"items" : game_id, "creator" : {"$exists" : True}})
			
			if cursor.count() != 0:
				creators = set()
				for doc in cursor:
					creators.add(doc["creator"])
				if len(creators) ==1:
					changed_creators.update(creators)
				else:
					for creator in creators:
						starred = creator + "*"
						changed_creators.add(starred)
			template_value = item[1]	
			game_value = item[2]
			
			if isinstance(template_value, unicode):
				template_value = template_value.encode("utf-8")
			if isinstance(game_value, unicode):
				game_value = game_value.encode("utf-8")
				
			if game_value != previous_value:
				f.write("\n\tChanged Value: " + str(game_value))
				changed_creators_list = list(changed_creators)
				if len(changed_creators_list) > 0:
					f.write("(")
					for index in range(0, len(changed_creators_list)):
						if index == len(changed_creators_list) -1:
							f.write(changed_creators_list[index])
						else:
							f.write(changed_creators_list[index] + ", ")
					f.write(")")
				previous_value = game_value
				changed_creators = set()
	
def compare_games(type):
	"""
	collect information of all games of the specific type
	
	Writes the number of games of this type played, the number of games with parameters
	changed, and any unchanged parameters to the output file, and then calls compare_parameter for any games
	with changed parameters
	
	Args:
		type: the game type that is being compared
		
	>>> compare_games("matrix") is None
	True
	"""
	cur = games.find({"creationTime" : {"$gte": date_after}, "template.type" : type, "_id" : {"$nin" : creator_games}})
	ex_game = cur[0]
	ex_game_parameters = ex_game["template"]["parameters"]
	cur.rewind()
	f.write("\n" + type + "\n")
	
	games_played = cur.count()
	f.write("Number of Games Played: " + str(games_played) + "\n")
	
	changed_parameters = []
	num_changed = 0
	
	actual_template = templates.find_one({"type" : type})
	if actual_template != None:
		actual_parameters = actual_template["parameters"]
		for game in cur:
			game_id = game["_id"]
			game_parameters = game["template"]["parameters"]
			is_modified = False
			
			
			for key in game_parameters:
				game_value = game_parameters[key]
				if key in actual_parameters:
					template_value = actual_parameters[key]
					if game_value != template_value:
						parameter_tuple = (key, template_value, game_value, game_id)
						changed_parameters.append(parameter_tuple)
						is_modified = True
						if key in ex_game_parameters:
							del ex_game_parameters[key]
				else:
					parameter_tuple = (key, None, game_value, game_id)
					changed_parameters.append(parameter_tuple)
	
			if is_modified:
				num_changed = num_changed + 1
		f.write("Number of Games with Parameters Changed: " + str(num_changed) + "\n")
		
		if len(ex_game_parameters) != 0:
			for key in ex_game_parameters:
				value = ex_game_parameters[key]
				if isinstance(value, unicode):
					value = value.encode("utf-8")
				f.write("\n\tParameter not changed: " + str(key) + "*\n\tDefault Value: " + str(value) + "\n")
		
		
		if len(changed_parameters) != 0:
			changed_parameters.sort(key= lambda tup: tup[0])
			
			previous_name = changed_parameters[0][0]
			one_parameter = []
			
			for item in changed_parameters:
				parameter_name = item[0]
				template_value = item[1]
				game_value = item[2]
				
				if previous_name != parameter_name:
					compare_parameter(one_parameter)
					previous_name = parameter_name
					one_parameter = []
					f.write("\n")
				one_parameter.append(item)
		
	else:
		f.write(type + " does not have a corresponding template \n")
	
def main():
	"""
	Main method, prints changed parameters in specified games from mongodb database onto text file
	
	Use the command prompt to specify the text file to print the results to
	Use -f or --filterdate to enter a date in mm/dd/yyyy format and remove all games before date
	Use -i or --ipaddress to enter the IP address of the remote MongoDB server to connect to
	Use -h or --help for more help
	
	>>> main() is None
	True
	"""
	global connection, games, playlists, templates, creator_games, f, date_after
	parser = argparse.ArgumentParser(description="Print changed parameters in specified games from mongodb database onto text file")
	parser.add_argument('filename', help="Enter the file name to print the results to, e.g output.txt")
	parser.add_argument('-i', '--ipaddress', default= 'localhost', help="Enter the ip address to connect mongodb to")
	parser.add_argument('-d', '--date', default = '01/01/0001', help="Enter date in mm/dd/yyyy format, removes all games before date")
	args = parser.parse_args()
	ipaddress = args.ipaddress
	month = int(args.date[0:2])
	day = int(args.date[3:5])
	year = int(args.date[6:10])
	
	f = open(args.filename, 'w')
	date_after = datetime.datetime(year, month, day, 0, 0, 0, 0)
 
	connection = pymongo.MongoClient(ipaddress, 27017)
	games = connection.moblab.games
	playlists = connection.moblab.playlists
	templates = connection.moblab.templates
	
	creator_games = filter_creators(playlists)
	games.create_index( [("template.type", pymongo.ASCENDING)])
	cur = games.find({"creationTime" : {"$gte": date_after}, "_id" : {"$nin" : creator_games}}).sort("template.type", pymongo.ASCENDING)

	previous_type = ""

	for game in cur:
		game_id = game["_id"]
		game_type = game["template"]["type"]
	
		if game_id not in creator_games:
			if game_type != previous_type:
				compare_games(game_type)
				previous_type = game_type
				f.write("\n")
	
	

if __name__ == "__main__":
	main()
	doctest.testmod()
	f.close()