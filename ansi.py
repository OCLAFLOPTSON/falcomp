from typing import NewType

AnsiEscape = NewType("AnsiEscape", str)

class ANSITAG:
    '''Library of ANSI escape sequences with some factory methods.'''
    start_italic = "\033[3m"
    stop_italic = "\033[23m"
    start_bold = "\033[1m"
    stop_bold = "\033[22m"
    reset = "\033[0m"

    def clear_and_return_cursor(col=1,row=1) -> AnsiEscape:
        '''ANSI tag that clears the console and returns the
        cursor to a given position.'''
        return f"\033[2J\033[3J\033[{row};{col}H"

    def color(red: int, green: int, blue: int, text: bool=True) -> str:
        """Construct an ANSI escape sequence for a given RGB color.

        text=True  → foreground color
        text=False → background color
        """
        return f"\033[{38 if text else 48};2;{red};{green};{blue}m"

    def move_cursor_to_line(line: int) -> str:
        """
        Return an ANSI escape sequence that moves the cursor to the
        given line at the leftmost column (column 1).
        """
        return f"\033[{line};1H"