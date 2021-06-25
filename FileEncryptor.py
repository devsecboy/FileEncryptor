from os import listdir
from os.path import isfile, join
import os
import gnupg
import sys
import subprocess
import argparse
import re

def PrintBanner():
    print  ("\n\n\n8888888888 d8b 888               8888888888                                             888                    \n"
            "888        Y8P 888               888                                                    888                    \n"
            "888            888               888                                                    888                    \n"
            "8888888    888 888  .d88b.       8888888    88888b.   .d8888b 888d888 888  888 88888b.  888888 .d88b.  888d888 \n"
            "888        888 888 d8P  Y8b      888        888  88b d88P     888P    888  888 888  88b 888   d88  88b 888P    \n"
            "888        888 888 88888888      888        888  888 888      888     888  888 888  888 888   888  888 888     \n"
            "888        888 888 Y8b.          888        888  888 Y88b.    888     Y88b 888 888  88P Y88b. Y88..88P 888     \n"
            "888        888 888  Y88888       8888888888 888  888  Y8888P  888      YY88888 88888P.   Y888   Y88P   888     \n"
            "                                                                           888 888                             \n"
            "                                                                      Y8b d88P 888                             \n"
            "                                                                       YY88PP  888                           \n\n\n")  
def ConfigureGPG():
    gpg=None
    if os.name == "nt":
        gpg = gnupg.GPG("gpg")
        gpg.encoding = 'utf-8'
        return gpg
    elif os.name == "posix":
        p = subprocess.Popen("ls -ld ~/.gnupg", stdout=subprocess.PIPE, shell=True)
        output = (p.communicate()[0]).strip()
        try:
            output = str(output, 'utf-8')
        except: 
            pass
        output = (output[output.rfind(' '):]).strip()
        p_status = p.wait()
        try:
            gpg = gnupg.GPG(gnupghome=output) 
        except TypeError:
            gpg = gnupg.GPG(homedir=output)
        gpg.encoding = 'utf-8'
        return gpg
    return gpg

def ImportPGPKeys(gpg):
    directory = 'Keys'
    for dir in os.listdir(directory):
        path = os.path.join(directory, dir)
        print ("\n\nEntering to " + dir + " directory...." )
        publicKeyFiles = [f for f in listdir(path) if isfile(join(path, f))]
        i=1
        for publicKeyFile in publicKeyFiles:
            filePath = path + "/" + publicKeyFile
            sys.stdout.write("\r" + "Processing files :=> "+ str(i) +"/" + str(len(publicKeyFiles)))
            sys.stdout.flush()
            i+=1;
            with open(filePath) as keyContent:
                key_data = keyContent.read()
                import_result = gpg.import_keys(key_data)

    keyList = open("KeysList.txt", "w") 
    public_keys = gpg.list_keys()
    for k in public_keys:
        keyList.write(k['uids'][0] + "\n")
    keyList.close()

def GetRecipients(excludeExpiredOrInvalid, recipientslist):
    recipients=[]
    with open('KeysList.txt') as keys:
        lines = keys.readlines()
        for line in lines:
            if any(re.findall(recipientslist, line, re.IGNORECASE)):
                email=line[:line.find(",")]
                start=email.index('<')+1
                end=email.index('>',start)
                email=email[start:end]
                if email not in excludeExpiredOrInvalid:
                    recipients.append(line[:line.find(",")])
    return recipients

def EncryptFile(recipientslist, filename):
    encrypted=False
    with open(filename, "rb") as f:
        excludeExpiredOrInvalid=[]
        while (encrypted == False):
            recipients = GetRecipients(excludeExpiredOrInvalid, recipientslist)
            status = gpg.encrypt_file(f,recipients,output=filename+".gpg",always_trust=True)
            if status:
                encrypted = True
                print ("\n\nok: " + str(status.ok))
                print ("status: "+ str(status.status))
                print ("stderr: "+str(status.stderr))
            else:
                start=(status.stderr).index('<')+1
                end=(status.stderr).index('>',start)
                excludeExpiredOrInvalid.append(status.stderr[start:end])
        if(len(excludeExpiredOrInvalid) != 0):
            print ("\n\n\n==================================================")
            print ("Skipped following keys as they are expired or invalid")
            print (excludeExpiredOrInvalid)

if __name__ == "__main__":
    PrintBanner()
    parser = argparse.ArgumentParser(description='Tool to import and encrypt report using multiple recipient')
    parser.add_argument("-i", "--importkeys", help="Use the program to import pgp keys from 'Keys' directory", default=False, required=False, action='store_true')
    parser.add_argument("-e", "--encrypt", help="Use the program to encrypt the file", default=False, required=False, action='store_true')
    parser.add_argument("-w", "--windows", help="Tool runs on windows", default=False, required=False, action='store_true')
    parser.add_argument("-l", "--linux", help="Tool runs on linux", default=False, required=False, action='store_true')
    parser.add_argument("-r", "--recipient", metavar='recipient',help="It can be a single recipient or organization. Ex. sample@example.org or example.org or 'example.org|example.com'", default="", required=False)
    parser.add_argument("-f", "--filepath", metavar='filepath',help="Filepath of the file to be encrypted", default="", required=False)
    args = parser.parse_args()
    
    gpg=ConfigureGPG()
    if gpg != None:
        if args.importkeys:
            ImportPGPKeys(gpg)
        
        if args.encrypt:
            if args.recipient == "" or args.filepath == "":
                print ("\n\n\n==========================================")
                print ("Error :==> Missing recipient and filepath\n\n")
                parser.print_help()
            EncryptFile(args.recipient, args.filepath)
    else:
        print ("Operating System type on found")