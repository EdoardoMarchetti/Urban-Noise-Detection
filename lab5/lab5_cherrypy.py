import cherrypy
import json
import redis
import uuid
from redis.commands.json.path import Path


REDIS_HOST = 'redis-11938.c293.eu-central-1-1.ec2.cloud.redislabs.com'
REDIS_PORT = 11938
REDIS_USERNAME = 'default'
REDIS_PASSWORD = 'pZIaK9HYlVQnpVCLoyqjcAUJSYsyLfIi'

# Connect to Redis server
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USERNAME, password=REDIS_PASSWORD)
is_connected = redis_client.ping()
print('Redis Connected:', is_connected)

# endpoint /status
class Status(object):
    exposed = True

    def GET(self, *path, **query):
        response_dict = {
            'status': 'online'
        }
        response = json.dumps(response_dict)

        return response

# endpoint /todos
class TodoList(object):
    exposed = True

    def GET(self, *path, **query):
        # Get all the todo keys
        keys = redis_client.keys('todo:*')
        print(keys)
        items = []

        #Check what todo items are requested
        # completed or not?
        completed = query.get('completed', None)
        if completed is not None:
            completed = bool(completed)
        #Get the message associated to query
        message = query.get('message', None)

        for key in keys:
            #Decode the key
            key = key.decode()
            #Get the relative item
            item = redis_client.json().get(key)
            #Remove the index
            uid = key.removeprefix('todo:')
            #Generate the unique id
            item['id'] = uid

            #Filter by 'completed' and 'message'
            if completed is not None and message is not None:
                if completed == item['completed'] and message in item['message']:
                    items.append(item)
            #Filter by 'completed' value
            elif completed is not None:
                if completed == item['completed']:
                    items.append(item)
            #Filter by 'message' value
            elif message is not None:
                if message in item['message']:
                    items.append(item)
            else:
            #Return all the items
                items.append(item)

        response = json.dumps(items)

        return response

    def POST(self, *path, **query):
        uid = uuid.uuid4()
        #Read the body
        body = cherrypy.request.body.read()
        #Convert the string body into a dictionary
        body_dict = json.loads(body.decode())
        
        #Create the todo item
        todo_data = {
            'message': body_dict['message'],
            'completed': False,
        }
        #Load the todo item on redis
        redis_client.json().set(f'todo:{uid}', Path.root_path(), todo_data)
        
        return

# endpoint /todo/{id}
class TodoDetail(object):
    exposed = True

    def GET(self, *path, **query):
        #Check if the path is inserted
        if len(path) != 1:
            #If not return a Bad request error
            raise cherrypy.HTTPError(400, 'Bad Request: missing id')
        #Get the requested id
        uid = path[0]
        #Get the todo item associated to uid
        item = redis_client.json().get(f'todo:{path[0]}')
        #Check if the item exists
        if item is None:
            #If not return a Not Found error
             raise cherrypy.HTTPError(404, '404 Not Found')
        #Set the id
        item['id'] = uid

        response = json.dumps(item)
        
        return response

    def PUT(self, *path, **query):
        """
            Update the item indicated in the path
        """
        #Check if the id is indicated
        if len(path) != 1:
            #If not raise a Bad Request error
            raise cherrypy.HTTPError(400, 'Bad Request: missing id')
        #Set the id
        uid = path[0]
        #Get the relative todo item
        item = redis_client.json().get(f'todo:{path[0]}')
        #Check if the item exists
        if item is None:
            #If not raise a Not Found error
            raise cherrypy.HTTPError(404, '404 Not Found')
        #Read the body
        body = cherrypy.request.body.read()
        body_dict = json.loads(body.decode())
        #Upload the todo item
        redis_client.json().set(f'todo:{uid}', Path.root_path(), body_dict)
        
        return

    def DELETE(self, *path, **query):
        if len(path) != 1:
            raise cherrypy.HTTPError(400, 'Bad Request: missing id')
        uid = path[0]
        #Try to remove the item
        found = redis_client.delete(f'todo:{uid}')
        #Check if the item has been removed
        if found == 0:
            raise cherrypy.HTTPError(404, '404 Not Found')

        return

if __name__ == '__main__':
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    cherrypy.tree.mount(Status(), '/online', conf)
    cherrypy.tree.mount(TodoList(), '/todos', conf)
    cherrypy.tree.mount(TodoDetail(), '/todo', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.engine.start()
    cherrypy.engine.block()