#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MEMO: RetroArch >= 1.8.5 is required
# usage: enable `network_cmd_enable` in retroarch, set HISCORE_PATH and HISCORE_DAT_PATH in state2hi.py or the environ

import sys
import os
import logging
import time
from io import BytesIO


HISCORE_PATH_USE_SUBDIRS=False

logging.getLogger().setLevel(logging.DEBUG)

# add to sys.path relative to the current running script    https://stackoverflow.com/questions/8663076/python-best-way-to-add-to-sys-path-relative-to-the-current-running-script
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from retroarchpythonapi import RetroArchPythonApi
while True:
	try:
		retroarch = RetroArchPythonApi()
		break
	except:
		logging.error("connection error, will retry in 2s...")
		time.sleep(2)
# end while

# path where .hi files will be loaded and saved
HISCORE_PATH = str(retroarch.get_config_param('savefile_directory'), 'utf-8')  # store hiscores in savefile_directory by default
#HISCORE_PATH = os.path.expanduser("~/.mame/hi")
if("HISCORE_PATH" in os.environ):
	HISCORE_PATH = os.environ['HISCORE_PATH']

hiscore_inited_in_ram = False
prev_content_name = None
hiscore_rows_to_process = []
hiscore_file_bytesio = BytesIO()
hiscore_file_path = ""


while True: 
	# wait for some content to be loaded
	while not (retroarch.is_alive() and retroarch.has_content()):
		hiscore_inited_in_ram = False
		prev_content_name = None
		time.sleep(5)
	# end while
	
	curr_content_name = str(retroarch.get_content_name(), 'utf-8')
	if not curr_content_name:
		hiscore_inited_in_ram = False
		prev_content_name = None
		time.sleep(5)
		continue
	# end if
	
	# detect game change
	if curr_content_name != prev_content_name:
		prev_content_name = curr_content_name
		
		hiscore_inited_in_ram = False
		
		# detect the system from the core name
		reported_system_id = str(retroarch.get_system_id(), 'utf-8')
		candidate_systems = []
		logging.debug("reported_system_id: " + reported_system_id)
		if reported_system_id in [ "Nestopia", "nes" ]:
			candidate_systems = [ "nes", "famicom", "fds", "nespal" ]
		elif reported_system_id == "super_nes":
			candidate_systems = [ "snes", "snespal" ]
		elif reported_system_id == "game_boy":
			candidate_systems = [ "gameboy", "gbcolor", "supergb" ]
		elif reported_system_id == "mega_drive":
			candidate_systems = [ "genesis", "megadrij", "megadriv", "sms", "smsj", "smspal", "gamegear", "gamegeaj", "segacd" ]
		elif reported_system_id == "pc_engine":
			candidate_systems = [ "pce", "tg16", "sgx" ]
		# TODO: more systems  http://www.progettoemma.net/mess/sysset.php
		
		logging.debug("game was changed, looking hiscore data for " + curr_content_name + "...")

		from state2hi import get_hiscore_rows_from_game
		# TODO: remove deps
		hiscore_rows_to_process = get_hiscore_rows_from_game(candidate_systems, curr_content_name)
		if len(hiscore_rows_to_process)==0:
			logging.error("nothing found in hiscore.dat for current game")
			continue
		else:
			logging.debug("found hiscore patches")
	
		# try to read the .hi hiscore file
		hiscore_file_data = None
		#system = candidate_systems[0] # TODO: guess current system from ???
		#if HISCORE_PATH_USE_SUBDIRS:
		#	hiscore_file_path = HISCORE_PATH + "/" + system + "/" + curr_content_name + ".hi"
		#else:
		#	hiscore_file_path = HISCORE_PATH + "/" + curr_content_name + ".hi"
		hiscore_file_path = HISCORE_PATH + "/" + curr_content_name + ".hi"
		
		try:
			hiscore_file = open(hiscore_file_path, 'rb')
			hiscore_file_data = hiscore_file.read()
			logging.info("read hiscore file: " + hiscore_file_path + " len: " + str(len(hiscore_file_data)))
			hiscore_file.close()
			hiscore_file_bytesio = BytesIO(hiscore_file_data)  # keep a copy in memory
		except:
			logging.info("hiscore file not found, will be created...")
			#logging.exception("")
		
		# DELETE
		# if reported_system_id == "mega_drive":  # TODO: test core==genplusgx
			# # need to byteswap hiscore_file_bytesio
			# hiscore_file_bytesio_swapped_buf = hiscore_file_bytesio.getbuffer()
			# hiscore_file_bytesio_len = hiscore_file_bytesio_swapped_buf.nbytes
			# hiscore_file_bytesio = BytesIO(b"\x00" * hiscore_file_bytesio_len)  # zero fill init
			# hiscore_file_bytesio_buf = hiscore_file_bytesio.getbuffer()
			# for i in range(0, hiscore_file_bytesio_len-1, 2):
				# hiscore_file_bytesio_buf[i] = hiscore_file_bytesio_swapped_buf[i+1]
				# hiscore_file_bytesio_buf[i+1] = hiscore_file_bytesio_swapped_buf[i]
			# #hiscore_file_bytesio.flush()
			# hiscore_file_bytesio.seek(0)  # rewind
		#end if reported_system_id == "mega_drive"
	# end if game was changed
	
	curr_hiscore_in_ram_bytesio = BytesIO()  # read from live memory to here
	for row in hiscore_rows_to_process:
		logging.debug("processing: " + row)
		splitted_row = row.split(",")
		cputag = splitted_row[0].split(":")[1]
		addresspace = splitted_row[1]
		if not addresspace=="program":
			logging.error("unsupported: " + addresspace)
			sys.exit(1)
		address = int(splitted_row[2], base=16)
		length = int(splitted_row[3], base=16)
		start_byte = int(splitted_row[4], base=16)
		end_byte = int(splitted_row[5], base=16)
		
		# fix genesis address
		if reported_system_id == "mega_drive" and address > 0xff0000:
			address -= 0xff0000
		
		response_bytes = retroarch.read_core_ram(address, length)
		#logging.debug(len(response_bytes))
		#logging.debug(int(response_bytes[0], base=16))
		#logging.debug(start_byte)
		if response_bytes == [b'-1']:
			logging.error("invalid address found in hiscore datfile (skipped): " + str(hex(address)))
			break
		
		if response_bytes and len(response_bytes)>1 and reported_system_id == "mega_drive":  # TODO: test core==genplusgx
			# need to byteswap response_bytes
			response_bytes_swapped = list()
			for i in range(0, len(response_bytes)-1, 2):
				response_bytes_swapped.append(response_bytes[i+1])
				response_bytes_swapped.append(response_bytes[i])
			response_bytes = response_bytes_swapped
			if ( len(response_bytes) % 2 ):
				logging.warning("odd sizes prolly wont work well with this core due to swapping")
				response_bytes.append(b'00')  # try to fix
		#end if
			
		# 1st loop: check start_byte and end_byte, if the match the code and an hiscore file was read, init the memory
		if hiscore_file_bytesio.getbuffer().nbytes > 0 and hiscore_inited_in_ram == False and response_bytes and int(response_bytes[0], base=16) == start_byte and int(response_bytes[-1], base=16) == end_byte:
			logging.info("start_byte and end_byte matches, writing into core memory...")
			# write data from hiscore_file_bytesio buffer
			buf = hiscore_file_bytesio.read(length)
			hiscore_file_bytesio.seek(0)  # rewind
			
			if reported_system_id == "mega_drive":  # TODO: test core==genplusgx
				# need to byteswap buf before writing into memory
				buf_swapped = buf   # TODO: faster method using bytearray() + append
				buf = bytes()
				for i in range(0, len(buf_swapped)-1, 2):
					buf += bytes([ buf_swapped[i+1] ])
					buf += bytes([ buf_swapped[i] ])
				#if ( len(buf) % 2 ):
				#	logging.warning("odd sizes prolly wont work well with this core due to swapping")
				#	buf += bytes( b'00' )  # try to fix
			# end if

			if retroarch.write_core_ram(address, buf) == True:
				# successfull memory write
				buf = hiscore_file_bytesio.read(length)  # reload
				curr_hiscore_in_ram_bytesio.seek(0)  # rewind
				curr_hiscore_in_ram_bytesio.write(buf)
				if row == hiscore_rows_to_process[-1]:
					# TODO: check if all the rows were written
					hiscore_inited_in_ram = True
					retroarch.show_msg("Hiscore loaded")
		
		elif response_bytes:
			# not the first loop
			# append read bytes to curr_hiscore_in_ram_bytesio
			for b in response_bytes:
				curr_hiscore_in_ram_bytesio.write(bytes([ int(b, base=16) ] ))
	# end for rows
	
	# check if hiscore data is changed
	curr_hiscore_in_ram_bytesio.flush()
	curr_hiscore_in_ram_bytesio.seek(0)  # rewind
	#print(curr_hiscore_in_ram_bytesio.getvalue())
	#print(hiscore_file_bytesio.getvalue())
	curr_hiscore_in_ram_bytesio_value = curr_hiscore_in_ram_bytesio.getvalue()
	if len(curr_hiscore_in_ram_bytesio_value) > 0 and bool(any(c != 0 for c in curr_hiscore_in_ram_bytesio_value)) and curr_hiscore_in_ram_bytesio_value != hiscore_file_bytesio.getvalue():
		# (over-)write to the hiscore file
		#if HISCORE_PATH_USE_SUBDIRS and not os.path.exists(HISCORE_PATH + "/" + system):
		#	os.mkdir(HISCORE_PATH + "/" + system)
		if not os.path.isfile(hiscore_file_path):
			# show msg only at the 1st save
			retroarch.show_msg("Hiscore file created")
		hiscore_file = open(hiscore_file_path, 'wb') # write+binary mode
		hiscore_file.write(curr_hiscore_in_ram_bytesio_value)
		hiscore_file.close()
		hiscore_file_bytesio = curr_hiscore_in_ram_bytesio  # keep the reference in memory
		logging.info("written hiscore file " + hiscore_file_path)
		#NO? retroarch.show_msg("Hiscore saved")  # too many alerts?
	else:
		logging.debug("hiscore data unchanged in memory, nothing to save")
	# end if
	
	# sleep to avoid sending too many read/write commands
	time.sleep(5)
# end while retroarch is running

