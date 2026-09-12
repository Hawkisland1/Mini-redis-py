from server import Server 
from gevent import monkey

if __name__ == '__main__':
    monkey.patch_all()
    server = Server(host='0.0.0.0')
    print('Starting server on 0.0.0.0:31337')
    server.run()