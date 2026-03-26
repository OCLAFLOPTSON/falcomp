from time import sleep
from sys import stdout

from falco_mp.falcomp.operations import size
from falco_mp.falcomp.color_theme import ColorTheme, ANSITAG
from falco_mp.falcomp.keys import read_key, key_incoming

class Text:
    def __init__(self, value: str, italic: bool=False, bold: bool=False):
        if italic:
            self.value = ANSITAG.start_italic+value+ANSITAG.stop_italic
        else:
            self.value = value

class Button:
    def __init__(self, label: Text, action, data=None,
            color_theme: ColorTheme=ColorTheme(
            bgcolor_main=ANSITAG.color(128, 128, 128),
            bgcolor_special=ANSITAG.color(211, 211, 211),
            textcolor_main=ANSITAG.color(0, 0, 0),
            texctolor_special=ANSITAG.color(245, 245, 245)
            ), active: bool=False):
        self.active = active
        self.label = label
        self.color_theme = color_theme
        self.action = action
        self.data = data
    
    def __call__(self, *args, **kwargs):
        self.action(*args, **kwargs)
    
    def render(self):
        out = ' '
        if self.active:
            out += self.color_theme.background.special
            out += self.color_theme.text.special
            out += self.label.value + ' ' + ANSITAG.reset
            return out
        out += self.color_theme.background.main
        out += self.color_theme.text.main
        out += self.label.value + ' ' + ANSITAG.reset
        return out
    
class PaddedRow:
    def __init__(self, parent, label: Text, action=None,
                 tooltip: Text|None=None, submenu: list|None=None,
                 active: bool=False, selectable: bool=True, data=None):
        self.action = action
        self.parent: Menu = parent
        self.active = active
        self.tooltip = tooltip
        self.submenu = submenu
        self.label = '  '+label.value
        self.selectable = selectable
        self.data = data
    
    def render(self, width: int):
        length = len(self.label)
        theme = self.parent.color_theme
        out = theme.background.main+theme.text.main+self.label
        if self.tooltip and self.active:
            out += (
                "-" * ((width-(length+len(self.tooltip.value)))//2 if
                       length < 76 else 0) +
                self.tooltip.value
            )
        if self.submenu and self.active:
            menu_length = 0
            for btn in self.submenu:
                menu_length += len(btn.label.value)
            if not self.tooltip:
                out += "-" * ((width-(length+menu_length))//2 if
                       length < 76 else 0)
            for i in range(0, len(self.submenu)):
                out += (
                    self.submenu[i].render() +
                    self.submenu[i].color_theme.background.offset + " " +
                    self.parent.color_theme.background.main
                ) if i < len(self.submenu) else (
                    self.submenu[i].render() +
                    self.submenu[i].color_theme.background.offset +
                    self.parent.color_theme.background.main
                )
        return out + ANSITAG.reset

def generic_startup(menu, data):
    ...

class Menu(object):
    def __init__(self, title: str, interval=0.025, on_startup=generic_startup,
                  tinput=None, data: dict=dict(),
                  color_theme: ColorTheme=ColorTheme()):
        self.CWD = "/"
        self.active = False
        self.interval = interval
        self.title = title
        self.color_theme = color_theme

        self.menu: list[PaddedRow] = []
        self.table: list = []
        self.data = data
        self.on_startup = on_startup

        self.tinput = tinput
        self.changed = False

    def clear(self):
        stdout.write(
            self.color_theme.background.main +
            ANSITAG.clear_and_return_cursor()
        )
        stdout.flush()
    
    def handler(self):
        def find_active(parent):
            for i in range(len(parent.menu)):
                if parent.menu[i].active:
                    return (i, parent.menu[i], "menu")
            for i in range(len(parent.table)):
                if parent.table[i].active:
                    return (i, parent.table[i], "table")
            return (None, None, None)

        key = read_key()
        if self.tinput:
            i, current_active, _ = find_active(self)
            if key not in ['UP', 'DOWN', "ENTER"]:
                if key == "LEFT":
                    ...
                elif key == "RIGHT":
                    ...
                else:
                    ...

        if key == "UP":
            i, current_active, _F = find_active(self)
            print(ANSITAG.move_cursor_to_line(i))

            if _F == "menu":

                if i - 1 >= 0:
                    if not self.menu[i-1].selectable:
                        y = i
                        for x in range(len(self.menu)):
                            if i-1 == 0 and not self.menu[i-1].selectable:
                                return
                            i -= 1
                            if self.menu[i].selectable:
                                self.menu[y].active = False
                                self.menu[i].active = True
                                return
                            
                    self.menu[i].active = False
                    self.menu[i-1].active = True

            elif _F == "table":
                ...

        elif key == "DOWN":
            i, current_active, _F = find_active(self)

            if _F == "menu":

                if i + 1 < len(self.menu):
                    if not self.menu[i+1].selectable:
                        y = i
                        for x in range(len(self.menu)):
                            if i+1 == len(self.menu) and not self.menu[i+1].selectable:
                                return
                            i += 1
                            if self.menu[i].selectable:
                                self.menu[y].active = False
                                self.menu[i].active = True
                                return
                            
                    self.menu[i].active = False
                    self.menu[i+1].active = True

            elif _F == "table":
                ...

        elif key == "LEFT":
            i, current_active, _F = find_active(self)

            if _F == "menu":
                if not current_active.submenu:
                    return
                for x in range(len(current_active.submenu)):
                    if current_active.submenu[x].active:
                        if x - 1 >= 0:
                            current_active.submenu[x].active = False
                            current_active.submenu[x-1].active = True
                            break
                
            elif _F == "table":
                ...

        elif key == "RIGHT":
            i, current_active, _F = find_active(self)

            if _F == "menu":
                if not current_active.submenu:
                    return
                for x in range(len(current_active.submenu)):
                    if current_active.submenu[x].active:
                        if x + 1 < len(current_active.submenu):
                            current_active.submenu[x].active = False
                            current_active.submenu[x+1].active = True
                            break
                
            elif _F == "table":
                ...

        elif key == "ENTER":
            i, current_active, _F = find_active(self)

            if _F == "menu":
                if current_active.submenu:
                    for x in range(len(current_active.submenu)):
                        if current_active.submenu[x].active:
                            current_active.submenu[x](self, {
                                'config': current_active.submenu[x].data.get('config'),
                                'key': current_active.submenu[x].data.get('key', '-1'),
                                'target': current_active.submenu[x].data.get('target'),
                                'data': current_active.submenu[x].data.get('data'),
                                'port': current_active.submenu[x].data.get('port'),
                                'parent': current_active.submenu[x].data.get('parent'),
                                'toggle': current_active.submenu[x].data.get('toggle'),
                                'add': current_active.submenu[x].data.get('add'),
                                'value': current_active.submenu[x].data.get('value'),
                                'path': current_active.submenu[x].data.get('path'),
                                'folder': current_active.submenu[x].data.get('folder'),
                                'yes': current_active.submenu[x].data.get('yes'),
                                'name': current_active.submenu[x].data.get('name'),
                                'filename': current_active.submenu[x].data.get('filename'),
                                'page': current_active.submenu[x].data.get('page'),
                                'location': current_active.submenu[x].data.get('location'),
                                'payload': current_active.submenu[x].data.get('payload'),
                                'mssg': current_active.submenu[x].data.get('mssg')
                            })

                if current_active.action:
                    if type(current_active.data) is not dict:
                        current_active.data = {}
                    current_active.data['path'] = self.CWD
                    current_active.action(self, current_active.data)

            elif _F == "table":
                ...
    
    def draw(self):
        cols, rows = size()
        out = ''
        for row in self.menu:
            out += row.render(cols) + "\n"
        for row in self.table:
            ...
        return out
    
    def run(self, data: dict|None=None):
        if self.on_startup and not self.active:
            self.on_startup(self, data if data else self.data)
        self.active = True
        current = ''

        # if self.menu:
        #     self.menu[len(self.menu)-1].active = True

        while self.active:
            if key_incoming():
                self.handler()
            else:
                new = self.draw()
                if new != current:
                    self.clear()
                    current = new
                    print(new)
                sleep(self.interval)
