#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 现学现卖、东拼西凑的玩意
#

from pyrogram import idle
from utils import load_plugin
from utils.utils import Packages
from utils.config import client, logger, prefix

Packages('convopyro TgCrypto')

if __name__ == "__main__":
    load_plugin()
    client.start()
    me = client.get_me()
    print(me.username)
    name = me.username if me.username else me.first_name + me.last_name if me.first_name and me.last_name else me.first_name
    logger.info(f"{name}，嗨！请在任意对话框发送 {prefix}pm help pm 获取帮助~")
    idle()
