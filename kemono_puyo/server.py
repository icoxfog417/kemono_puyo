import os
import json
import tornado.web
import tornado.websocket
import tornado.escape
from kemono_puyo.detector import detect_kemono


IMAGE_PATH = os.path.join(os.path.dirname(__file__), "static/_images")


class IndexHandler(tornado.web.RequestHandler):
    
    def get(self):
        cache = []
        for f in os.listdir(IMAGE_PATH):
            if os.path.isfile(os.path.join(IMAGE_PATH, f)):
                fname, _ = os.path.splitext(f)
                _, name = fname.split("_")
                cache.append((f, name))

        _data = json.dumps({"data": cache})
        self.render("index.html", cache=json.dumps(_data))

    def post(self):
        # for test
        cat_url = "https://ddnavi.com/wp-content/uploads/2014/04/0429_neko_s.jpg"
        dog_url = "https://dzwud19fd1isz.cloudfront.net/images/detailMain_pomeranian.png"
        c_and_d = "http://www.fremantle.wa.gov.au/sites/default/files/Dog-with-Cat_HD_animalplanethd.com_.jpg"
        for url in [cat_url, dog_url, c_and_d]:
            r = detect_kemono(url)
            KemonoConnection.update_cache(r)
            KemonoConnection.send_updates(r)


class KemonoConnection(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        return {}

    def open(self):
        KemonoConnection.waiters.add(self)

    def on_close(self):
        KemonoConnection.waiters.remove(self)

    @classmethod
    def update_cache(cls, path_name):
        path, name = path_name
        file_name = os.path.basename(path)
        cls.cache.append((file_name, name))
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]
        return (file_name, name)

    @classmethod
    def send_updates(cls, fname_name):
        for waiter in cls.waiters:
            try:
                waiter.write_message({"data": fname_name})
            except Exception as ex:
                print("send error: {}".format(ex))

    def on_message(self, message):
        pass


class KemonoHandler(tornado.web.RequestHandler):

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        url = data["url"]
        result = detect_kemono(url, rotate=True)
        if len(result) > 0:
            print(result)
            r = KemonoConnection.update_cache(result)
            KemonoConnection.send_updates(r)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/connect", KemonoConnection),
            (r"/kemono", KemonoHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret=os.environ.get("SECRET_TOKEN", "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"),
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)
