import pynng

from .common_bak import *


class NanomsgRPCServer:
    @staticmethod
    def ping():
        return 'pong'

    @staticmethod
    def new_req(name: str, *args, **kwargs):
        return json.dumps(dict(name=name, args=args, kwargs=kwargs)).encode()

    def __init__(self, url):
        self.url = url
        self.__reset__()

    def __reset__(self):
        self._running = False
        self._rep_socket = pynng.Rep0()

    def __start__(self):
        if not self._running:
            t = threading.Thread(target=self.__run__, daemon=True)
            t.start()
        else:
            raise RPCError('thread still running, or stopped incorrectly')

    def __stop__(self):
        self.__send_result__(True)
        self._rep_socket.close()
        self.__reset__()

    def __run__(self):
        self._rep_socket.listen(self.url)
        self._running = True
        print('running')
        while self._running:
            try:
                q = self.__receive_request__()
                name = q['name']
                target = self.__find_call_target__(name)
                args = q['args']
                kwargs = q['kwargs']
                r = target(*args, **kwargs)
                try:
                    self.__send_result__(r)
                except pynng.BadState:
                    if name != 'stop':
                        raise
            except Exception as e:
                self.__send_error__(e)

    @lru_cache()
    def __find_call_target__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            try:
                return globals()[name]
            except KeyError:
                raise NameError(name)

    def __send_dict__(self, d):
        try:
            s = json.dumps(d, ensure_ascii=False).encode()
        except Exception as e:
            self.__send_error__(e)
        else:
            self._rep_socket.send(s)

    def __receive_request__(self):
        return json.loads(self._rep_socket.recv())

    def __send_error__(self, e: Exception):
        d = dict(ok=False, error=f'Python Exception: {type(e).__name__}: {e}')
        self.__send_dict__(d)

    def __send_result__(self, json_obj):
        d = dict(ok=True, result=json_obj)
        self.__send_dict__(d)
