import argparse
from .http_app import serve

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=8080)
    a=p.parse_args()
    serve(a.host,a.port)

if __name__=='__main__':
    main()
