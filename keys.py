import os
import sys

CTRL_S = "\x13"
CTRL_C = "\x03"

if os.name == "nt":

    import msvcrt

    def key_incoming():
        return msvcrt.kbhit()

    def read_key():

        ch = msvcrt.getch()

        if ch in (b"\x00", b"\xe0"):

            code = msvcrt.getch()

            if code == b"H":
                return "UP"

            if code == b"P":
                return "DOWN"

            if code == b"K":
                return "LEFT"

            if code == b"M":
                return "RIGHT"

            return None

        if ch == b"\t":
            return "TAB"

        if ch == b"\r":
            return "ENTER"

        if ch == b"\x13":
            return CTRL_S

        if ch == b"\x03":
            return CTRL_C

        try:
            return ch.decode()
        except:
            return None


else:

    import termios
    import tty
    import select

    def key_incoming():
        r, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(r)

    def read_key():

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)

        try:

            tty.setraw(fd)

            ch = sys.stdin.read(1)

            if ch == "\x1b":

                seq = sys.stdin.read(2)

                if seq == "[A":
                    return "UP"

                if seq == "[B":
                    return "DOWN"

                if seq == "[C":
                    return "RIGHT"

                if seq == "[D":
                    return "LEFT"

                if seq == "[Z":
                    return "SHIFT_TAB"

                return None

            if ch == "\t":
                return "TAB"

            if ch == "\r":
                return "ENTER"

            if ch == CTRL_S:
                return CTRL_S

            if ch == CTRL_C:
                return CTRL_C

            return ch

        finally:

            termios.tcsetattr(fd, termios.TCSADRAIN, old)