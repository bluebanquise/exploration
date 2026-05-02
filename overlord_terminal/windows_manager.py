import sys,time
import yaml
import os
#from rich.traceback import install
import textwrap
import validators
import zoneinfo
import json

class windows_manager(object):
  """ This is a small windows manager for terminal.
  I hate things that clear the terminal because it often clears logs or errors.
  So this is an home made concept of windows manager that lives verticaly in the terminal :)
  """

  def __init__(self, init_nesting_level=-1):
    self.w_nesting_level = init_nesting_level
    #self.w_colors = ['39', '214', '201', '226']
    self.w_colors = ['226', '208', '196', '163', '45', '82']
    self.w_allowed_colors = {
      'blue': '\033[94m',
      'green': '\033[92m',
      'reset': '\033[0m'
    }

  def t_green(self, message):
    return self.w_allowed_colors['green'] + message + self.w_allowed_colors['reset']

  def t_blue(self, message):
    return self.w_allowed_colors['blue'] + message + self.w_allowed_colors['reset']

  def w_sprint(self, message, nl=True):
    # Now we have to parse text lines by lines, and decorate it
    # We use native decorator, but we have to complete each line with spaces

    # Small fix: if empty message, add at least a space to prevent empty line.
    if message == "":
      message = " "
    umessage = []
    for line in message.splitlines():
      umessage.append(self.w_decorator_left_right(line, force_nesting_level = self.w_nesting_level + 1, fill_line = True))
    message = '\n'.join(umessage)
    if nl:
      message = message + '\n'
    for c in message:
      sys.stdout.write(c)
      sys.stdout.flush()
      # if c != " ":
      #   time.sleep(1./500)

  def w_input(self, message, nl=True):
    umessage = self.w_decorator_left_right(message, force_nesting_level = self.w_nesting_level + 1, no_right = True)
    answer = input(umessage)
    # https://stackoverflow.com/questions/12586601/remove-last-stdout-line-in-python
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)
    print(self.w_decorator_left_right(message + str(answer), force_nesting_level = self.w_nesting_level + 1, fill_line = True))
    return answer

  def w_create(self, w_title=None):
    self.w_sprint("\n")
    # Get size of terminal
    # We do that each time to cover terminal resized during usage
    columns = os.get_terminal_size().columns
    # Set lead section depending if we are creating or closing a window
    # This is of size 5
    lead = "╭─────"
    self.w_nesting_level = self.w_nesting_level + 1
    # Create current windows frame
    box = "\033[38;5;" + self.w_colors[self.w_nesting_level] + "m" + lead
    # Manage title if any
    if w_title is not None:
      box = box + " " + str(w_title) + " "
      title_size = len(w_title) + 2
    else:
      title_size = 0
    # Complete the line
    for i in range(1, columns - self.w_nesting_level * 4 * 2 - len(lead) - title_size - 1, 1):
      box = box + "─"
    box = box + "╮" + "\033[0m"
    box = self.w_decorator_left_right(box)
    print(box)

  def w_destroy(self):
    # Get size of terminal
    # We do that each time to cover terminal resized during usage
    columns = os.get_terminal_size().columns
    # Set lead section depending if we are creating or closing a window
    # This is of size 5
    lead = "╰─────"
    # Create current windows frame
    box = "\033[38;5;" + self.w_colors[self.w_nesting_level] + "m" + lead
    # Complete the line
    for i in range(1, columns - self.w_nesting_level * 4 * 2 - len(lead) - 1, 1):
      box = box + "─"
    box = box + "╯" + "\033[0m"
    box = self.w_decorator_left_right(box)
    print(box)
    self.w_nesting_level = self.w_nesting_level - 1

  def w_decorator_left_right(self, message, force_nesting_level=None, fill_line=False, no_right=False):
    if force_nesting_level is not None:
      nesting_level = force_nesting_level
    else:
      nesting_level = self.w_nesting_level
    buffer = ""
    for nl in range(0, nesting_level, 1):
      buffer = buffer + "\033[38;5;" + self.w_colors[nl] + "m│\033[0m   "
    message = buffer + message
    buffer = ""
    if not no_right:
      for nl in range(nesting_level-1, -1, -1):
        buffer = buffer + "\033[38;5;" + self.w_colors[nl] + "m   │\033[0m"
      # Before applying right buffer, lets check if line must be filled
      if fill_line:
        columns = os.get_terminal_size().columns
        message_buffer = (message + buffer)
        message_buffer = message_buffer.replace("\033[0m", "")
        for i in self.w_colors:
          message_buffer = message_buffer.replace("\033[38;5;" + str(i) + "m", "")
        for i, v in self.w_allowed_colors.items():
          message_buffer = message_buffer.replace(v, "")
        for i in range(1, columns - len(message_buffer), 1):
          message = message + " "

      message = message + buffer
    return message
