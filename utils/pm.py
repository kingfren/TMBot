'''获取插件信息和插件管理'''
import os
import re
import sys
import git
import json
import asyncio
import requests
import importlib
from pathlib import Path
from ast import literal_eval
from bs4 import BeautifulSoup
from packaging import version as v

from utils import import_plugin
from utils.utils import Packages, PLUGINS, scheduler, oncmd
from utils.config import client, version, prefix, base_dir, plugins_dir, conf, config

from pyrogram import filters

def get_args(mgs):
    args = {}
    for i, arg in enumerate(mgs.text.strip().split()):
        args[i] = arg
    return args

def restart():
    os.execv(sys.executable, [sys.executable] + sys.argv)

def get_url(url):
    with requests.Session() as s:
        r = s.get(url)
        if not r.ok:
            return False
        return r.text

def get_plugins():
    result = get_url('https://github.com/noreph/TMBot-Plugins/raw/main/.plugin_list')

    if result is False:
        return False

    dct = literal_eval(result)

    for i in dct:
        dct[i]['url'] = f'https://github.com/noreph/TMBot-Plugins/raw/main/{i}.py'

    return dct

async def install(url, plugin):
    flag = plugin in PLUGINS.dct()
    content = get_url(url)
    packages = re.search('(?<=(Packages\((\'|\"))).+(?=(\'|\")\))', content)
    if packages:
        if not Packages(packages.group()):
            return False
    with open(f'{plugins_dir}/{plugin}.py', "w+") as f:
        f.write(content)
    root = 'data/plugins'
    path = Path(root, plugin)
    module_path = '.'.join(path.parent.parts + (path.stem,))

    if flag:
        try:
            importlib.reload(sys.modules[module_path])
            return True
        except Exception as e:
            logger.error(f"reload error: {module_path}:\n{e}")
            return False
    else:
        if import_plugin(module_path):
            return True
        else:
            return False

def plist():
    lst = []
    plugins = PLUGINS.dct()
    for plugin in plugins:
        if plugins[plugin]['type'] in ['cmd', 'sys']:
            lst.append(plugins[plugin]['cmd'])
        if plugins[plugin]['type'] != 'sys':
            lst.append(plugins[plugin]['name'])
    return lst

@oncmd(cmd='pm')
async def handler(client, message):
    '''
1、查看已安装插件列表：
`pm`

2、查看插件、指令信息：
`pm help <插件名>/<指令>`

3、升级程序：
`pm update`

4、升级插件：
`pm update plugin`

5、获取可用插件列表：
`pm list`

6、安装插件：
    安装部分插件：
    `pm add <插件 1> <插件 2> <插件 3>`
    安装所有插件：
    `pm add all`

7、删除插件：
    删除已安装插件：
    `pm del <插件名>`
    删除所有已安装插件：
    `pm del all`

8、修改配置：
    `pm set <插件名>`

9、重启：
`pm restart`
    '''
    args = get_args(message)
    content = f'🤖 **TMBot v{version}**\n'
    content += f'▍ `{message.text}`\n\n'
    plugins = PLUGINS.dct()

    async def del_msg(msg, t: int = 30):
        await asyncio.sleep(t)
        try:
            await msg.delete()
        except Exception:
            pass

    async def get_list(content):
        await message.edit(content + '获取列表中...')

        dct = get_plugins()

        if not dct:
            await message.edit(content + "插件列表获取失败~")
            return

        content += '可用插件列表:\n'
        for i in list(dct.keys()):
            content += f"`{i}`：{dct[i]['desc']}\n"
        await message.edit(content)
        await del_msg(message, 60)

    async def add(content):
        for i in list(args.keys())[:2]:
            del args[i]

        if not args:
            content += '缺少参数~'
            await message.edit(content)
            return

        await message.edit(content + "获取插件中...")

        dct = get_plugins()

        if not dct:
            await message.edit(content + "插件列表获取失败~")
            return

        lst = list(dct.keys())

        content += f"安装：\n"
        await message.edit(content)
        if args.get(2) == 'all':
            for i in dct:
                content += f"`{i}`...\n"
                await message.edit(content)
                await asyncio.sleep(2)
                if v.parse(version) >= v.parse(dct[i]['ver']):
                    if await install(dct[i]['url'], i):
                        content = content.replace(f"`{i}`...\n", f"`{i}`...✓ \n")
                        await message.edit(content)
                    else:
                        content = content.replace(f"`{i}`...\n", f"`{i}`...✗ ：安装失败\n")
                        await message.edit(content)
                else:
                    content = content.replace(f"`{i}`...\n", f"`{i}`...✗ ：要求版本 {dct[i]['ver']}\n")
                await asyncio.sleep(1)
            await message.edit(content + f'\n发送 `{prefix}pm` 获取帮助~')
        else:
            for i in list(args.values()):
                if i in lst:
                    content += f"`{i}`...\n"
                    await message.edit(content)
                    await asyncio.sleep(2)
                    if v.parse(version) >= v.parse(dct[i]['ver']):
                        if await install(dct[i]['url'], i):
                            content = content.replace(f"`{i}`...\n", f"`{i}`...✓ \n")
                            await message.edit(content)
                        else:
                            content = content.replace(f"`{i}`...\n", f"`{i}`...✗ ：安装失败\n")
                            await message.edit(content)
                    else:
                        content = content.replace(f"`{i}`...\n", f"`{i}`...✗ ：要求版本 {dct[i]['ver']}\n")
                else:
                    content += f"`{i}` 不存在~\n"
                    await message.edit(content)
                await asyncio.sleep(1)
            await message.edit(content + f'\n发送 `{prefix}pm` 获取帮助~')

        await del_msg(message)

    async def delete(content):
        if not args.get(2):
            content += '缺少参数~'
            await message.edit(content)
            return
        plugins = PLUGINS.dct()
        if args.get(2) and args.get(2) == 'all':
            await message.edit(content + '即将删除所有插件~\n')
            for plugin in list(plugins):
                if plugins[plugin]['type'] != 'sys':
                    PLUGINS.delete(plugin)
            await message.edit(content + '已删除所有插件~\n')

        elif args.get(2) and args.get(2).replace(prefix, "") in plist():
            for plugin in plugins:
                if args.get(2).replace(prefix, "") == plugins[plugin]['name'] or args.get(2).replace(prefix, "") == plugins[plugin]['cmd']:
                    if plugins[plugin]['type'] == 'sys':
                        await message.edit(content + f"系统插件 {arg} 无法删除~")
                        return
                    content += f"删除插件 `{plugin}`...\n"
                    await message.edit(content)
                    await asyncio.sleep(2)
                    if plugins[plugin]['type'] in ['cmd', 'msg']:
                        PLUGINS.delete(plugin)
                        break
                    elif plugins[plugin]['type'] == 'sched':
                        PLUGINS.delete(plugin)
                        break
            content = content.replace(f"删除插件 `{plugin}`...\n", f"已删除插件：`{plugin}`\n")
            await message.edit(content)

        else:
            content += f'`{args.get(2)}` 不存在~' 
            await message.edit(content)

        await del_msg(message)


    async def update(content):
        dct = get_plugins()
        plugins = PLUGINS.dct()

        match args.get(2):
            case 'plugin':
                if not (len(plugins) == 1 and 'pm' in plugins):
                    content += '更新插件：\n'
                    await message.edit(content)

                    for plugin in plugins:
                        if plugins[plugin]['type'] != 'sys':
                            if plugin in dct:
                                if plugins[plugin]['ver'] != dct[plugin]['ver']:
                                    content += f"`{plugin}`...\n"
                                    await message.edit(content)
                                    if await install(dct[plugin]['url'], plugin):
                                        content = content.replace(f"`{plugin}`...\n", f"`{plugin}`...✓：更新成功~ \n")
                                        await message.edit(content)
                                    else:
                                        content = content.replace(f"`{plugin}`...\n", f"`{plugin}`...✗：更新失败~ \n")
                                        await message.edit(content)
                                else:
                                    content += f"`{plugin}`：暂无更新~ \n"
                                    await message.edit(content)
                            await asyncio.sleep(1)
                    await del_msg(message)
                else:
                    await del_msg(await message.edit(content + "未装插件~"))

            case _:
                content += '\n更新程序中...'
                await message.edit(content)
                try:
                    update = git.cmd.Git(base_dir)
                    result = update.pull()
                    if result == 'Already up to date.':
                        content = content.replace('\n更新程序中...', '\n程序暂无更新~')
                    elif result.find("Fast-forward") > -1:
                        content = content.replace('\n更新程序中...', f'''\n更新完成，即将重启：\n```{result}```''')
                        await message.edit(content)
                        await del_msg(message, 3)
                        restart()
                    else:
                        content = content.replace('\n更新程序中...', f'''\n更新出错：\n```{result}```''')
                except Exception as e:
                    content = content.replace('\n更新程序中...', f'''\n更新出错：```\n{e}```''')
                await message.edit(content)
                await del_msg(message)

    async def get_help(content):
        if not args.get(2):
            content += '缺少参数~'
            await message.edit(content)
            return

        plugin = args.get(2).replace(prefix,"")
        if plugin not in plist():
            content += f'`{args.get(2)}` 不存在~'
            await message.edit(content)
            return

        if not plugins.get(plugin):
            for i in plugins:
                if plugins[i]['cmd'] == plugin:
                    plugin = plugins[i]['name']
                    break

        content += f'**{args.get(2)}** 的信息：\n\n'

        if plugins[plugin]['type'] in ['sys', 'cmd']:
            content += f"命令：`{prefix}{plugins[plugin]['cmd']}`\n"

        content += f"版本需求：`{plugins[plugin]['ver']}`\n"
        content += f"插件名：`{plugins[plugin]['name']}`\n\n"

        content += f"{plugins[plugin]['help']}\n"

        if plugins[plugin]['doc']:
            content += f"{plugins[plugin]['doc']}\n"

        await message.edit(content)
        await del_msg(message)

    async def pm(content):
        sys, cmds, msgs, scheds = {}, {}, {}, {}
        for plugin in plugins:
            if plugins[plugin]['type'] == 'sys':
                sys[plugins[plugin]['cmd']] = plugins[plugin]['help']
            if plugins[plugin]['type'] == 'cmd':
                cmds[plugins[plugin]['cmd']] = plugins[plugin]['help']
            if plugins[plugin]['type'] == 'msg':
                msgs[plugins[plugin]['name']] = plugins[plugin]['help']
            if plugins[plugin]['type'] == 'sched':
                scheds[plugins[plugin]['name']] = plugins[plugin]['help']

        for i in sys:
            content += f"`{prefix}{i}`：{sys[i]}\n"

        if cmds:
            content += "\n**命令列表**\n"
            for i in cmds:
                content += f"`{prefix}{i}`：{cmds[i]}\n"

        if msgs:
            content += "\n**无命令插件**\n"
            for i in msgs:
                content += f"`{i}`：{msgs[i]}\n"

        if scheds:
            content += "\n**定时插件**\n"
            for i in scheds:
                content += f"`{i}`：{scheds[i]}\n"

        await message.edit(content)
        await del_msg(message)

    async def setting(content):
        async def func(_, __, m):
            if m.reply_to_message:
                return m.reply_to_message_id == message.id

        _filter = filters.create(func)

        async def listen():
            msg = await client.listen.Message(_filter, filters.user(message.from_user.id), timeout = 300)
            if msg:
                await client.listen.Cancel(filters.user(message.from_user.id))
                return msg
            return False

        conf.read(config)
        text = str()
        for i in conf.sections():
            try:
                desc = f"：{conf[i]['desc']}"
            except Exception:
                desc = ''
            text += f"`{i}`{desc}\n"
        await message.edit(content + f"请选一个配置回复进行编辑：\n{text}")

        while True:
            msg = await listen()
            if not msg:
                await del_msg(await message.edit(content + "回复超时，请重试~"))
                return
            await msg.delete()

            if msg.text in conf:
                me = await client.get_me()
                if "only_me" in conf[msg.text] and conf.getboolean(msg.text, 'only_me') and message.chat.id != me.id :
                    return await del_msg(await message.edit(content + "此部分配置仅允许在 Saved Messages 里编辑~"))

                global section
                section = msg.text
                dct = {x:y for x,y in conf.items(msg.text)}
                await message.edit(content + f"请按照如下格式回复新配置：\n`{dct}`")
                continue

            try:
                global sections
                sections = json.loads((msg.text).replace("'","\""))
            except Exception:
                await del_msg(await message.edit(content + "格式错误，请重试~"))
                return
            else:
                conf[section] = sections
                with open(config, 'w') as configfile:
                    conf.write(configfile)
                await del_msg(await message.edit(content + "修改完成，部分配置需重启后生效~"))
                return

    match args.get(1):
        case 'help':
            await get_help(content)
        case 'update':
            await update(content)
        case 'list':
            await get_list(content)
        case 'add':
            await add(content)
        case 'del':
            await delete(content)
        case 'set':
            await setting(content)
        case 'restart':
            await del_msg(message, 1)
            restart()
        case _:
            await pm(content)
