#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Retroarch Python API
This is a Python API for the RetroArch /
libretro Libraries for Console Emulators

Derived and still mostly compatible with  https://github.com/merlink01/RetroArchPythonAPI/
Added python3 support and made network-based by eadmaster
"""

import os
import time
import logging
import socket

__version__ = 0.5
__copyright__ = 'GPL V2'



class RetroArchPythonApi(object):

    """Usage:
    from retroarchpythonapi import RetroArchPythonApi
    api = RetroArchPythonApi()
    
    api.show_msg("Hello world!")
    api.toggle_pause()
    api.save_state()
    api.load_state()
    api.read_core_ram(0x7df, 4)  # read 4 bytes from address 7df
    api.write_core_ram(0x7df, [0x00, 0x00, 0x00, 0x00])  # write 4 bytes set to 0 from address 7df
    api.reset()
    api.quit()
    
    methods to read current status:
    api.is_alive()  # true if is responding to network commands
    api.has_content()  # true if has some content loaded
    api.is_paused() # true if has some content loaded and it IS paused
    api.is_playing()  # true if has some content loaded and it IS NOT paused
    api.get_version()
    api.get_system_id()  # returns a string like "nes"
    api.get_content_name()  # returns a string like "Super Mario Bros. (W) [!]"
    api.get_content_crc32_hash()  # returns a string like "d445f698"
    api.get_config_param('savefile_directory')  # read a config param (not all the params are supported!)
    
    # all the methods returns a true value on success, or thow exceptions on errors.
    """

    _socket = None
    _socket_ipaddr = "127.0.0.1"
    _socket_portnum = 55355
    _network_sleep_time = 0.1
    _version = ""

    def __init__(self, ipaddr="127.0.0.1", portnum=55355, network_sleep_time=0.1, check_connection=True):

        # Logging
        self.logger = logging.getLogger('RetroArchPythonApi')

        # Settings
        #self.settings = {}
        # TODO: read retroarch settings

        # Pathes
        #self.pathes = {}
        # TODO: self.pathes['settings'] = "$HOME/.config/retroarch.cfg"

        # RetroArch Config File
        #configfile = os.path.join(settings_path, 'retroarch.cfg')
        #self.pathes['configfile'] = configfile
        
        # UDP socket init
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # SOCK_DGRAM specifies that this is UDP
        #s.bind((ipaddr, portnum))
        #s.setblocking(0)  # set receive non-blocking.

        logging.info('Retroarch UDP socket created')
        
        # save ipaddr and portnum for later use
        self._socket_ipaddr = ipaddr
        self._socket_portnum = portnum
        self._network_sleep_time = network_sleep_time
        
        if not check_connection:
            return
    
        self.logger.info("Checking connection with Retroarch on " + ipaddr + ":" + str(portnum) + "...")
        
        # temp. add socket timeout
        self._socket.settimeout(1)
        
        self._version = self.get_version()
        if not self._version:
            self.logger.error("Connection timeout: make sure Retroarch is running, has network commands enabled and is connectable.")
            #self.logger.warning("Connection timeout: make sure Retroarch is running, has network commands enabled and is connectable (will retry connecting until killed).")
            #raise Exception("Connection timeout")
        #while not self._version:
        #    self._version = self.get_version()
        #    time.sleep(2)

        # remove socket timeout
        self._socket.settimeout(None)
        
        self.logger.info('Retroarch connection ok')
        
        retroarch_version_major = self._version.split(b'.')[0]
        retroarch_version_minor = b".".join(self._version.split(b'.')[1:])
        if int(retroarch_version_major) == 0 or (int(retroarch_version_major) == 1 and float(retroarch_version_minor) <= 8.4):
            self.logger.warning('current Retroarch ver. does not support GET_STATUS, SHOW_MSG and GET_CONFIG_PARAM commands. Please update to the lastest ver.')


    def show_msg(self, msg):
        """ Shows a message via the OSD """
        self._socket.sendto(b'SHOW_MSG ' + msg.encode('utf-8') + b'\n', (self._socket_ipaddr, self._socket_portnum))
        return True


    def clear_msgs(self):
        """ Clear all message shown via the OSD """
        self._socket.sendto(b'CLEAR_MSG\n', (self._socket_ipaddr, self._socket_portnum))
        return True
        
    def show_overlay_text(self, text, text_position=1):
        """ Shows an overlay text via the AI service """
        # https://docs.libretro.com/guides/ai-service/
        p = { "text": text, "text_position" : 2}
        import json
        print(b'SHOW_OVERLAY ' + json.dumps(p).encode('utf-8') + b'\n')
        self._socket.sendto(b'SHOW_OVERLAY ' + json.dumps(p).encode('utf-8') + b'\n', (self._socket_ipaddr, self._socket_portnum))
        return True
    
    def show_overlay_image(self, img_file_path):
        """ Shows an overlay image via the AI service """
        # https://docs.libretro.com/guides/ai-service/
        img_file_data = open(img_file_path, "rb").read()
        import base64
        img_file_base64_str = base64.b64encode(img_file_data).decode()
        p = { "image": img_file_base64_str }
        import json
        self._socket.sendto(b'SHOW_OVERLAY ' + json.dumps(p).encode('utf-8') + b'\n', (self._socket_ipaddr, self._socket_portnum))
        return True
        
    def clear_overlays(self):
        self._socket.sendto(b'CLEAR_OVERLAY\n', (self._socket_ipaddr, self._socket_portnum))
        return True
        
    def get_config_param(self, param_name):
        """ Read a param from the configuration (e.g. 'savefile_directory') """
        # ver. check to avoid freezing
        retroarch_version_major = self._version.split(b'.')[0]
        retroarch_version_minor = b".".join(self._version.split(b'.')[1:])
        if int(retroarch_version_major) == 0 or (int(retroarch_version_major) == 1 and float(retroarch_version_minor) <= 8.4):
            self.logger.error('current Retroarch ver. does not support GET_CONFIG_PARAM commands. Please update to the lastest ver.')
            return b""
        # else
        self._socket.sendto(b'GET_CONFIG_PARAM '  + param_name.encode('utf-8') + b'\n', (self._socket_ipaddr, self._socket_portnum))
        response_str, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
        param_value = response_str.split()[2]
        if param_value == "unsupported":
            raise Exception("unsupported param: " + param_name)
        # else
        return param_value


    def get_status(self):
        """ Returns a string summarizing the current status (e.g. 'GET_STATUS PLAYING Nestopia,Super Mario Bros. (W) [!],crc32=3337ec46') """
        # ver. check to avoid freezing
        retroarch_version_major = self._version.split(b'.')[0]
        retroarch_version_minor = b".".join(self._version.split(b'.')[1:])
        if int(retroarch_version_major) == 0 or (int(retroarch_version_major) == 1 and float(retroarch_version_minor) <= 8.4):
            self.logger.error('current Retroarch ver. does not support GET_STATUS command. Please update to the lastest ver.')
            return b""
        # else

        self._socket.sendto(b'GET_STATUS\n', (self._socket_ipaddr, self._socket_portnum))
        response_str, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
        return response_str.rstrip()


    def has_content(self):
        """ returns True if the Retroarch has some content loaded (paused or not)"""
        status_str = self.get_status()
        splitted_status_str = status_str.split(b",")
        if status_str==b"" or splitted_status_str[0].split(b" ")[1] == b'CONTENTLESS':
            return False
        else:
            return True
    

    def is_paused(self):
        """ returns True if the content is paused """
        status_str = self.get_status()
        splitted_status_str = status_str.split(b",")
        if status_str==b"" or splitted_status_str[0].split(b" ")[1] == b'PAUSED':
            return True
        else:
            return False
            

    def is_playing(self):
        """ returns True if the content is running """
        status_str = self.get_status()
        splitted_status_str = self.get_status().split(b",")
        status = splitted_status_str[0].split(b" ")[1]
        if status_str==b"" or  status == b'RUNNING' or status == b'PLAYING':
            return True
        else:
            return False
        

    def get_system_id(self):
        """ returns current system_id (e.g. 'nes') or the core name (e.g. 'Nestopia') """
        status_str = self.get_status()
        if status_str:
            splitted_status_str = status_str.split(b",")
            return splitted_status_str[0].split(b" ")[-1]
        else:
            return b""
        

    def get_content_crc32_hash(self):
        """ returns current content CRC32 hash as a string """
        status_str = self.get_status()
        if status_str and b"crc32=" in status_str:
            return status_str.split(b"crc32=")[1]
        else:
            return b""


    def get_content_name(self):
        """ returns current content name, from the ROM filename (e.g. 'Super Mario Bros. (W) [!]') """
        status_str = self.get_status()
        if status_str and b"crc32=" in status_str:
            return status_str.split(b",crc32=")[0].split(b",", maxsplit=1)[-1]
        else:
            return b""
        
        
    def get_version(self):
        """ returns current Retroarch version (as a string) """
        self._socket.sendto(b'VERSION\n', (self._socket_ipaddr, self._socket_portnum))
        response_str, addr = self._socket.recvfrom(16)
        return response_str.rstrip()


    def is_alive(self):
        """ returns True if Retroarch is running and connectable """
        self._socket.settimeout(1)  # temp. add socket timeout
        try:
            v = self.get_version()
            return True
        except:
            # timeout
            return False
        finally:
            self._socket.settimeout(None)  # remove socket timeout


    def quit(self):
        """Exit a running ROM"""

        if not self.has_content():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Quit')

        if self.is_paused():
            self.toggle_pause()
            time.sleep(self._network_sleep_time)

        self._socket.sendto(b'QUIT\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        self.logger.info('Rom Exited Successfull')
        return True


    def toggle_pause(self):
        """Toggle from Pause to Unpause mode
        Returns: The new State: "Pause" or "Unpause" Mode
        Returns: False an Error occured
        """

        if not self.has_content():
            self.logger.error('Rom is not running')
            return False

        self.logger.info('Send: Toggle Pause')

        self._socket.sendto(b'PAUSE_TOGGLE\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        
        time.sleep(self._network_sleep_time)
        
        if self.is_paused():
            return 'paused'
        else:
            return 'unpaused'

            
    def read_core_ram(self, address, length):
        """ read from current core RAM at address length-bytes. Returs an array of bytes. """
        
        # ver. check to avoid freezing
        retroarch_version_major = self._version.split(b'.')[0]
        retroarch_version_minor = b".".join(self._version.split(b'.')[1:])
        if int(retroarch_version_major) == 0 or (int(retroarch_version_major) == 1 and float(retroarch_version_minor) <= 8.4):
            self.logger.error('current Retroarch ver. does not support READ_CORE_RAM command. Please update to the lastest ver.')
            return ""
        # else
        
        if not self.has_content():
            self.logger.error('No content loaded')
            return []
                
        self.logger.info('Send: Read core ram')
        
        cmd = b"READ_CORE_RAM " + ("%x" % address).encode() + b" " + ("%d" % length).encode() + b'\n'

        self._socket.sendto(cmd, (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        
        time.sleep(self._network_sleep_time)
        
        answer, addr = self._socket.recvfrom(4096) # buffer size is 4096 bytes - MEMO: blocking until something is received
        # TODO: read by blocks
        
        if answer.startswith(b'READ_CORE_RAM'):
            response_bytes = answer.split()[2:]  # from 'READ_CORE_RAM f E5 C4 09 F0 2A 00 00 31 00 01\n'
            return response_bytes
        else:
            raise Exception("invalid answer: " + str(answer))
            
    
    def write_core_ram(self, address, buf):
        """ write into current core RAM from address the array of bytes passed into buf. """
        
        # ver. check
        retroarch_version_major = self._version.split(b'.')[0]
        retroarch_version_minor = b".".join(self._version.split(b'.')[1:])
        if int(retroarch_version_major) == 0 or (int(retroarch_version_major) == 1 and float(retroarch_version_minor) <= 8.4):
            self.logger.error('current Retroarch ver. does not support WRITE_CORE_RAM command. Please update to the lastest ver.')
            return False
            
        if not self.has_content():
            self.logger.error('No content loaded')
            return False
            
        cmd = b"WRITE_CORE_RAM " + ("%x" % address).encode()
        for b in buf:
            cmd += b" %02x" % b
        cmd += b"\n"
        self.logger.debug('Sending: ' + str(cmd))  # e.g. b"WRITE_CORE_RAM f E5 C4 09 F0 2A 00 00 31 00 01\n"

        self._socket.sendto(cmd, (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        return True

    
    def toggle_fullscreen(self):
        """Toggle from Window to Fullscreen mode
        #Returns: The new State: "Fullscreen" or "Window" Mode
        #Returns: False an Error occured
        """

        self.logger.info('Send: Fullscreen Toggle')
        
        self._socket.sendto(b'FULLSCREEN_TOGGLE\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        
        time.sleep(self._network_sleep_time)
        
        # read current fullscreen status
        video_fullscreen_status = self.get_config_param("video_fullscreen")
        if video_fullscreen_status == b"true":
            return("Fullscreen")
        else:
            return("Window")
    

    def load_state(self):
        """ Load currently-selected savestate """

        if not self.has_content():
            self.logger.error('No content loaded')
            return False

        self._socket.sendto(b'LOAD_STATE\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        return True
        
        
    def save_state(self):
        """ Saves currently-selected savestate """

        if not self.has_content():
            self.logger.error('No content loaded')
            return False

        self.logger.info('Send: Save State')

        self._socket.sendto(b'SAVE_STATE\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        return True


    def reset(self):
        """ Reset a running content """

        if not self.has_content():
            self.logger.error('No content loaded')
            return False

        self.logger.info('Send: Reset')

        if self.is_paused():
            self.toggle_pause()

        self._socket.sendto(b'RESET\n', (self._socket_ipaddr, self._socket_portnum))
        # if no socket error assume the command was successful
        return True


if __name__ == '__main__':
	ra = RetroArchPythonApi()
	prev_content = ""
	while(True):
		print(ra.has_content())
		if ra.has_content():
			curr_content = ra.get_content_name()
			if curr_content != prev_content:
				print("now playing: " + curr_content.decode().strip("\'"))
				prev_content = curr_content
		try:
			time.sleep(5)
		except KeyboardInterrupt:
			# clean exit
			ra.quit()
