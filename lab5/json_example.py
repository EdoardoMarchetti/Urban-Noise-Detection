import json
import os


my_dict = {
    'name': 'Tony',
    'surname' : 'Stark',
    'age' : 40,
    'hobbies' : ['sport', 'music', 'tech']
}

print(type(my_dict))
print(my_dict)

#Convert the dict in a string with json
my_str = json.dumps(my_dict)
print(type(my_str))
print(my_str)

filename = os.path.join('.','lab5/example.json')

#Save the dict as a json file
with open(filename, 'w') as fp:
    json.dump(my_dict, fp)

#Read the json file as store the result as a dictionary
with open(filename, 'r') as fp:
    new_dict = json.load(fp)

print(f'\n Loaded dict {new_dict}')


