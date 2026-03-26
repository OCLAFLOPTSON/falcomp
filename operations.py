from subprocess import (
    check_output, run as sprun,
    Popen, CompletedProcess, TimeoutExpired, CalledProcessError,
    PIPE, STDOUT
)
from json import loads, dumps, JSONDecodeError
from pathlib import Path
from shutil import get_terminal_size
from os import get_terminal_size
from sys import stdout, stdin
from hashlib import sha256
from time import sleep
from serial import Serial

from falco_mp.falcomp.color_theme import ANSITAG
from falco_mp.falcomp.keys import key_incoming, read_key

def file_hash(path):
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def size():
    try:
        return get_terminal_size()
    except:
        pass

    try:
        return get_terminal_size(stdout.fileno())
    except:
        pass

    try:
        return get_terminal_size()
    except:
        pass
    
    return (80, 24)

class ActionCall:
    def __init__(self, action: str):
        self.action = action
    def __repr__(self):
        return f"::action:: -> {self.action}"

class Config:

    def update(port: str, current: dict):
        '''Perform a diff and update config file at port if changes
        detected.'''
        old = Config.get(port)
        if current != old:
            MPCommands.write_file(port, 'config.json', dumps(current))
            print(ActionCall("Updated Config File"))
    
    def new(port):
        _d = MPCommands.get_connected_devices()
        x = False
        for device in _d:
            device: Device
            if device.port == port:
                serial = device.serial
                x = True
                break
        if not x:
            serial = "E"
        return dumps({
            'name': 'UNSET',
            'serial': serial,
            'confirm-on-sync': True,
            'preserve-device-files': False,
            'ignore': [
                "env/",
                "typings/",
                "__pycache__"
            ],
            'notes': []
        })
    
    def get(port) -> dict|bool:
        '''
        #### Get the config file from the given port.
        <hr>

        If no config.json exists, creates one.

        If json.loads fails, returns False.
        '''
        if not MPCommands.file_exists(port, 'config.json'):
            MPCommands.write_file(port, 'config.json', Config.new(port))
        config = MPCommands.read_file(port, 'config.json')
        try:
            config = loads(config)
        except JSONDecodeError:
            config = False
        
        return config

class FSCommands:
    file_system = 'fs'
    _copy = "cp"
    remove_file = "rm"
    remove_directory = "rmdir"
    read_file = "cat"
    make_directory = "mkdir"
    recursive = "-r"

    def new_directory(path):
        return [
            FSCommands.file_system,
            FSCommands.make_directory,
            ":"+path
        ]

    def delete(file_path: bool|str=False, directory: bool=False):
        '''
        #### Construct a remove file command to be used with mpremote.
        <hr>

        ##### directory
        - If False, supply rm command. Else rmdir
        '''
        if not directory:
            return [
                FSCommands.file_system,
                FSCommands.remove_file,
                ":"+file_path
            ]
        return [
            FSCommands.file_system,
            FSCommands.remove_file,
            FSCommands.recursive,
            ":"+file_path
        ]

    def copy(local_path, device_path, render=False, emit=True,
                  directory: bool=False) -> list[str]|str:
        '''
        #### Return a file-copy command to be used with mpremote.
        <hr>

        ##### render
        - If True, return a rendered string instead of list[str]

        ##### emit
        - If True, copy from local to device. If False, copy from
        device to local.

        ##### directory
        - If True, inserts the -r flag before the path arguments to
        recursively copy the directory at path.
        '''
        if emit:
            cmd = [
                FSCommands.file_system,
                FSCommands._copy,
                local_path,
                ":"+device_path
            ]
        else:
            cmd = [
                FSCommands.file_system,
                FSCommands._copy,
                ":"+device_path,
                local_path
            ]
        if directory:
            cmd.insert(2, FSCommands.recursive)
        if not render:
            return cmd
        
        return " ".join(cmd)

def mp_command(port: str, interrupt: bool=False, soft_reset: bool=False,
               repl: bool=False, mount: bool|list[str]=False,
               execute: bool|str|list[str]=False, run: bool|str=False,
               filesystem: bool|list[str]=False):
    '''
    Construct an mpremote command.\n
    Evaluates keyword arguments according to an order of operations.\n
        - ###### Order of Operations
        - ###### interrupt
        - ###### soft_reset
        - ###### repl
        - ###### mount
        - ###### execute
        - ###### run
    Everything in the sequence below soft_reset is an endpoint. For
    example:\n
        ```python
mp_command(
    "COM11",
    soft_reset=True,
    mount=('src/', 'run', 'main.py'),
    execute=('import main', 'import other_module')
)
        ```
    Nothing from the execute node forward is reachable since mount is
    truthy, resulting in an exit before trailing kwargs could be evaluated.\n
    <h1>KWARGS</h1>
    <hr>

    #### port
    - A string literal referencing the port to which to connect.
    - Passing "list" to port returns list devices command. 
    ### interrupt
    - If True, inserts the interrupt command at the beginning of the sequence.
    #### soft_reset
    - True or False. If True, inserts a soft reset before the given command
    but after the interrupt command, if applicable.
    #### repl
    - If true, exits with start repl command.
    #### mount
    - A list with the order (path, cmd, *args), where path is the path to
        which to mount, cmd is a string[command] i.e "run", *args are all
        optional arguments such as filepaths.
    #### execute
    - If not false must be either a single string or list of strings which
    are python operations.
    #### run
    - If not False must be a string that is the filepath to the file on the
    device which will be run.
    #### filesystem
    - If not False must be a list of fs commands.
    '''
    _cmd = ["mpremote", "connect", port]
    if port == "list":
        return _cmd

    if interrupt:
        _cmd.append('interrupt')

    if soft_reset:
        _cmd.append('soft-reset')

    if repl:
        _cmd.append('repl')
        return _cmd

    if mount:
        _cmd.append('mount')
        _cmd.append(mount[0])
        _cmd.append(mount[1])
        for arg in mount[2:]:
            _cmd.append(arg)
        return _cmd
            
    if execute:
        _cmd.append('exec')
        if type(execute) is list:
            for stmt in execute:
                _cmd.append(stmt+";")
        elif type(execute) is str:
            _cmd.append(execute+";")
        return _cmd
    
    if run:
        _cmd.append('run')
        _cmd.append(run)
        return _cmd
    
    if filesystem:
        if type(filesystem) is list:
            _cmd = _cmd+filesystem
            return _cmd

class Device:
    def __init__(self, port, serial, data):
        self.port = port
        self.serial = serial
        self.data = data
        
class MPCommands:
    '''A library of mpremote operations.'''
    def remote_execute(port, script: str, timeout: None|float=None):
        """
        Remotely execute an arbitrary script. Returns the output.
        """
        result: CompletedProcess = sprun(
            mp_command(port, soft_reset=True, execute=script),
            capture_output=True,
            text=True,
            timeout=timeout if timeout else 0
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    def generate_stubs(port):
        print("Generating stubs...")
        root = Path.cwd() / "typings"
        root.mkdir(exist_ok=True)

        def _modules(port):
            result: str = MPCommands.remote_execute(
                port,
                "help('modules')",
                timeout=5
            )
            modules = []
            for _n in result.split():
                if _n.isidentifier():
                    modules.append(_n)
            return sorted(set(modules))
        
        def _get_attributes(port, module: str):
            script = [
                'from json import dumps\n',
                'try:\n',
                f'  import {module}\n',
                'except:\n',
                '  print(str(dict()))\n',
                '  raise SystemExit\n',
                'attrs = dict()\n',
                f'for name in dir({module}):\n',
                '  try:\n',
                f'    attr = getattr({module}, name)\n',
                f'    if type(attr).__name__ == "type":\n',
                f'      kind = "class"\n',
                f'    elif callable(attr):\n',
                f'      kind = "function"\n',
                f'    else:\n',
                f'      kind = "var"\n',
                f'    attrs[name] = kind\n'
                '  except Exception as e:\n',
                '    print(e)\n',
                'print(dumps(attrs))'
            ]
            try:
                out = MPCommands.remote_execute(
                    port,
                    ''.join(script),
                    timeout=5
                )
            except TimeoutExpired:
                print(f"::!timeout!:: Skipping {module} due to timeout error.")
                return {}
            
            start = out.find("{")
            end = out.rfind("}")

            if start == -1:
                return {}
            return loads(out[start:end + 1])
        
        def _write_stub(module: str, attrs: dict, root: Path):
            try:
                path = root / f"{module}.pyi"
                with path.open("w", encoding="utf8") as f:
                    f.write(f"# {module} Stub generated by falco-mp.\n\n")
                    for name, kind in sorted(attrs.items()):
                        if name.startswith("_"):
                            continue
                        if kind == "class":
                            f.write(f"class {name}:\n")
                            f.write("    ...\n\n")
                        elif kind == "function":
                            f.write(f"def {name}(*args, **kwargs): ...\n\n")
                        else:
                            f.write(f"{name}: object\n")
            except Exception as e:
                print(e)
        
        modules = _modules(port)
        # exit(str(modules))
        for module in modules:
            if module.startswith("_"):
                continue
            print(f"::discovered:: {module}")

            try:
                attrs = _get_attributes(port, module)
                _write_stub(module, attrs, root)
            except Exception as e:
                print(e)

        print("::success:: Stub Generation Successful.")
    
    def interrupt(port):
        '''Send an interrupt sequence to a given port.'''
        with Serial(port, 115200, timeout=1) as s:
            sleep(0.1)
            s.write(b'\x03\x03\x03')

    def run_file(port, path: str='main.py'):
        '''
        Run the python file at a given path.
        '''
        _p = False
        if "/" in path:
            _p = True
            path, name = path.rsplit('/', 1)
            if '.' in name:
                name, ext = name.split('.')
                if ext != 'py':
                    return
            path = path.split('/')
            path = '.'.join(path)
            ext = ''
        else:
            name, ext = path.split('.')
            if ext != 'py':
                return
        script = 'import ' + (path+'.'+name if _p else name)

        print(ANSITAG.reset)
        try:
            _x = sprun(mp_command(port, soft_reset=True, execute=script))

        except Exception as e:
            print(e)

        finally:
            active = True
            print('\n\n\n  ~ Script exited successfully. ~\npress any key to exit')
            while active:
                if key_incoming():
                    read_key()
                    active = False
            
            MPCommands.interrupt(port)
    
    def run_repl(port):
        print(ANSITAG.reset)
        sprun(['mpremote', 'connect', port, 'soft-reset', 'repl'])
    
    def get_device_file_hash(port):
        """
        
        """
        script = [
            'from hashlib import sha256\n',
            'from os import walk\n',
            'def file_hash(path):\n',
            '    h = sha256()\n',
            '    with open(path, "rb") as f:\n',
            '        while True:\n',
            '            chunk = f.read(512)\n',
            '            if not chunk:\n',
            '                break\n',
            '            h.update(chunk)\n',
            '    return h.hexdigest()\n',
            'files = dict()\n',
            'for root, dirs, filenames in os.walk("/"):\n',
            '    for name in filenames:\n',
            '        path = root + "/" + name if root != "/" else "/" + name\n',
            '        try:\n',
            '            files[path] = file_hash(path)\n',
            '        except:\n',
            '            pass\n',
            'print(files)\n'
        ]

    def scan_all_files(port):
        '''
        #### Return a dict containing the full filetree on the device.
        <hr>

        *Performs recursive operation.
        #### Data Structure

        ``` python
        file_scan = {
            'folders': {
                {
                'size': <* filesize *>,
                'path': <* path *>,
                'files': {etc...},
                'folders': {etc...}
                },
                etc...
            },
            'files': {
                {
                'size': <* filesize *>,
                'path': <* path *>
                },
                etc...
            }
        }
        ```
        '''
        print(f"{ANSITAG.color(60, 60, 100)}::filescan:: Scanning device at {port}{ANSITAG.reset}\n")
        cwd = ''
        out = {'files': {}, 'folders': {}}
        def _r_check(cwd, out):
            def _hash_device_file(port, path):
                script = [
                    'from hashlib import sha256\n',
                    'from binascii import hexlify\n',
                    'h = sha256()\n',
                    f'with open("{path}", "rb") as f:\n',
                    '    while True:\n',
                    '        chunk = f.read(4096)\n',
                    '        if not chunk:\n',
                    '            break\n',
                    '        h.update(chunk)\n',
                    'print(hexlify(h.digest()).decode())'
                ]
                try:
                    return check_output(
                        mp_command(port, execute=''.join(script)),
                        text=True
                    )
                except CalledProcessError as e:
                    print(e.output)

            files: str = check_output(
                mp_command(port,soft_reset=True, filesystem=['fs', 'ls', '-r', f':{cwd}']),
                text=True
            )
            for file in files.splitlines()[1:]:
                file = file.lstrip().split()
                name = file[1]
                path = cwd+name

                if "." in name:
                    out['files'][name] = {
                        'size': file[0],
                        'path': path,
                        'hash': _hash_device_file(port, path)
                    }
                    continue

                out['folders'][name] = {
                    'size': file[0],
                    'path': path,
                    'files': {},
                    'folders': {}
                }
                
                print(f"::discovered:: {name}")
                _r_check(path,out['folders'][name])

        _r_check(cwd,out)
        return out

    def scan_local_files(port):
        '''
        Return a dict matching the device filetree structure.
        '''
        print(f"{ANSITAG.color(60, 60, 100)}::filescan:: Scanning local working directory{ANSITAG.reset}\n")
        root = Path.cwd()
        ignore = Config.get(port).get('ignore')

        def _scan(path: Path, ignore: list):
            out = {'files': {}, 'folders': {}}
            for p in path.iterdir():
                if p.name in ignore:
                    continue
                if p.is_file():
                    out['files'][p.name] = {
                        'size': p.stat().st_size,
                        'path': str(p.relative_to(root).as_posix()),
                        'hash': file_hash(str(p.relative_to(root).as_posix()))
                    }

                elif p.is_dir():
                    name = p.name+"/"
                    out['folders'][name] = {
                        'size': 0,
                        'path': str(p.relative_to(root)).replace("\\", "/")+"/",
                        'files': {},
                        'folders': {}
                    }

                    out['folders'][name].update(_scan(p, ignore))
                print(f"::discovered:: {str(p.relative_to(root).as_posix())}")

            return out

        return _scan(root, ignore)
    
    def sync_working_directory(port):
        '''
        ### ! PERFORMS DEVICE WRITE OPERATIONS ! \n
        <hr>

        #### Sync the working directory to device.
        - Diff files
        - Update if changes detected
        - Ignores names found in config['ignore'] (device config.json file)
        '''
        config = Config.get(port)
        preserve = config.get('preserve-device-files', False)
        ignore = config.get('ignore', list())

        local_directory = MPCommands.scan_local_files(port)
        device_directory = MPCommands.scan_all_files(port)

        diff = {
            "files_added": [],
            "files_removed": [],
            "files_modified": [],
            "folders_added": [],
            "folders_removed": []
        }

        def _diff(_local, _peripheral):
            local_files = _local.get("files", {})
            peripheral_files = _peripheral.get("files", {})

            local_keys = set(local_files.keys())
            peripheral_keys = set(peripheral_files.keys())

            ################################################### Device , Local
            for name in sorted(local_keys - peripheral_keys): # missing, exists
                if name in ignore:
                    continue
                path = local_files[name]["path"]
                diff["files_added"].append(path)
                print(f"::copy:: {name}")
                
                check_output(
                    ['mpremote', 'connect', port, 'soft-reset', 'fs', 'cp', path, ":"+path],
                    text=True
                )

            for name in sorted(peripheral_keys - local_keys): # exists, missing
                path = peripheral_files[name]["path"]
                if path == 'config.json':
                    continue
                if preserve:
                    continue
                diff["files_removed"].append(path)
                print(f"::delete:: {name}")

                MPCommands.delete_file(port, path)

            for name in sorted(local_keys & peripheral_keys): # exists, exists
                if local_files[name]["hash"] != peripheral_files[name]["hash"]:
                    path = local_files[name]["path"]
                    diff["files_modified"].append(path)
                    print(f"::update:: {name}")
                
                    check_output(
                        ['mpremote', 'connect', port, 'soft-reset', 'fs', 'cp', path, ":"+path],
                        text=True
                    )

            # FILES
            local_folders = _local.get("folders", {})
            peripheral_folders = _peripheral.get("folders", {})

            local_keys = set(local_folders.keys())
            peripheral_keys = set(peripheral_folders.keys())

            ################################################### Device , Local
            for name in sorted(local_keys - peripheral_keys): # missing, exists
                if name in ignore:
                    continue
                path = local_folders[name]["path"]

                if not MPCommands.file_exists(port, path):
                    diff["folders_added"].append(path)
                    MPCommands.new_folder(port, path)

                _diff(local_folders[name], {"files": {}, "folders": {}})

            ################################################### exists, missing
            for name in sorted(peripheral_keys - local_keys, key=lambda n: -len(peripheral_folders[n]["path"])):
                if preserve:
                    continue
                path = peripheral_folders[name]["path"]
                diff["folders_removed"].append(path)

                MPCommands.delete_file(port, path, folder=True)

            ################################################### exists, exists
            for name in sorted(local_keys & peripheral_keys):
                _diff(local_folders[name], peripheral_folders[name])

        _diff(local_directory, device_directory)
        return diff
    
    def delete_file(port, path, folder=False):
        check_output(
            mp_command(port, soft_reset=True, filesystem=FSCommands.delete(path, folder)),
            text=True
        )

    def read_file(port, path):
        '''#### Performs a read operation on the device at port. Returns
        the raw file with newline characters intact.'''
        script = [
            f'with open("{path}", "r") as f:\n',
            '    print(f.read())'
        ]
        return check_output(
            mp_command(
                port,
                soft_reset=True,
                execute=''.join(script)
            ),
            text=True
        )

    def write_file(port: str, path: str, text: bool|str=False, jsonify: bool|dict=False):
        '''
        #### Write a file at the given path on the device at port.
        - If no file exists, creates new file.

        <hr>
        '''
        if text and not jsonify:
            script = [
                f'with open("{path}", "w") as f:\n',
                f"    f.write('{text}')"
            ]
            script = ''.join(script)
        elif jsonify and not text:
            script = [
                f'from ujson import dumps\n',
                f'with open("{path}", "w") as f:\n',
                f'    f.write(dumps({jsonify!r}))'
            ]
        else:
            script = f'open("{path}", "w").close()'
        check_output(
            mp_command(
                port,
                soft_reset=True,
                execute=script
            ),
            text=True
        )
    
    def new_folder(port, path):
        check_output(
            mp_command(port, soft_reset=True, filesystem=FSCommands.new_directory(path)),
            text=True
        )
        
    def copy_file(port, path, emit:bool=True, directory: bool=False):
        command = [
            "mpremote",
            'connect',
            port,
            "fs",
            "cp",
            path if emit else f":",
            f":" if emit else path
        ]
        if directory:
            command.insert(5, "-r")
        check_output(command, text=True)
    
    def device_directory_layer(port, path:str="/"):
        '''-> {folders: dict, files: dict, name: str, path: str}'''
        script = [
            "from os import listdir\n",
            "from json import dumps\n",
            f"directory = listdir('{path}')\n",
            "print(dumps(directory))"
        ]
        directory = loads(check_output(
            mp_command(port, soft_reset=True, execute=''.join(script)),
            text=True
        ))
        if path != "/":
            name = path.split("/")
            name = name[(len(name)-1 if name[len(name)-1] else len(name)-2)]
        else:
            name = 'ROOT'
            path = ''
        out = {'folders': {},'files': {}, 'name': name}
        for file in directory:
            if file.find(".") >= 0:
                out['files'][file] = {'name': file, "path": path+file}
                continue
            file = f"{file}/"
            out['folders'][file] = {'name': file, 'path': path+file}

        out['path'] = path

        return out
    
    def device_filetree(port):
        '''
        Generate filetree from the device at a given port.
        <hr>

        - #### Filetree consists of dict with four nodes:
            - folders
            - files
            - name
            - path
        \n
        <hr>

        #### folders
        - A dict containing additional layers. Empty if no folders exist
        at the current level.

        <hr>

        #### files
        - A list of filenames with extensions.

        <hr>

        #### name
        - A string containing the label for the current level of the directory.

        <hr>

        #### path
        - the whole file path to the current level of the directrory. 

        <hr>

        The path to a given file can be constructed by <*filetree*>[<*node_path*>]['path'] + files[index]
        '''
        def check_for_folders(port, layer):
            work_done = False
            for key in layer['folders'].keys():
                    layer['folders'][key] = MPCommands.device_directory_layer(port, key[:len(key)-1])
                    work_done = True
                    if work_done:
                        check_for_folders(port, layer['folders'][key])

        layer1 = MPCommands.device_directory_layer(port)
        check_for_folders(port, layer1)

        return layer1
        
    def list_devices() -> list[str]:
        '''
        ##### Return an array containing information of devices currently
        ##### connected to serial.
        <hr>

        <b>Indexing</b>

            - 0 : Port
            - 1 : Serial
            - 2 : VID:PID
            - 3 : Manufacturer
            - 4 : Product
            - 5 : Interface
        '''
        _d: str = check_output(mp_command('list'), text=True)
        return [line.strip().split(" ") for line in _d.splitlines()]
    
    def get_device_details(port):
        script = [
            'from os import uname\n',
            'from json import dumps\n',
            'from os import statvfs\n',
            '_d = uname()\n'
            '_e = statvfs("/")\n',
            'data = {\n',
            '  "system": {\n',
            '    "sysname": _d.sysname,\n',
            '    "nodename": _d.nodename,\n',
            '    "release": _d.release,\n',
            '    "version": _d.version,\n',
            '    "machine": _d.machine\n',
            '  },\n',
            '  "storage": {\n',
            '    "total": _e[0] * _e[2],\n',
            '  "free": _e[0] * _e[4],\n',
            '  "used": (_e[0] * _e[2]) - (_e[0] * _e[4])\n',
            '  }\n',
            '}\n',
            'print(dumps(data))'
        ]
        _d = check_output(
            mp_command(port, soft_reset=True, execute="".join(script)),
            text=True
        )
        return loads(_d)
    
    def file_exists(port, path):
        '''
        ##### Check if a file exists at a given port.
        <hr>

        ##### Returns True if the given path exists, else False
        '''
        script = [
            f"from os import stat\n",
            f"try:\n",
            f"  stat('{path}')\n",
            f"  print(1)\n",
            f"except OSError:\n",
            f"  print(0)"
        ]
        MPCommands.interrupt(port)
        _d = check_output(
            mp_command(port, soft_reset=True, execute="".join(script)),
            text=True
        )
        return bool(int(_d.splitlines()[0]))
    
    def get_connected_devices():
        devices = MPCommands.list_devices()
        out = []
        for device in devices:
            port = device[0]
            serial = device[1]
            details = MPCommands.get_device_details(port)
            out.append(Device(port,serial,details))
        return out

class OperationStack:
    '''
    #### Construct an operation stack.
    <hr>

    #### call
    - OperationStack sequentially calls operations in a blocking manner.
    <hr>

    #### await
    - OperationStack sequentially adds operations to the running event
    loop as tasks.
    '''
    def __init__(self, operations: list):
        self.operations = operations
    
    def __call__(self):
        def func():
            ...
        def task(_f):
            if type(_f) != type(func):
                return
            _f()
            print(f"::action:: {_f.__name__}")
        for _t in self.operations:
            task(_t)
    
    def __await__(self):
        from asyncio import gather
        x = [self._await]
        yield from gather(self._await())
    async def _await(self):
        from asyncio import get_event_loop, sleep as asleep
        async def coroutine():
            ...
        async def task(coro):
            if type(coro) is not type(coroutine):
                return
            get_event_loop().create_task(coro())
            print(f"::action:: {coro.__name__}")
            await asleep(0)

        for _t in self.operations:
            get_event_loop().create_task(task(_t))

