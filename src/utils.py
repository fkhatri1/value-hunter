import configparser
from typing import Dict
import os
import sys
from datetime import datetime as dt

def get_config(path: str = '/home/ec2-user/stocks/config.ini') -> Dict:
    config = configparser.ConfigParser()
    config.read(path)
    return config._sections



# ***********************
# Logger
# ***********************
# Inputs:
#   - level (optional): defines the log level of the message to be printed
#   - path (optional): defines the path to write log to
#   - print_to_stdout (optional): boolean
# Notes:
#   - Supports info, warn and error levels

class Logger:
    LOG_LEVELS = ('info', 'warn', 'error')

    # Initializer
    def __init__(self, level:str = 'info', path:str = None, print_to_stdout:bool = True) -> None:
        self.level = level.lower()

        # Parse parent dir of output path, check if writable
        if path is not None:
            try:
                output_parent_dir = path[::-1].split("/",1)[1][::-1]
            except Exception as e:
                raise ValueError(f"Output file path {path} cannot be parsed.")

            if os.access(output_parent_dir, os.W_OK):
                # open file for writing, 
                self.print_to_file = True
                self.f = open(path, "a+")  #a+ indicates append if exists, else create
            else:
                raise RuntimeError(f"{path} is not a writeable location.")
        else:
            self.print_to_file = False
        
        self.print_to_stdout = print_to_stdout

    # __setattr__
    # Use to check if user tries to set invalid options
    def __setattr__(self, name, value):
        if name == 'level':
            # Check if valid log level was specified
            if value.lower() in Logger.LOG_LEVELS:
                object.__setattr__(self, 'level', value.lower())
            else:
                raise ValueError(f"{value} is not a valid log level.  Valid levels: {Logger.LOG_LEVELS}")

        elif name == 'path':
            # Changing of output path on the fly is not allowed for simplicity
            raise RuntimeError(f"Cannot change log output path on-the-fly.")
        
        # Check if bool passed in for print_to_stdout
        elif name in ('print_to_stdout', 'print_to_file'):
            if isinstance(value, bool):
                object.__setattr__(self, name, value)
            else:
                raise ValueError(f"{value} is not valid. Must be boolean True or False.")
        
        elif name == 'f':
            object.__setattr__(self, name, value)

        else:
            raise NameError(f"{name} is not a valid attribute.")

    # Destructor
    def __del__(self):
        try:
            self.f.close()
        except Exception as e:
            pass

    
    def _print(self, level, msg) -> None:
        if self.print_to_file:
            self.f.write(f'{dt.now().strftime("%m/%d/%Y %H:%M:%S")} {level.upper()}: {msg}\n')
        
        if self.print_to_stdout:
            sys.stdout.write(f'{dt.now().strftime("%m/%d/%Y %H:%M:%S")} {level.upper()}: {msg}\n')
            # Flush output to stdout
            sys.stdout.flush()
        

    def info(self, msg) -> None:
        if self.level == 'info':
            self._print('info', msg)

    def warn(self, msg) -> None:
        if self.level in ('info', 'warn'):
            self._print('warn', msg)

    def error(self, msg) -> None:
        self._print('error', msg)

    def set_log_level(self, level) -> None:
        self.level = level
