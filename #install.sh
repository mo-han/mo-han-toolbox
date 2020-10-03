#!/bin/sh

cp -rp mylib ~/bin/
install -p -m 755 mykits/mykit.py ~/bin/mykit
install -p -m 755 mykits/my_tg_bot.py ~/bin/my_tg_bot
