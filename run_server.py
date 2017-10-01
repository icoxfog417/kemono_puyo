import os
import shutil
import tornado.ioloop
import tornado.httpserver
import tornado.escape
from tornado.options import define, options
from kemono_puyo.server import Application, IMAGE_PATH


"""
if os.path.isdir(IMAGE_PATH):
    shutil.rmtree(IMAGE_PATH)
os.mkdir(IMAGE_PATH)
"""


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    port = int(os.environ.get("PORT", 8080))
    print("server is running on port {0}".format(port))
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
