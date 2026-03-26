from falco_mp.falcomp.ansi import AnsiEscape, ANSITAG

class ColorTheme(object):
    class Color:
        def __init__(self, main, special, offset):
            self.main = main
            self.special = special
            self.offset = offset

    def __init__(self, bgcolor_main: AnsiEscape=ANSITAG.color(16, 16, 26),
                 bgcolor_special: AnsiEscape=ANSITAG.color(60, 60, 100),
                 bgcolor_offset: AnsiEscape=ANSITAG.color(35, 35, 45),
                 textcolor_main: AnsiEscape=ANSITAG.color(112, 112, 255, True),
                 texctolor_special: AnsiEscape=ANSITAG.color(124, 124, 175, True),
                 textcolor_offset: AnsiEscape=ANSITAG.color(160, 160, 160, True)):
        self.text = ColorTheme.Color(
            textcolor_main,
            texctolor_special,
            textcolor_offset
        )
        self.background = ColorTheme.Color(
            bgcolor_main,
            bgcolor_special,
            bgcolor_offset
        )