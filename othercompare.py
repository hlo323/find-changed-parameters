import pymongo
import sys

connection = pymongo.MongoClient("mongodb://localhost")

db = connection.test
games = db.games
template = db.template
f = open("myfile.txt", "w")


def compare_one_game(item):
	game_template = item["template"]
	game_name = game_template["name"]
	game_parameters = game_template["parameters"]
	
	actual_template = template.find_one({"name" : game_name}, {"parameters" : 1, "_id" : 0})
	actual_parameters = actual_template["parameters"]
	
	for key in game_parameters:
		game_value = game_parameters[key]
		template_value = actual_parameters[key]
		print game_value
		print template_value
		#if game_value != template_value:
			#f.write("Parameter: " + str(key) + "\nDefault Parameter: " + str(template_value) + "\nChanged Parameter: " +str(game_value)+ "\n")
			
def is_changed(item):
	game_template = item["template"]
	game_name = game_template["name"]
	game_parameters = game_template["parameters"]
	
	actual_template = template.find_one({"name" : game_name}, {"parameters" : 1, "_id" : 0})
	actual_parameters = actual_template["parameters"]
	
	for key in game_parameters:
		game_value = game_parameters[key]
		template_value = actual_parameters[key]
		if game_value != template_value:
			return True
	return False

def compare_many_games(name):
	#f.write(name + "\n")
	
	number = games.find({"template.name" : name}).count()
	#f.write("Number of Games Played: " + str(number)+ "\n")
	
	changed = 0
	cur = games.find()
	for item in cur:
		game_name = item["template"]["name"]
		if game_name == name and is_changed(item):
			changed = changed + 1
	#f.write("Number of Games with Parameters Changed: " + str(changed)+"\n")
	
	cur = games.find()
	for item in cur:
		game_name = item["template"]["name"]
		if game_name == name:
			compare_one_game(item)

def compare_collection():			
	cur = games.find().sort("template.name", pymongo.ASCENDING)
	previous_name = ""
	for item in cur:
		game_name = item["template"]["name"]
		if game_name != previous_name:
			compare_many_games(game_name)
			previous_name = game_name
			#f.write("\n")

compare_collection()