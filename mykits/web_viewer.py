import psutil
import webview.window

from mylib.ex.console_app import *


def get_page_title(window: webview.window.Window):
    return window.evaluate_js('document.title')


def window_handler(window: webview.window.Window):
    sleep(.1)
    title = get_page_title(window)
    while not title:
        sleep(.1)
        title = get_page_title(window)
    window.set_title(title)


apr = ArgumentParserRigger()
an = apr.an

an.url = an.t = an.title = ''


@apr.root()
@apr.arg(an.url)
@apr.opt(an.t, an.title)
@apr.map(an.url, an.title)
@ostk.deco_factory_daemon_subprocess()
def view_page(url, title='pywebview'):
    parse = urllib.parse.urlparse
    r = parse(url)
    if not r.scheme:
        r = parse('http://' + url)
    w = webview.create_window(title, r.geturl())
    webview.start(window_handler, w)


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
