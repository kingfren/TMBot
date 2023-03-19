import re
from pathlib import Path
from importlib import import_module

from packaging import version as v

from utils.config import version, plugins_dir, logger
from utils.utils import scheduler, PLUGINS

scheduler.start()

def import_plugin(plugin):
    try:
        import_module(plugin)
        return True
    except Exception as e:
        logger.error(f'failed to import :{plugin}\n {e}')
        return False

def load_plugin():

    PLUGINS.init()

    import_plugin('utils.pm')

    root = 'data/plugins'

    for path in sorted(Path(root).glob("*.py")):
        module_path = '.'.join(path.parent.parts + (path.stem,))

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        ver = re.search('(?<=ver\=(\'|\")).+?(?=(\'|\"))', text)

        if v.parse(version) >= v.parse(ver.group(0)):
            import_plugin(module_path)
        else:
            logger.error(f'failed to import {module_path}: Version Mismatch Error')
