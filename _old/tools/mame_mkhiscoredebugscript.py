#!/usr/bin/python

import sys

REQ_GAME_NAME=sys.argv[1]

OUTFILE_PATH=REQ_GAME_NAME + ".mamedebug"

HISCORE_PATH="/home/andy/.mame/dats/hiscore.dat"

hiscore_file = open(HISCORE_PATH)

hiscore_rows_to_process = []

while(True):
	line = hiscore_file.readline()
	
	if not line:
		# EOF
		break 
	elif line.strip() == "":
		# line was empty
		continue
		     
	line = line.strip()
	if line.startswith(";"):
		continue
	if line.endswith(":"):
		# check if game matches
		line_gamename = line.split(':')[0]
		if not line_gamename == REQ_GAME_NAME:
			continue
		# else reads the hiscore rows
		while(True):
			line = hiscore_file.readline()
			if line.strip() == "":
				# end of codes
				break
			if not line.startswith("@"):
				# comments?
				continue
			# else
			hiscore_rows_to_process.append(line.strip())
		# end while
	# end if
# end while

if len(hiscore_rows_to_process)==0:
	print("nothing found!")
	sys.exit(1)

# else

outfile = open(OUTFILE_PATH, "w")

#conditions = []
# sample output: "wp ffe108,cc,w,(maincpu.b@FFE108==00 && maincpu.b@FFFE1D3==41),{save thunderl.hi,ffe108,cc; g}"
single_debugger_command = ""

print("written output file: ")

row_counter = 0
for row in hiscore_rows_to_process:
	splitted_row = row.split(",")
	cputag = splitted_row[0].split(":")[1]
	addresspace = splitted_row[1]
	if not addresspace=="program":
		print("unsupported: " + addresspace)
		sys.exit(1)
	address = splitted_row[2]
	length = splitted_row[3]
	start_byte = splitted_row[4]
	end_byte = splitted_row[5]
	if len(splitted_row)==7:
		print("unsupported: prefill")
		sys.exit(1)
		#prefill = splitted_row[6]
	
	output_line = "wp " + address + "," + length + ",rw,"
	
	#2FIX: adds the conditions: start conditon
	#output_line += "(" + cputag + ".w@" + address + "==" + start_byte
	
	#2FIX: end condition
	#end_address = str(format(int(address, 16) + int(length, 16) - 1, "x"))
	#output_line += " && " + cputag + ".w@" + end_address + "==" + end_byte + ")"
	output_line += "1"
	
	# output file
	row_counter += 1
	output_line += ",{save " + REQ_GAME_NAME + ("-part%.2d" % row_counter) + ".hi," + address + "," + length + "; g}"
	single_debugger_command += "save " + REQ_GAME_NAME + ("-part%.2d" % row_counter) + ".hi," + address + "," + length + "; "
	
	print(output_line)
	outfile.write(output_line+"\n")
# end for

outfile.write("g\n")

print("")
single_debugger_command += "g"
print("single debugger command: " + single_debugger_command)
print("")

print("tip: use with: mame139 -v -debug -debugscript " + REQ_GAME_NAME + ".mamedebug "  + REQ_GAME_NAME)
if len(hiscore_rows_to_process)>1:
	print("then: cat " + REQ_GAME_NAME + "-part*.hi > " + REQ_GAME_NAME + ".hi")
	
	
