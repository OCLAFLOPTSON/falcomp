from falco_mp.falcomp.tui import Menu, Text, PaddedRow, Button
from falco_mp.falcomp.color_theme import ColorTheme, ANSITAG
from falco_mp.falcomp.operations import Config, MPCommands, size
from falco_mp.falcomp.keys import key_incoming, read_key

from time import sleep

FRAMERATE = 0.08
DONATE = "http://buymeacoffee.com/timfalco"
STOP = False
CWD = "/"

CONFIG_BEEN_HERE = False

config_data = {}

def _confirm(menu: Menu, mssg: str='?', active_on_complete: int|None=None):
    '''
    - Disables all menu options and appends a PaddedRow with submenu[yes,no]
    - Returns True if yes is selected, else returns False
    - Returns menu to normal condition
    '''
    active = True
    answer = False
    if not active_on_complete:
        active_on_complete = len(menu.menu)-1

    not_selectable = set()

    for i in range(len(menu.menu)):
        if menu.menu[i].active:
            menu.menu[i].active = False
        if not menu.menu[i].selectable:
            not_selectable.add(i)
        menu.menu[i].selectable = False
    
    def _yes(menu, data):
        nonlocal active, answer
        active = False
        answer = True
    def _no(menu, data):
        nonlocal active, answer
        active = False

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text(f"{mssg}"),
        submenu=[
            Button(
                label=Text("yes", italic=True),
                action=_yes,
                data={}
            ),
            Button(
                label=Text("no", italic=True),
                action=_no,
                data={},
                active=True
            )
        ],
        active=True
    ))
    current = menu.draw()
    menu.clear()
    print(current)
    while active:
        if key_incoming():
            menu.handler()
        else:
            new = menu.draw()
            if new != current:
                menu.clear()
                current = new
                print(new)
            sleep(menu.interval)

    for i in range(len(menu.menu)):
        if i not in not_selectable:
            menu.menu[i].selectable = True

    menu.menu[active_on_complete].active = True
    menu.on_startup(menu, menu.data)
    return answer

def open_menu(cmenu: Menu, data: dict):
    global config_data
    target = data.get("target")
    config_data = data.get("data")
    target.data = data
    target.data['parent'] = cmenu
    if type(target) is not Menu:
        raise AttributeError(f"Button data error:\n  Target: {target}\n Data: {data}")
    cmenu.active = False
    target.run(data)

def _info(menu: Menu, data: dict):
    mssg = data.get('payload', 'ERROR')
    print(mssg)

async def itrpt():
    from asyncio import sleep as asleep
    global STOP
    STOP = True
    await asleep(FRAMERATE*5)
    STOP = False

class Device:
    def __init__(self, port: str, serial: str):
        self.name = "UNSET"
        self.port = port
        self.serial = serial

async def animated_print(text: str, framrate=FRAMERATE, end="\n"):
    from sys import stdout
    from asyncio import sleep
    global STOP
    for char in text:
        if not STOP:
            stdout.write(char)
            stdout.flush()
            await sleep(framrate)
        else:
            break
    stdout.write(end)
    stdout.flush()

def close_and_exit(menu: Menu, data):
    from asyncio import sleep, run, get_event_loop
    
    async def interupt():
        while True:
            if key_incoming():
                await itrpt()
            await sleep(0)

    async def loop():
        get_event_loop().create_task(interupt())
        global STOP
        i = 2
        x,y = size()
        menu.clear()

        print("[ANY KEY] → skip")
        i += 1
        # print("\n\n\n\n")
        # i += 5
        print("\n\n\n")
        i += 4
        await animated_print(
            "This app provided free and open source by Timothy Falco".center(x),
            framrate=0.02
        )
        i += 1
        await animated_print(
            f"Gratuity is not necessary but may be directed to {DONATE}".center(x),
            framrate=0.02
        )
        i += 1
        await animated_print(
            "Thank you for using Falco-MP!".center(x),
            framrate=0.02
        )
        i += 1
        if STOP:
            print("Thank you for using Falco-MP!".center(x))
        print("\n"*(y-i), end=ANSITAG.reset)
        exit()
    run(loop())

# ################ ~ File Editor Menu ~ ###################################

# def save_file(menu: Menu, data):
#     port = data.get('port')
#     path = data.get('path')
#     payload = data.gat('payload')
#     if port and path and payload:
#         MPCommands.write_file(port, path, payload)
#         menu.on_startup(menu, data)
#         menu.run()
    

# def insert_return(menu: Menu, data):
#     filename = data.get('filename')
#     port = data.get('port')
#     path = data.get('path')
#     page = data.get('page')
#     x, y = data.get('location')
#     if x+1 < len(menu.menu):
#         page[x+1] = []
#         ansii_esc = ANSITAG.reset+menu.color_theme.text.special
#         text = f'{menu.color_theme.background.main}[{x+2}] |{ansii_esc}{''.join(page[x+1])}'
#         menu.menu.insert(x+2, PaddedRow(
#             parent=menu,
#             label=Text(text),
#             action=insert_return,
#             data={
#                 'page': page,
#                 'location': (x, y)
#             }
#         ))
        
#     menu.on_startup(menu, {
#         'filename': filename,
#         'port': port,
#         'path': path,
#         'page': page,
#         'change': True
#     })
#     menu.run()

# def file_editor_startup(menu: Menu, data: dict):
#     filename = data.get('filename')
#     port = data.get('port')
#     path = data.get('path')

#     page = data.get('page')
#     i = 0
#     if not page:
#         file: str = MPCommands.read_file(port, 'main.py').splitlines()
#         page = dict()
#         for line in file:
#             page[i+1] = [char for char in line]
#             i += 1

#     if not len(menu.menu):
#         menu.menu.append(PaddedRow(
#             parent=menu,
#             label=Text(f"File Editor ({filename})\n\n"),
#             selectable=False
#         ))
        
#         def find_active(parent):
#             for i in range(len(parent.menu)):
#                 if parent.menu[i].active:
#                     return (i, parent.menu[i])
#             return (0, None)
        
#         i, current_active = find_active(menu)
#         location = data.get('location')
#         x = location[0] if location else 0
#         y = location[1] if location else 0

#         for key in page.keys():
#             label_color = (
#                 menu.color_theme.background.main +
#                 ANSITAG.start_bold if menu.menu[i].active else ''
#             )
#             label = f'{label_color}[{x+1}] |{ANSITAG.reset+menu.color_theme.text.special}{''.join(page[key])}'

#             menu.menu.append(PaddedRow(
#                 parent=menu,
#                 label=Text(label),
#                 action=insert_return,
#                 data={
#                     'page': page,
#                     'location': (x, y)
#                 }
#             ))

#             x += 1
        
#         change = data.get("change")
#         if change:
#             payload = ''
#             for key in page.keys():
#                 payload += ''.join(page[key])+'\n'
#             menu.menu.append(PaddedRow(
#                 parent=menu,
#                 label=Text("🖪"),
#                 action=save_file,
#                 data={
#                     'port': port,
#                     'path': path,
#                     'payload': payload
#                 }
#             ))
        
#         menu.menu.append(PaddedRow(
#             parent=menu,
#             label=Text('← Main Menu'),
#             tooltip=Text("return", italic=True),
#             action=open_menu,
#             data={
#                 'target': main_menu,
#                 'data': data,
#                 'port': port,
#                 'parent': device_menu
#             },
#             active=True
#         ))

# file_editor = Menu(
#     title="File Editor",
#     data={
#         'page': dict(),
#         'change': False
#     },
#     on_startup=file_editor_startup,
#     tinput=True
# )

################ ~ Device Menu ~ ########################################

def create_file(menu: Menu, data):
    folder = data.get("folder", False)
    port = data.get("port")
    path = data.get("path")
    if folder:
        path = path+input("Folder Name: ")
        MPCommands.new_folder(port, path)
    else:
        path = path+input("Filename: ")
        MPCommands.write_file(port, path)
    menu.on_startup(menu, menu.data)
    menu.run()

def delete(menu: Menu, data: dict):
    path = data.get('path')
    if path[0] == "/":
        path = path[1:]
    port = data.get('port')
    folder = data.get('folder')
    if folder:
        path = "/"+path[:len(path)-1]
    active = True
    complete = False
    def choose(menu, data):
        nonlocal active, complete
        yes = data.get("yes")
        active = False
        complete = yes

    for row in menu.menu:
        if row.active:
            row.active = False
        row.selectable = False

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text(f"DELETE {path}?"),
        submenu=[
            Button(
                label=Text("yes", italic=True),
                action=choose,
                data={
                    'yes': True
                }
            ),
            Button(
                label=Text("no", italic=True),
                action=choose,
                active=True,
                data={}
            )
        ],
        active=True
    ))
    
    current = menu.draw()
    menu.clear()
    print(current)
    while active:
        if key_incoming():
            menu.handler()
        else:
            new = menu.draw()
            if new != current:
                menu.clear()
                current = new
                print(new)
            sleep(menu.interval)
    
    for row in menu.menu[1:]:
        if row.label == "↕":
            continue
        row.selectable = True
    menu.menu = menu.menu[:len(menu.menu)-1]
    if not complete:
        menu.on_startup(menu, menu.data)
        menu.run()
        return
    print("Deleting...")
    MPCommands.delete_file(port, path, folder)
    menu.on_startup(menu, menu.data)
    menu.run()

def change_working_directory(menu: Menu, data: dict):
    menu.CWD = data.get("path", "/")
    menu.on_startup(menu, data)
    menu.run()

def go_back_one(menu: Menu, data: dict):
    _p = menu.CWD.split('/')
    if _p[len(_p)-1]:
        _p.pop()
    else:
        _p.pop()
        _p.pop()
    menu.CWD = "/".join(_p)+"/" if len(_p) else "/"
    menu.on_startup(menu, data)
    menu.run()

def run_script(menu: Menu, data):
    '''Requires: data:{port, path}'''
    try:
        port = data.get('port')
        path = data.get('path', 'main.py')
        menu.clear()
        MPCommands.run_file(port, path)
    except Exception as e:
        print(e)
        exit()
    finally:
        menu.on_startup(menu, menu.data)
        menu.run()

def run_repl(menu: Menu, data: dict):
    try:
        port = data.get('port')
        menu.clear()
        MPCommands.run_repl(port)
    finally:
        menu.on_startup(menu, menu.data)
        menu.run()

def sync_files(menu: Menu, data):
    def _sync(menu, data):
        port = data.get('port')
        config = data.get('config', dict())
        report: dict = MPCommands.sync_working_directory(port)
        menu.CWD = "/"
        menu.on_startup(menu, menu.data)
        _m = config.get("print_sync_resport")
        mssg = f"""
        Final Sync Report:
            Files Added:
                {report.get("files_added", "None")}
            Files Removed:
                {report.get("files_removed", "None")}
            Files Modified:
                {report.get("files_modified", "None")}
            Directories Added:
                {report.get("folders_added", "None")}
            Directories Removed:
                {report.get("folders_removed", "None")}
        """ if _m else None
        menu.run({"mssg": mssg})
        
    def _dont_sync(menu: Menu, data):
        menu.on_startup(menu, menu.data)
        menu.run()
        
    port = data.get("port")
    config = Config.get(port)

    if config["confirm-on-sync"]:
        for row in menu.menu:
            if row.active:
                row.active = False
            row.selectable = False

        menu.menu.append(PaddedRow(
            parent=menu,
            label=Text("Sync Working Directory To Device?"),
            submenu=[
                Button(
                    label=Text("yes", italic=True),
                    action=_sync,
                    data={
                        "port": port,
                        "config": config
                    }
                ),
                Button(
                    label=Text("no", italic=True),
                    action=_dont_sync,
                    data={},
                    active=True
                )
            ],
            active=True
        ))
        active = True
        current = menu.draw()
        menu.clear()
        print(current)
        while active:
            if key_incoming():
                menu.handler()
            else:
                new = menu.draw()
                if new != current:
                    menu.clear()
                    current = new
                    print(new)
                sleep(menu.interval)
        
    report = MPCommands.sync_working_directory(port)
    menu.on_startup(menu, menu.data)
    
    _m = config.get("print_sync_resport")
    mssg = f"""
    Final Sync Report:
        Files Added:
            {report.get("files_added", "None")}
        Files Removed:
            {report.get("files_removed", "None")}
        Files Modified:
            {report.get("files_modified", "None")}
        Directories Added:
            {report.get("folders_added", "None")}
        Directories Removed:
            {report.get("folders_removed", "None")}
    """ if _m else None
    menu.run({"mssg": mssg})

def generate_stubs(menu: Menu, data: dict):
    port = data.get('port')
    if _confirm(menu, f"Generate stubs from device at port: {port}?"):
        MPCommands.generate_stubs(port)

def _device_menu_startup(menu: Menu, data: dict):
    menu.menu = []
    port = menu.data.get("port")
    device_config = Config.get(port)
    cols, rows = size()

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text(f'Device: {device_config.get("name")}({port})'),
        selectable=False
    ))
    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text("options", italic=True),
        submenu=[
            Button(
                label=Text("(►)"),
                action=run_script,
                data={
                    'port': port,
                    'path': 'main.py'
                },
                active=True
            ),
            Button(
                label=Text('REPL'),
                action=run_repl,
                data={
                    'port': port
                }
            ),
            Button(
                label=Text("Sync"),
                action=sync_files,
                data={
                    'port': port
                }
            ),
            Button(
                label=Text("Create File"),
                action=create_file,
                data={
                    'port': port,
                    'path': menu.CWD,
                }
            ),
            Button(
                label=Text("Create Folder"),
                action=create_file,
                data={
                    'port': port,
                    'path': menu.CWD,
                    'folder': True
                }
            ),
            Button(
                label=Text("Generate Stubs"),
                action=generate_stubs,
                data={"port": port}
            )
        ]
    ))
    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text("↕".center(cols//2)),
        selectable=False
    ))

    # filetree
    port = menu.data.get("port")
    layer = MPCommands.device_directory_layer(port, menu.CWD)
    name = f"__{layer.get('name')}__"
    titlebar = name + "_" * ((cols//2)-len(name))
    hr = "_"*(cols//2)

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text(titlebar),
        selectable=False
    ))
    if menu.CWD != "/":
        menu.menu.append(PaddedRow(
            parent=menu,
            label=Text("↰"),
            submenu=[
                Button(
                    label=Text("return", italic=True),
                    action=go_back_one,
                    active=True,
                    data={}
                )
            ]
        ))
    i = 0
    layer_folders = layer.get('folders', {})
    layer_files = layer.get("files", {})
    for key in layer_folders.keys():
        if not len(layer_files):
            label = Text(f"└{layer['folders'][key]['name']}")
        else:
            label = Text(f"├{layer['folders'][key]['name']}")
        menu.menu.append(PaddedRow(
            parent=menu,
            label=label,
            submenu=[
                Button(
                    label=Text("open", italic=True),
                    action=change_working_directory,
                    data={
                        'path': layer['folders'][key].get('path')
                    },
                    active=True
                ),
                Button(
                    label=Text("delete", italic=True),
                    action=delete,
                    data={
                        'path': layer['folders'][key].get('path'),
                        'port': port,
                        'folder': True
                    }
                )
            ]
        ))

        i += 1
    i = 0
    for key in layer_files.keys():
        _n = layer_files[key].get("name")
        _p = layer_files[key].get("path")
        submenu = []
        if _p == "config.json":
            submenu.append(
                Button(
                    label=Text("open", italic=True),
                    action=open_menu,
                    data={
                        'target': config_menu,
                        'data': data,
                        'port': port,
                        'parent': menu
                    },
                    active=True if _n == "config.json" else False
                )
            )
        if '.py' in _n:
            submenu.append(
                Button(
                    label=Text("run", italic=True),
                    action=run_script,
                    data={
                        'port': port,
                        'path': _p
                    },
                    active=True
                )
            )
        # submenu.append(Button(                              # Fix Later
        #     label=Text("open", italic=True),
        #     action=open_menu,
        #     active=True,
        #     data={
        #         'target': file_editor,
        #         'filename': _n,
        #         'path': layer_files[key].get('path'),
        #         'port': port
        #     }
        # ))
        submenu.append(Button(
            label=Text("delete", italic=True),
            action=delete,
            data={
                'path': _p,
                'port': port,
                'folder': False
            },
            active=False if ".py" in _n or _n == "config.json" else True
        ))
        if i >= len(layer_files.keys())-1:
            menu.menu.append(PaddedRow(
                parent=menu,
                label=Text(f"└{_n}"),
                submenu=submenu
            ))
            continue 
        menu.menu.append(PaddedRow(
            parent=menu,
            label=Text(f"├{layer_files[key].get("name")}"),
            submenu=submenu
        ))

        i += 1

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text(hr),
        selectable=False
    ))
    
    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text("↕".center(cols//2)),
        selectable=False
    ))
    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text('← Main Menu'),
        tooltip=Text("return", italic=True),
        action=open_menu,
        data={
            'target': main_menu,
            'data': menu.data,
            'port': port,
            'parent': device_menu
        },
        active=True
    ))

device_menu = Menu(
    title="Device Menu",
    interval=FRAMERATE,
    on_startup=_device_menu_startup
)

################ ~ Configure Menu ~ #####################################

def update_config_entry(menu: Menu, data):
    from time import sleep
    key = data.get('key')
    config = data.get('config')
    port = data.get('port', "")
    toggle = data.get("toggle", False)
    if toggle:
        config[key] = False if config[key] else True
        Config.update(port, config)
        menu.on_startup(menu, menu.data)
        menu.run()
    menu.clear()
    print("Update Setting:\n\n")
    config[key] = input(f"Enter a new {key}: ")
    Config.update(port, config)
    menu.on_startup(menu, menu.data)
    menu.run()

def config_subentry(menu: Menu, data):
    config = data.get('config')
    port = data.get('port')
    key = data.get('key')
    value = data.get('value')
    if data.get("add", False):
        menu.clear()
        print("Add a label to sub-list:\n\n")
        new_label = input("Label (max characters: 100): ")
        if key == "notes":
            from datetime import datetime
            ts = datetime.now()
            config[key].append(f"{ts.strftime('%m/%d/%Y - %I:%M %p')} : {new_label[:74]}")
            Config.update(port,config)
            menu.on_startup(menu, menu.data)
            menu.run()
            return
        config[key].append(new_label[:74])
        Config.update(port,config)
        menu.on_startup(menu, menu.data)
        menu.run()
    for x in range(len(config[key])):
        if config[key][x] == value:
            config[key].pop(x)
            Config.update(port, config)
            menu.on_startup(menu, menu.data)
            menu.run()

def config_startup(menu: Menu, data):

    port = menu.data.get('port')
    if not port:
        raise AttributeError(f'Bad port. Data: {menu.data}')
    cols, rows = size()
    
    menu.menu = [
        PaddedRow(
            parent=config_menu,
            label=Text("Device Configuration"),
            selectable=False
        )
    ]
    
    config_data = Config.get(port)

    i = 0
    keys = config_data.keys()
    for key in keys:
        toggle = True if type(config_data[key]) is bool else False
        if key == "serial":
            selectable = False
        else:
            selectable = True
        
        ##### info labels ########
        if key == "preserve-device-files":
            info_label = """
If True, sync ignores files which do exist on the device but do not exist
in the local working directory.

If False, syncs local working directory normally.

Selecting toggles the value.
"""
        elif key == "confirm-on-sync":
            info_label = """
If True, requires confirmation before syncing.

Selecting toggles the value.
"""
        elif key == "notes":
            info_label = """
Add a text note with a timestamp.

100 character maximum.
"""
        elif key == "ignore":
            info_label = """
A list of patterns for sync to ignore. Files/folders in the working
directory which are declared here are not copied to the device.
"""
        else:
            info_label = False
        ##########################

        if type(config_data[key]) is list:
            last_index = i < len(keys)-1
            menu.menu.append(PaddedRow(
                parent=menu,
                label=Text(f'├{str(key)}┐') if last_index else Text(f'└{str(key)}┐'),
                submenu=[
                    Button(
                        label=Text('Add', italic=True),
                        action=config_subentry,
                        data={
                            'add': True,
                            'port': port,
                            'config': config_data,
                            'key': key
                        },
                        active=True
                    ),
                    Button(
                        label=Text("info", italic=True),
                        action=_info,
                        data={
                            "payload": (
                                info_label if info_label
                                else "Add a string object to the list."
                            )
                        }
                    )
                ],
                selectable=selectable
            ))
            for x in range(len(config_data[key])):
                if x == len(config_data[key])-1:
                    menu.menu.append(PaddedRow(
                        parent=menu,
                        label=Text(f"│  └{str(config_data[key][x])}") if last_index else Text(f"   └{str(config_data[key][x])}"),
                        submenu=[
                            Button(
                                label=Text("delete", italic=True),
                                active=True,
                                action=config_subentry,
                                data={
                                    'port': port,
                                    'config': config_data,
                                    'key': key,
                                    'value': config_data[key][x]
                                }
                            ),
                            Button(
                                label=Text("info", italic=True),
                                action=_info,
                                data={
                                    "payload": (
                                        info_label if info_label
                                        else "Delete a string object from the list."
                                    )
                                }
                            )
                        ],
                        selectable=selectable
                    ))
                    break
                menu.menu.append(PaddedRow(
                    parent=menu,
                    label=Text(f"│  ├{str(config_data[key][x])}") if last_index else Text(f"   ├{str(config_data[key][x])}"),
                    submenu=[
                        Button(
                            label=Text("delete", italic=True),
                            active=True,
                            action=config_subentry,
                            data={
                                'port': port,
                                'config': config_data,
                                'key': key,
                                'value': config_data[key][x]
                            }
                        ),
                        Button(
                            label=Text("info", italic=True),
                            action=_info,
                            data={
                                "payload": (
                                    info_label if info_label
                                    else "Delete a string object from the list."
                                )
                            }
                        )
                    ],
                    selectable=selectable
                ))
        elif i >= len(keys)-1:
            menu.menu.append(PaddedRow(
                parent=menu,
                label=Text(f'└{key} : {config_data[key]}└'),
                submenu=[
                    Button(
                        label=Text("edit", italic=True) if not toggle else Text("toggle", italic=True),
                        active=True,
                        action=update_config_entry,
                        data={
                            'key': key,
                            'config': config_data,
                            'target': None,
                            'data': menu.data,
                            'port': menu.data.get('port'),
                            'parent': config_menu,
                            'toggle':toggle
                        }
                    ),
                    Button(
                        label=Text("info", italic=True),
                        action=_info,
                        data={
                            "payload": (
                                info_label if info_label
                                else f"{"Toggle" if toggle else "Edit"} the config setting value.\n"
                            )
                        }
                    )
                ],
                selectable=selectable
            ))
            break
        else:
            menu.menu.append(PaddedRow(
                parent=menu,
                label=Text(f'├{key} : {config_data[key]}'),
                submenu=[
                    Button(
                        label=Text("edit", italic=True) if not toggle else Text("toggle", italic=True),
                        active=True,
                        action=update_config_entry,
                        data={
                            'key': key,
                            'config': config_data,
                            'target': None,
                            'data': menu.data,
                            'port': menu.data.get('port'),
                            'parent': config_menu,
                            'toggle':toggle
                        }
                    ),
                    Button(
                        label=Text("info", italic=True),
                        action=_info,
                        data={
                            "payload": (
                                info_label if info_label
                                else f"{"Toggle" if toggle else "Edit"} the config setting value.\n"
                            )
                        }
                    )
                ],
                selectable=selectable
            ))

        i += 1

    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text("↕".center(cols//2)),
        selectable=False
    ))
    menu.menu.append(PaddedRow(
        parent=menu,
        label=Text('← Return'),
        tooltip=Text("return", italic=True),
        action=open_menu,
        data={
            'target': data.get('parent', main_menu),
            'data': menu.data,
            'port': menu.data.get('port')
        }
    ))
    menu.menu[len(menu.menu)-1].active = True

config_menu = Menu(
    title="Device Configuration",
    interval=FRAMERATE,
    on_startup=config_startup
)


################ ~ Main Menu ~ ##########################################

def _refresh_device_list(parent: Menu, data):
    # parent.data['parent'] = None

    parent.menu = [
        PaddedRow(
            parent=main_menu,
            label=Text("Falco-MP MicroPython Device Manager\n\n", italic=True),
            selectable=False
        ),
        PaddedRow(
            parent=main_menu,
            label=Text("\n\n\n"),
            selectable=False
        ),
        PaddedRow(
            parent=main_menu,
            label=Text("Refresh"),
            action=_refresh_device_list,
            tooltip=Text("Refresh Device List", italic=True),
            active=True
        ),
        PaddedRow(
            parent=main_menu,
            label=Text("Exit"),
            action=close_and_exit,
            tooltip=Text("Close and exit", italic=True)
        )
    ]
    for entry in MPCommands.list_devices():
        port = entry[0]
        data = Config.get(port)

        parent.menu.insert(1, PaddedRow(
            parent=parent,
            label=Text(f'{data.get("name", "UNSET") if data else "UNSET"}({port})'),
            submenu=[
                Button(
                    label=Text("Select", italic=True),
                    action=open_menu,
                    data={
                        'target': device_menu,
                        'data': data,
                        'port': port,
                        'parent': parent
                    },
                    active=True
                ),
                Button(
                    label=Text("Configure"),
                    action=open_menu,
                    data={
                        'target': config_menu,
                        'data': data,
                        'port': port,
                        'parent': parent
                    }
                )
            ],
            data="DEVICE"
        ))


main_menu = Menu(
    title="Falco-MP Device Controller",
    interval=FRAMERATE,
    on_startup=_refresh_device_list
)
main_menu.menu = [
    PaddedRow(
        parent=main_menu,
        label=Text("Falco-MP MicroPython Device Manager\n\n", italic=True),
        selectable=False
    ),
    PaddedRow(
        parent=main_menu,
        label=Text("\n\n\n"),
        selectable=False
    ),
    PaddedRow(
        parent=main_menu,
        label=Text("Refresh"),
        action=_refresh_device_list,
        tooltip=Text("Refresh Device List", italic=True)
    ),
    PaddedRow(
        parent=main_menu,
        label=Text("Exit"),
        action=close_and_exit,
        tooltip=Text("Close and exit", italic=True)
    )
]