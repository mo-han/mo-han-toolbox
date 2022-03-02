import webview.window

from mylib.ext.console_app import *

screen_width, screen_height = ostk.get_screen_size_via_tkinter()


def get_page_title(window: webview.window.Window):
    return window.evaluate_js('document.title')


def window_handler(window: webview.window.Window, title=None):
    if not title:
        sleep(.1)
        title = get_page_title(window)
        while not title:
            sleep(.1)
            title = get_page_title(window)
    window.set_title(title)


apr = ArgumentParserWrapper()
an = apr.an

an.url = an.t = an.title = ''


@apr.root()
@apr.arg(an.url)
@apr.opt(an.t, an.title)
@apr.map(an.url, an.title)
@ostk.deco_factory_pythonw_subprocess()
def view_page(url, title=None):
    parse = urllib.parse.urlparse
    r = parse(url)
    if not r.scheme:
        r = parse('http://' + url)
    w = webview.create_window(title, r.geturl(), width=int(screen_width * .7), height=int(screen_height * .7))
    webview.start(window_handler, (w, title))


def main():
    apr.parse()
    apr.run()


if __name__ == '__main__':
    main()
