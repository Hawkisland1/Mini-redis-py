from server import Server 
from gevent import monkey

if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    server = Server()
    print('Starting server on 127.0.0.1:31337')
    server.run()