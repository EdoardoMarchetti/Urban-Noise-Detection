import redis

class Redis_Client():

    def __init__(self,
                 host = 'redis-19577.c81.us-east-1-2.ec2.cloud.redislabs.com', 
                 port = 19577,
                 username = 'default',
                 password = 'so7BaeUMztM1pEpKusnIWrk9PN0nSVdm'):

        self.host = host 
        self.port = port
        self.username = username
        self.password = password



    def get_client(self):
        return redis.Redis(host= self.host, port= self.port, username= self.username, password= self.password)

