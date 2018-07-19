# Python - bat file processor
# Use to manipulate BAT phone exports
# python batmigrator.py <input file of bat export> <DeviceList.txt> <sitesubnets.txt>
# python batmigrator.py export.txt DeviceList.txt sitesubnets.txt
#
# To Run via MAC List:
# python batMigrator.py ASL-Final-Export.txt ASL-Devices.csv

# will dump output into batmigrator-output.csv


import csv  # imports the csv module
import sys  # imports the sys module
import os
import re
import time
from collections import OrderedDict
#from pathlib import Path
from netaddr import IPNetwork, IPAddress


reader = csv.reader(open('phonebuttontemplate.csv', 'r', newline=''))
PhoneButtonList = dict(reader)

filedir = os.path.dirname(__file__)
inputdir = os.path.join(filedir, 'input')
outputdir = os.path.join(filedir, 'output')
# outputdir = Path("output/")
regexinputfile = os.path.join(inputdir,'regex.csv')
logfile = open(os.path.join(outputdir,'log.txt'), 'w+', newline='')

print("The DN expansion file file is ", regexinputfile)

regexinput = open(regexinputfile, 'rt', newline='')  # Opens the csv file
reader = csv.reader(regexinput) # Creates the reader object

# Build OrderedDict for modDNwDP
try:
    myordereddict = OrderedDict(reader)
    # print(myordereddict)
    for findkey, replacevalue in myordereddict.items():
        print(findkey, replacevalue)
        logfile.write(findkey + replacevalue + "\n")

except ValueError:
    breakpoint()

finally:
    regexinput.close()

datestring = time.strftime("%Y%m%d")

# This section determines how the script determines a list of devices to convert.
# MAC - Requires the second argument to contain a list of MAC addresses
# Subnet - Requires the second argument to be a CSV in the format MAC,IP - Requires the third argument to be a CSV in format SITECODE,X.X.X.X/XX
# Device Pool - Requires a mapping in the modSiteFromDP function, no arguments are needed at this time. An input file may be added at a later date.

MatchType = ''

DevFormatPrompt = input('Would you like to analyze devices via MAC, Subnet or DP: (m, s, or d) ')
if DevFormatPrompt == 'm':
    MatchType = 'mac'
    reader = csv.reader(open(os.path.join(inputdir, sys.argv[2]), 'rU', newline=''))
    DeviceMACList = dict(reader)
elif DevFormatPrompt == 's':
    MatchType = 'ip'
    # Create the DeviceIPList dictionary from CSV in format DeviceName,IPAddress or DeviceName,SITECODE if matching on MACs
    reader = csv.reader(open(os.path.join(inputdir, sys.argv[2]), 'rU', newline=''))
    DeviceIPList = dict(reader)
    # Create the sitesubnets dictionary from CSV in format SITECODE,X.X.X.X/XX
    reader = csv.reader(open(os.path.join(inputdir, sys.argv[3]), 'rU', newline=''))
    sitesubnets = dict(reader)
    # print sitesubnets
elif DevFormatPrompt == 'd':
    MatchType = 'dp'
    #reader = csv.reader(open(os.path.join(inputdir, sys.argv[2]), 'rbU', newline=''))
    #DeviceDPList = dict(reader)
else:
    print("No Match")

# BEGIN FUNCTIONS
# ----------------------------------------
def modSiteFromMAC(devicename):
    try:
        sitecode = DeviceMACList[devicename]
        return sitecode
    except KeyError:
        return "NotToBeMigrated"


def modSiteFromDP(dp): # Used to determine what device pools are to be migrated and sets the site code for each
    dict = {'US-HI-SRST-dp': 'USHI',
            'US-KX-GW-dp': 'USKX',
            'US-KX-SRST-dp': 'USKX',
            'US-PR-SRST-dp': 'USPR',
            'USIF-Admin3-SRST-dp': 'USIF',
            'USIF-Admin3-dp': 'USIF',
            'USIF-Analog-dp': 'USIF',
            'USIF-IT-3-dp': 'USIF',
            'USRB-Admin4-dp': 'USRB',
            'USRB-Analog-dp': 'USRB',
            'USRB-IT-4-dp': 'USRB'}
            #'USIF-Services-dp': 'USIF',
            #'USIRB-Services-dp': 'USRB',
            #'USIF-UCCE5-dp': 'USIF',
            #'USIF-UCCE7-dp': 'USIF',
            #'USRB-UCCE6-dp': 'USRB',
            #'USRB-UCCE8-dp': 'USRB',
            #'USUCM-UCCE-dp': 'UCCE',
            #'USUK-UCCE8-dp': 'UCCE',
    try:
        sitecode = dict[dp]
        return sitecode
    except KeyError:
        return "NotToBeMigrated"


def modSiteFromIP(devicename): # Used to determine which phones based on IP are to be migrated and sets the site code for each
    try:
        # Check DeviceIPList for devicename match & return IP, if not found return NotToBeMigrated
        DeviceIP = DeviceIPList.get(devicename, "NotToBeMigrated")
        if DeviceIP != "NotToBeMigrated":
            for subnet in sitesubnets:
                if IPAddress(DeviceIP) in IPNetwork(subnet):  # Uses netaddr module to Match IP to Subnet? What is Subnet here?
                    sitecode = sitesubnets.get(subnet, "NotToBeMigrated")  # Check sitesubnets for subnet match & return sitecode, if not found return NotToBeMigrated
                    return sitecode
                else:
                    sitecode = "NotToBeMigrated"
                    return sitecode
        else:
            sitecode = "NotToBeMigrated"
            return sitecode
    except KeyError:
        return "NotToBeMigrated"


def modDevicePool(regioncode, devicename):
    searchObj = re.search(r'(\S{2})', devicename, re.M | re.I)
    if searchObj.group(1) == "SE":
            regioncode = regioncode + " Endpoints"
    elif searchObj.group(1) == "AN" or searchObj.group(1) == "AT" or searchObj.group(1) == "VG":
            regioncode = regioncode + " Analog"
    return regioncode


def modCallPickup(callpickup):
    if callpickup:
        callpickup = newSiteCode + " " + callpickup
        if not callpickup in cpexport:
            cpexport.append(callpickup)
            cp.writerows([cpexport])
    return callpickup


def modmoh(mohsourceid):
    if mohsourceid != '':
        mohsourceid = mohLookup(mohsourceid)
    return mohsourceid


def modDeviceDesc(desc, dn):
    searchObj = re.search(r'(\S.*)\sucm.', desc, re.M | re.I)
    if searchObj and dn:
        if newSiteCode != 'NotToBeMigrated':
            desc = newSiteCode + " " + searchObj.group(1) + " " + dn[1:]
        return desc
    searchObj = re.search(r'(\S.*)\-ucm.', desc, re.M | re.I)
    if searchObj and dn:
        if newSiteCode != 'NotToBeMigrated':
            desc = newSiteCode + " " + searchObj.group(1) + " " + dn[1:]
        return desc
    searchObj = re.search(r'(.*)', desc, re.M | re.I)
    if searchObj and dn:
        if newSiteCode != 'NotToBeMigrated':
            desc = newSiteCode + " " + searchObj.group(1) + " " + dn[1:]
        return desc
    if searchObj:
        if newSiteCode != 'NotToBeMigrated':
            print("Blank Description - ", desc)
            logfile.write("Blank Description - " + desc +"\n")
            desc = newSiteCode + " " + searchObj.group(1)
        return desc
# modify device description field to remove any characters/space at the end that begins with ' ucm...' or '-cucm...'

def moduserassociation (userID, device):
    user.append(device)
    user.append(userID)
    b.writerows([user]) # Write the deivcename,userid to the userassociation.csv file
    return '' # Return a blank string to blank out the user association


def modinterestingdn(dn):
    if dn:
        interestingdns.append(dn)


def moddnexport(dn):
    if dn:
        dnexport.append(dn + '\tStaging ' + newSiteCode + ' ' + datestring + '\tOn Cluster')
        c.writerows([dnexport])


def mod86dnexport(dn,oldPT):
    if dn:
        dn86export.append(dn + '\t' + oldPT + '\tStaging ' + newSiteCode + ' ' + datestring)
        d.writerows([dn86export])
        rp86file.write(dn + "\t" + oldPT + "\t" + newSiteCode + " CDW " + datestring + "\tNANP\tNULL\tTEMP SME to MC\troute\tfalse\tfalse\t\t\t\t\tNo Error\n")


def mod86macupdate(mac):
    if mac:
        mac86file.write('<command><updatePhone><name>' + mac + '</name>\n\n<newName>SEP' + str(dummymac) + '</newName></updatePhone></command>\n\n\n\n')
        macmapfile.write(mac + ',SEP' + str(dummymac) + '\n')


def mod105macupdate(mac):
    if mac:
        mac105file.write('<command><updatePhone><name>SEP' + str(dummymac) + '</name>\n\n<newName>' + mac +'</newName></updatePhone></command>\n\n\n\n')

# -----------------------------------------------------------BEGIN DN MODS-------------------------------------
def modDNwDP(dn):
    newDN = ''
    try:
        for findkey, replacevalue in myordereddict.items():
            #print (findkey, replacevalue)
            searchObj = re.search(findkey, dn, re.M | re.I)
            if searchObj:
                newDN = replacevalue + searchObj.group(1)
                #print("Matched! The expanded DN is", newDN)
                if 'BadDN' in newDN and dn !='':
                    print("DN or SD Issue: " + row[devicenameidx] + " - " + dn)
                    logfile.write("DN or SD Issue: " + row[devicenameidx] + " - " + dn +"\n")
                return newDN

    except ValueError:
        breakpoint()

def modDNDescription(dn, desc, newSiteCode):
    if dn:
        dn = modDNwDP(dn)
        desc = newSiteCode + " " + desc + " " + dn[1:]
        return desc
    else:
        return dn


# -----------------------------------------------------------END DN MODS---------------------------------------
def modCSS(css):
    searchObj = re.search(r'.*Long Distance$', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " LD"
        return css
    searchObj = re.search(r'.*LD$', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " LD"
        return css
    searchObj = re.search(r'.*International$', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Intl"
        return css
    searchObj = re.search(r'.*Internal$', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Internal"
        return css
    searchObj = re.search(r'.*Local$', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Local"
        return css
    searchObj = re.search(r'.*International', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Intl"
        return css    
    searchObj = re.search(r'.*LD', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " LD"
        return css
    searchObj = re.search(r'.*Long Distance', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " LD"
        return css
    searchObj = re.search(r'.*Local', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Local"
        return css
    searchObj = re.search(r'.*Internal', css, re.M | re.I)
    if searchObj:
        css = "DN " + newSiteCode + " Internal"
        return css
    else:
        css = "DN " + newSiteCode + " LD"
        return css


def modpartition(partition):
    if partition:
        partition = 'Staging ' + newSiteCode
    return partition


def modbuttontemplate(template):
    try:
        template = PhoneButtonList[template]
        return template
    except KeyError:
        # print "Phone Button Template missing from List: " + template
        return template


def modsoftkeytemplate(template):
    searchObj = re.search(r'^(.*)', template, re.M | re.I)
    newTemplate = softkeyTemplateLookup(template)
    return newTemplate


def modcommondevicecfg():
    newCDC = newRegionCode + " User Endpoint"
    return newCDC


def modXML(devtype, XML):
    if devtype == 'Cisco 7941':
        # 86 to 91 7941 phone - remove logserver
        XML = re.sub(r"(.*)<logServer></logServer>(.*)", r'\1\2', XML)
    return XML


def modcfwdest(num, newSiteCode):
    # try to mod based on dn
    newnum = modDNwDP(num)  # Send the number to the modDNwDP module and if no matches are found, continue...
    #if newnum != num:
    #    searchObj = re.search(r'^9(\d{7})$', num, re.M | re.I)
    #    if searchObj:
    #        newnum = "9" + searchObj.group(1)  # Set to 9 + 7 digits
    #    return newnum
    #searchObj = re.search(r'^9(\d{10})$', num, re.M | re.I)
    #if searchObj:
    #    newnum = "91" + searchObj.group(1)  # Set to 91 + 10 digits
    #    return newnum
    #searchObj = re.search(r'^91(\d{10})$', num, re.M | re.I)
    #if searchObj:
    #    newnum = "91" + searchObj.group(1)  # Set to 91 + 10 digits
    #    return newnum
    #if newnum != "":
    #    # newnum = num + "-CDWUnmodified" # Returned if none of the above match
    return newnum


def modPhoneLoad(type):
    dict = {'Cisco 6921': '',  # SCCP69xx.9-4-1-3SR1
            'Cisco 6941': '',  # SCCP69xx.9-4-1-3SR1
            'Cisco 6945': '',  # SCCP6945.9-4-1-3
            'Cisco 7841': '',  # sip78xx.10-2-1-12
            'Cisco 7906': '',  # SCCP11.9-4-2-1S
            'Cisco 7911': '',  # SCCP11.9-4-2-1S
            'Cisco 7912': '',
            'Cisco 7921': '',  # CP7921G-1.4.5.3
            'Cisco 7925': '',  # CP7925G-1.4.5.3
            'Cisco 7936': '',  # cmterm_7936.3-3-21-0
            'Cisco 7937': '',  # apps37sccp.1-4-5-7
            'Cisco 7940': '',  # P0030801SR02
            'Cisco 7941': '',  # SCCP41.9-4-2-1S
            'Cisco 7942': '',  # SCCP42.9-4-2-1S
            'Cisco 7945': '',  # SCCP45.9-4-2-1S
            'Cisco 7960': '',  # P0030801SR02
            'Cisco 7961G-GE': '',  # SCCP41.9-4-2-1S
            'Cisco 7961': '',  # SCCP41.9-4-2-1S
            'Cisco 7962': '',  # SCCP42.9-4-2-1S
            'Cisco 7965': '',  # SCCP45.9-4-2-1S
            'Cisco 7970': '',  # SCCP70.9-4-2-1S
            'Cisco 7971': '',  # SCCP70.9-4-2-1S
            'Cisco 7975': '',  # SCCP75.9-4-2-1S
            'Cisco 8831': '',  # sip8831.10-3-1-16
            'Cisco 8841': '',  #
            'Cisco 8851': '',
            'Cisco 8861': '',
            'Cisco 8945': '',
            'Cisco 9951': '',  # sip9951.9-4-2-13
            'Cisco 9971': '',
            'Cisco 8961': '',
            'Cisco ATA 186': '',
            'Cisco VGC Phone': '',
            'Analog Phone': '',
            'CTI Port': '',
            'Cisco IP Communicator': '',
            'Third-party SIP Device (Advanced)': '',
            'Third-party SIP Device (Basic)': '',
            'Cisco TelePresence EX90': ''}
    try:
        newPhoneLoad = dict[type]
        return newPhoneLoad
    except KeyError:
        print("Phone Load Missing for phone type " + type)
        logfile.write("Phone Load Missing for phone type " + type +"\n")
        return ''


def softkeyTemplateLookup(template):
    dict = {
        'Hunt Group LogIN standard': 'Avera Standard HLOG',
        'Standard Feature-ICU': 'Avera Standard ICU',
        'UCCX Agent User': 'Avera Standard Agent'}
    try:
        newTemplate = dict[template]
        return newTemplate
    except KeyError:
        if template == '':
            return ''
        else:
            # print "Soft-Key Template missing: " + template + ", Reset to Blank"
            return ''


def devsecpro(type):
    dict = {
        'Analog Phone': 'Analog Phone - Standard SCCP Non-Secure Profile',
        'Cisco 7937': 'Cisco 7937 - Standard SCCP Non-Secure Profile',
        'Cisco 7940': 'Cisco 7940 - Standard SCCP Non-Secure Profile',
        'Cisco 7960': 'Cisco 7960 - Standard SCCP Non-Secure Profile',
        'Cisco ATA 186': 'Cisco ATA 186 - Standard SCCP Non-Secure Profile',
        'Cisco 7912': 'Cisco 7912 - Standard SCCP Non-Secure Profile',
        'Cisco VGC Phone': 'Cisco VGC Phone - Standard SCCP Non-Secure Profile',
        }
    try:
        securityprofile = dict[type]
        return securityprofile
    except:
        securityprofile = 'Universal Non-Secure'
        return securityprofile


def mohLookup(sourceid):
    dict = {'0': '',
            '1': '3',  # McKennan Music on Hold to MCK-MusicOnHold
            '2': '',  # 04_Still_In_Saigon to ?????????????
            '3': '',  # 01_Isla_del_Sol to ????????????
            '4': ''}  # NCH Music On Hold to ?????????
    try:
        newsourceid = dict[sourceid]
        return newsourceid
    except KeyError:
        print("MOH source id not found " + sourceid)
        logfile.write("MOH source id not found " + sourceid +"\n")
        return sourceid


def linegroupmod(inputfile):
# --------------------------------Opens DN List-------------------------------- #
    with open("DN105Export.csv", newline='') as d:  # changed from DNExport.csv
        dnlist = []
        DN105Export = d.read().splitlines()
        for entry in DN105Export:
            e164 = entry[:13]
            dnlist.append(e164)
            # print e164
        # print dnlist

# --------------------------------Open Input and Create Reader-------------------------------- #
    f = open(inputfile, 'rb', newline='')  # opens the input file (typically linegroup.csv)
    reader = csv.reader(f)  # creates the reader object

# --------------------------------Open Output and Create Writer-------------------------------- #
    outputfile = open('LineGroupMod-output.csv', 'wb', newline='') # Specifies the output file
    a = csv.writer(outputfile)

# --------------------------------Prepare file to compare-------------------------------- #
    rownum = 0
    for row in reader:  # iterates the rows of linegroup.csv
            if rownum == 0:
                sourceheader = row
                header = row
                dnidx = []
                partidx = []
                ###### Line specific
                for linenum in range(1, 50):
                    try:
                        dnidx.append(header.index('DN OR PATTERN ' + str(linenum)))
                        partidx.append(header.index('ROUTE PARTITION ' + str(linenum)))
                    except ValueError:
                        break
                a.writerow(header)
            else:
                colnum = 0
                linegroup = []
                for col in row:
                    if colnum in dnidx:
                        col = modDNwDP(col)
                    elif colnum in partidx:
                        if row[colnum - 1]: # Checks to see if there's a DN
                            col = "On Cluster"
                    linegroup.append(col) # Adds DN and On Cluster to linegroup list
                    colnum += 1
# ------------------See if dn(from DNlist is in the particular line group and if so save that line------------------ #
                #print linegroup
                for newdn in dnlist:
                    #print "\\"+newdn, "in dnlist?"
                    if newdn in linegroup:
                        print("DN found in line group: "+newdn)
                        logfile.write("DN found in line group: "+newdn +"\n")
                        a.writerow(linegroup) # Adds to the CSV all of the DNs found in the current row
                        break
            rownum += 1


def modexternalnumbermask(mask):
    # Add + if mask begins with 1 + 10 digits
    searchObj = re.search(r'^(1\d{10})$', mask, re.M | re.I)
    if searchObj:
            newmask = "+" + searchObj.group(1)
            print("Matched 11 digits starting with 1, mask will be: " + newmask)
            logfile.write("Matched 11 digits starting with 1, mask will be: " + newmask +"\n")
            return newmask
    # Add + if mask is 10 digits
    searchObj = re.search(r'^(\d{10})$', mask, re.M | re.I)
    if searchObj:
            newmask = "+1" + searchObj.group(1)
            # print "Matched 10 digits, mask will be: " + newmask
            return newmask
    else:
        # print "External Phone Mask Unmodified as " + mask
        return mask



f = open(os.path.join(inputdir, sys.argv[1]), 'rt', newline='')  # opens the csv file
# f = open('MEL-FINAL-EXPORT.txt','rt', newline='') # Enable to choose file instead of providing as an arg. Might have to see how this would impact other arg positions
try:
    #alldnlist = list()
    #alldevices = list()
    #interestingdevices = list()
    #interestingdns = list()
    #dncounts = dict()
    #alldevicesoutput = open('alldevicesoutput.txt', 'wb', newline='')
    #interestingdevicesoutput = open('interestingdevicesoutput.txt', 'wb', newline='')
    #interestingdnsoutput = open('interestingdnsoutput.txt', 'wb', newline='')
    dummymac = int(datestring + '0000')
    reader = csv.reader(f)  # creates the reader object from the CSV module using "f" which is the all phones all details export
    rownum = 0
    outputfile = open(os.path.join(outputdir,'batmigrator-output.csv'), 'w', newline='')
    a = csv.writer(outputfile)
    userfile = open(os.path.join(outputdir,'userassociation.csv'), 'w', newline='')
    b = csv.writer(userfile)
    # Create file and first row header format for files that will be used to update DNs and create route patterns
    dnfile = open(os.path.join(outputdir,'DN105Export.csv'), 'w', newline='')
    c = csv.writer(dnfile)
    dn105header = []
    dn105header.append('DN\tStagingPartition\tPartition')
    c.writerows([dn105header])
    dn86file = open(os.path.join(outputdir,'DN86Export.csv'), 'w', newline='')
    d = csv.writer(dn86file)
    dn86header = []
    dn86header.append('DN\tPartition\tNew Partition')
    d.writerows([dn86header])
    rp86file = open(os.path.join(outputdir,'RP86Import.tsv'), 'w', newline='')
    rp86file.write("Route Pattern\tPartition\tDescription\tDial Plan Name\tRoute Filter\tRoute List\tRoute or Block\tProvide Dial Tone\tUse Calling Party's Ext Mask\tDiscard Digit Instructions\tCalled Party Prefix Digits\tCalling Party Prefix Digits\tCalling Party Transform Mask\tRelease Cause\n")
    mac86file = open(os.path.join(outputdir,'MACUpdate86.xml'), 'w', newline='')  # Create and open file to utilize raw axl to change MACs
    mac105file = open(os.path.join(outputdir,'MACUpdate105.xml'), 'w', newline='')  # Create and open file to utilize raw axl to change MACs. Not a CSV file, so no need to also open with csv.writer
    macmapfile = open(os.path.join(outputdir,'MAC-Map.csv'), 'w', newline='')  # Create and open file to use as a reference to map real vs dummy MACs. Not a CSV file, so no need to also open with csv.writer
    shortexportfile = open(os.path.join(outputdir,'shortexport.csv'), 'w', newline='')  # CONFIRM USE, REMOVE IF NO LONGER IN USE
    cpfile = open(os.path.join(outputdir,'CPExport.csv'), 'w', newline='')
    shortexport = csv.writer(shortexportfile)  # CONFIRM USE, REMOVE IF NO LONGER IN USE
    cp = csv.writer(cpfile)
    # Begin processing all phones all details export
    for row in reader:  # iterates the rows of the file in order and builds a list of row positions for each
        if rownum == 0:  # Determines if we're dealing with the header row
            sourceheader = row  # Used by linegroupmod function, determine if needed/why we can't use header below
            header = row
            # Initilize and clear lists that will be used to determine the index location in the list of. DO WE NEED THESE???
            dnidx = []
            partidx = []
            vmpidx = []
            linecssidx = []
            linedescriptionidx = []
            lineaargroupidx = []
            fwdallcssidx = []
            fwdall2ndcssidx = []
            fwdalldestidx = []
            fwdcss1idx = []
            fwdcss2idx = []
            fwdcss3idx = []
            fwdcss4idx = []
            fwdcss5idx = []
            fwdcss6idx = []
            fwdcss7idx = []
            fwdcss8idx = []
            fwdcss9idx = []
            linetextlabelidx=[]
            asciialertnameidx = []
            asciidisplaynameidx = []
            asciiltlidx = []
            mohidx = []
            removeidx = []
            softkeyidx = []
            useridx = []
            subscribesvcasciiidx = []
            serviceurlidx = []
            blflabelasciiidx = []
            blfdestidx = []
            reroutingcssidx = []
            callpickupidx = []
            sipprofileidx = []
            dnexport = []
            dn86export = []
            mac105update = []
            mac86update = []
            cpexport = []
            externalmaskidx = []
            # Start population of device specefic header index lists
            devicenameidx = header.index('Device Name')
            buttontemplateidx = header.index('Phone Button Template')
            devicecssidx = header.index('CSS')
            devicedescidx = header.index('Description')
            deviceaarcssidx = header.index('AAR CSS')
            locationidx = header.index('Location')
            cssrerouteidx = header.index('CSS Reroute')
            subscribecssidx = header.index('Device Subscribe CSS')
            devicetypeidx = header.index('Device Type')
            deviceaargroupidx = header.index('AAR Group')
            devicepoolidx = header.index('Device Pool')
            phoneloadidx = header.index('Phone Load Name')
            mohidx.append(header.index('User Hold MOH Audio Source'))
            mohidx.append(header.index('Network Hold MOH Audio Source'))
            presencegroupidx = header.index('Device Presence Group')
            devicesecurityidx = header.index('Device Security Profile')
            commonphoneprofileidx = header.index('Common Phone Profile')
            networklocaleidx = header.index('Network Locale')
            userlocaleidx = header.index('Device User Locale')
            commondevicecfgidx = header.index('Common Device Configuration')
            softkeyidx = header.index('Softkey Template')
            reroutingcssidx = header.index('CSS Reroute')
            sipprofileidx = header.index('SIP Profile')
            mlppindicationidx = header.index('MLPP Indication')
            mlpppreemptionidx = header.index('MLPP Preemption')
            dndoptionidx = header.index('DND Option')
            ringsettingphoneactive1idx = header.index('Ring Setting (Phone Active) 1')
            # Start population of line specific header index lists
            for linenum in range(1, 50):
                try:
                    dnidx.append(header.index('Directory Number ' + str(linenum)))
                    partidx.append(header.index('Route Partition ' + str(linenum)))
                    vmpidx.append(header.index('Voice Mail Profile ' + str(linenum)))
                    linecssidx.append(header.index('Line CSS ' + str(linenum)))
                    linedescriptionidx.append(header.index('Line Description ' + str(linenum)))
                    lineaargroupidx.append(header.index('AAR Group(Line) ' + str(linenum)))
                    asciialertnameidx.append(header.index('ASCII Alerting Name ' + str(linenum)))
                    asciidisplaynameidx.append(header.index('ASCII Display ' + str(linenum)))
                    asciiltlidx.append(header.index('ASCII Display ' + str(linenum)))
                    callpickupidx.append(header.index('Call Pickup Group ' + str(linenum)))
                    fwdallcssidx.append(header.index('Forward All CSS ' + str(linenum)))
                    fwdall2ndcssidx.append(header.index('Secondary CSS for Forward All ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward All Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward Busy Internal Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward Busy External Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward No Answer Internal Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward No Answer External Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward No Coverage Internal Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward No Coverage External Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward on CTI Failure Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward Unregistered Internal Destination ' + str(linenum)))
                    fwdalldestidx.append(header.index('Forward Unregistered External Destination ' + str(linenum)))
                    fwdcss1idx.append(header.index('Forward Busy Internal CSS ' + str(linenum)))
                    fwdcss2idx.append(header.index('Forward Busy External CSS ' + str(linenum)))
                    fwdcss3idx.append(header.index('Forward No Answer Internal CSS ' + str(linenum)))
                    fwdcss4idx.append(header.index('Forward No Answer External CSS ' + str(linenum)))
                    fwdcss5idx.append(header.index('Forward No Coverage Internal CSS ' + str(linenum)))
                    fwdcss6idx.append(header.index('Forward No Coverage External CSS ' + str(linenum)))
                    fwdcss7idx.append(header.index('Forward on CTI Failure CSS ' + str(linenum)))
                    fwdcss8idx.append(header.index('Forward Unregistered Internal CSS ' + str(linenum)))
                    fwdcss9idx.append(header.index('Forward Unregistered External CSS ' + str(linenum)))
                    linetextlabelidx.append(header.index('Line Text Label ' + str(linenum)))
                    mohidx.append(header.index('Line User Hold MOH Audio Source ' + str(linenum)))
                    mohidx.append(header.index('Line Network Hold MOH Audio Source ' + str(linenum)))
                    removeidx.append(header.index('ASCII Line Text Label ' + str(linenum))) # Uncommented for Avera ASM
                    externalmaskidx.append(header.index('External Phone Number Mask ' + str(linenum)))
                except ValueError:
                    break
            for sdnum in range(1, 200):  # Changed to 200 from 99
                try:
                    fwdalldestidx.append(header.index('Speed Dial Number ' + str(sdnum)))
                    removeidx.append(header.index('Speed Dial Label ASCII ' + str(sdnum)))
                    # If you attempt to remove and there is no field such as above it will hit the except and
                    # break out of this condition and skip any remaining SDs you are trying to run it against
                except ValueError:
                    break
            for usernum in range(1, 10):
                try:
                    useridx.append(header.index('User ID ' + str(usernum)))
                except ValueError:
                    break    
            for servicenum in range(1, 3):
                try:
                    removeidx.append(header.index('Subscribed Service Name ASCII ' + str(servicenum)))
                    removeidx.append(header.index('SURL Label ASCII ' + str(servicenum)))
                except ValueError:
                    break
            for value in range(1, 4):
                try:
                    removeidx.append(header.index('BLF Directed Call Park Label ASCII ' + str(value)))
                except ValueError:
                    break
            for blfnum in range(1, 200):  # Changed to 200 from 50
                try:
                    blfdestidx.append(header.index('Busy Lamp Field Destination ' + str(blfnum)))
                    removeidx.append(header.index('Busy Lamp Field Label ASCII ' + str(blfnum)))
                except ValueError:
                    break
            for intercomnum in range(1, 10):
                try:
                    removeidx.append(header.index('Intercom ASCII Line Text Label ' + str(intercomnum)))
                except ValueError:
                    break
# -----------------------------------------------HEADER ROW REMOVALS------------------------------------------------ #
            # Below are differences for 86->91 for 7941 phone
            header.append('Caller ID Calling Party Transformation CSS')
            header.append('Caller ID Use Device Pool Calling Party Transformation CSS')
            header.append('Remote Number Calling party Transformation CSS')
            header.append('Remote Number Use Device Pool Calling Party Transformation CSS')
            header.append('Allow iX Applicable Media')
            header.append('Require off-premise location')
            header.append('URI 1 on Directory Number 1')
            header.append('URI 1 Route Partition on Directory Number 1')
            header.append('URI 1 Is Primary on Directory Number 1')
            header.append('URI 2 on Directory Number 1')
            header.append('URI 2 Route Partition on Directory Number 1')
            header.append('URI 2 Is Primary on Directory Number 1')
            header.append('URI 3 on Directory Number 1')
            header.append('URI 3 Route Partition on Directory Number 1')
            header.append('URI 3 Is Primary on Directory Number 1')
            header.append('URI 4 on Directory Number 1')
            header.append('URI 4 Route Partition on Directory Number 1')
            header.append('URI 4 Is Primary on Directory Number 1')
            header.append('URI 5 on Directory Number 1')
            header.append('URI 5 Route Partition on Directory Number 1')
            header.append('URI 5 Is Primary on Directory Number 1')
            header.append('Reject Anonymous Calls 1')
            header.append('Third-party Registration Required')
            header.append('Block Incoming Calls while Roaming')
            header.append('Home Network ID')
            # Device Column Removals
            removeidx.append(header.index('Calling Party Transformation CSS'))
            removeidx.append(header.index('Mobile Smart Client Profile'))
            header.remove('Calling Party Transformation CSS')
            header.remove('Mobile Smart Client Profile')
            # Line Column Removals
            for linenum in range(1, 50):
                try:
                    header.remove('ASCII Line Text Label ' + str(linenum))
                except ValueError:
                    break
            for intercomnum in range(1, 10):
                try:
                    header.remove('Intercom ASCII Line Text Label ' + str(intercomnum))
                except ValueError:
                    break
            # Speed Dial Column Removals
            for sdnum in range(1, 200):  # Changed to 200 from 99
                try:
                    header.remove('Speed Dial Label ASCII ' + str(sdnum))
                except ValueError:
                    break
            # Service URL Removals
            for servicenum in range(1, 3):
                try:
                    header.remove('Subscribed Service Name ASCII ' + str(servicenum))
                    header.remove('SURL Label ASCII ' + str(servicenum))
                except ValueError:
                    break
            # BLF Removals
            for blfnum in range(1, 200):
                try:
                    header.remove('Busy Lamp Field Label ASCII ' + str(blfnum))
                except ValueError:
                    break
            for value in range(1, 4):
                try:
                    header.remove('BLF Directed Call Park Label ASCII ' + str(value))
                except ValueError:
                    break
            # print(header)
            # stop = input("STOP")
            a.writerows([header])
# ----------------------------------------------DATA ROW MODIFICATIONS---------------------------------------------- #
        else:
            # print("The first item in the DN Index is :", dnidx[0])
            colnum = 0
            phone = []
            user = []
            for col in row:
                if colnum == 0:
                    shortexportrow = list()  # CONFIRM USE, REMOVE IF NO LONGER IN USE
                    #alldevices.append(col)
                    tempdevicename = col
                    if MatchType == 'mac':
                        newSiteCode = modSiteFromMAC(row[devicenameidx])
                    elif MatchType == 'ip':
                        newSiteCode = modSiteFromIP(row[devicenameidx])
                    elif MatchType == 'dp':
                        dp = row[colnum + 2]
                        newSiteCode = modSiteFromDP(dp)
                    else:
                        break
                    if newSiteCode == "NotToBeMigrated":
                        # if device name is not in the checkdevice file and the checkdevice list is not empty
                        #shortexportrow.append(tempdevicename)  # Adds device name CONFIRM USE, REMOVE IF NO LONGER IN USE
                        #for item in dnidx:
                        #    shortexportrow.append(row[item])  # Adds DNs of that device name CONFIRM USE, REMOVE IF NO LONGER IN USE
                        #shortexport.writerow(shortexportrow)  # Export of Devicenames with DNs that will not be migrated CONFIRM USE, REMOVE IF NO LONGER IN USE
                        break
                    else:
                        #newSiteCode = col
                        newRegionCode = newSiteCode[0:3]
                        #col = row[devicenameidx]
                        if str(col).startswith('SEP'):  # if the Device name starts with SEP
                            dummymac += 1
                            mod86macupdate(col)
                            mod105macupdate(col)
                            #interestingdevices.append(col)
                            col = 'SEP' + str(dummymac)
                        phone.append(col)
                elif colnum not in removeidx:
                    if colnum == header.index('Device Pool'):  # Device Pool Name
                        col = modDevicePool(newRegionCode, row[devicenameidx])
                    if colnum == devicedescidx:  # Device Description
                        newDN = modDNwDP(row[dnidx[0]])
                        col = modDeviceDesc(col, newDN)
                    elif colnum == header.index('XML'):  # XML
                        col = modXML(row[devicetypeidx], col)
                    elif colnum == header.index('Softkey Template'):  # Softkey Name
                        col = modsoftkeytemplate(col)
                    elif colnum == header.index('Phone Button Template'):  # Map Phone Button Template to IB Standard Naming convention - Uses phonebuttontemplate.csv for dictionary,
                        col = modbuttontemplate(col)
                    elif colnum == header.index('Location'):  # Location Name
                        #col = modlocation(col, row[devicepoolidx]) # Old method but the data is not accurate, Use newSiteCode instead
                        col = newSiteCode
                    elif colnum == header.index('CSS'):  # Blank out Dev CSS
                        col = ""
                    elif colnum == header.index('AAR Group'):  # Blank out AAR Group
                        col = ""
                    elif colnum == header.index('AAR CSS'):  # Blank out AAR CSS
                        col = ""
                    elif colnum == header.index('Device Presence Group'):  # Set Device Presence Group to Standard
                        col = "Standard Presence group"
                    elif colnum == header.index('Device Security Profile'):  # Set Device use Universal Security Profile
                        col = devsecpro(row[devicetypeidx])
                        #col = "Universal Non-Secure"
                    elif colnum == header.index('Media Resource Group List'):  # Blank out MRGL
                        col = ""
                    elif colnum == header.index('Common Phone Profile'):  # Set to Standard
                        col = "Standard"
                    elif colnum == subscribecssidx:
                        col = "System Internal"
                    elif colnum == networklocaleidx:
                        col = "United States"
                    elif colnum == sipprofileidx:
                        col = "Standard Endpoint"
                    elif colnum == userlocaleidx:
                        col = "English United States"
                    elif colnum == header.index('Common Device Configuration'):  # Set Common Device Cfg to US User Endpoint by Default
                        col = newRegionCode + " User Endpoint"
                    elif colnum == mlppindicationidx:
                        col = "Default" # Set MLPP Indication to Default
                    elif colnum == mlpppreemptionidx:
                        col = "Default" # Set MLPP Preemption to Default
                    elif colnum == dndoptionidx:
                        col = "Ringer Off"  # Set DND Option to Ringer Off
                    elif colnum == ringsettingphoneactive1idx:
                        col = "Use System Default"  # Sets Ring Setting (Phone Active) 1
                    elif colnum == phoneloadidx:
                        col = modPhoneLoad(row[devicetypeidx])
                    elif colnum in dnidx:  # Directory Number
                        oldPT = row[colnum + 1]
                        dn86 = mod86dnexport(col,oldPT)
                        dn86export = []
                        #modinterestingdn(col)
                        if col:
                            col = modDNwDP(col)
                            moddnexport(col)
                            dnexport = []
                    elif colnum in linedescriptionidx:  # Line Descriptions
                        dn = row[colnum - 45]
                        col = modDNDescription(dn, col, newSiteCode)
                    elif colnum in partidx:  # Partition
                        col = modpartition(col)
                    elif colnum in vmpidx:  # voicemail profile - Set to Blank
                        if row[colnum - 2]:
                            col = "UCXN"
                    elif colnum in mohidx:  # moh mod index
                        col = modmoh(col)
                    elif colnum in useridx:  # Export User and Device Name to UserAssociation.txt
                        if col != '':
                            col = moduserassociation(col,row[devicenameidx])
                    elif colnum in linecssidx:  # Line CSS - Update to Device CSS
                        if row[colnum - 3]:  # As long as the DN is NOT blank
                            if col:
                                col = modCSS(col)
                            else:
                                col = modCSS(row[devicecssidx])
                    elif colnum == reroutingcssidx:  # ReReouting CSS to match DN 1 CSS or Device CSS
                        if row[dnidx[0]]:  # As long as the DN is NOT blank
                            if col:
                                col = modCSS(col)
                            else:
                                col = modCSS(row[devicecssidx])
                    elif colnum in lineaargroupidx:  # remove AAR Group Line info
                        col = ""
                    elif colnum in callpickupidx:  # Convert the Call Pickup Group name
                        col = modCallPickup(col)
                    elif colnum in fwdalldestidx:  # FWD All Destination modification
                        if col != "":
                            col = modcfwdest(col, newSiteCode)
                            if col[0:1] == "\\":    # if string begins with \
                                col = col[1:]       # replace with everything except the first character
                    elif colnum in blfdestidx:  # BLF Destination modification
                        if col:
                            col = modcfwdest(col, newSiteCode)
                            if col[0:1] == "\\":
                                col = col[1:]
                    elif colnum in fwdallcssidx:  # FWD All CSS
                        if row[colnum - 10]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdall2ndcssidx:  # FWD All CSS
                        col = ""
                    elif colnum in fwdcss1idx:  # FWD CSS
                        if row[colnum - 13]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss2idx:  # FWD CSS
                        if row[colnum - 16]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss3idx:  # FWD CSS
                        if row[colnum - 19]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss4idx:  # FWD CSS
                        if row[colnum - 22]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss5idx:  # FWD CSS
                        if row[colnum - 25]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss6idx:  # FWD CSS
                        if row[colnum - 28]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss7idx:  # FWD CSS
                        if row[colnum - 52]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss8idx:  # FWD CSS
                        if row[colnum - 60]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in fwdcss9idx:  # FWD CSS
                        if row[colnum - 63]:
                            col = "DN " + newSiteCode + " LD"
                    elif colnum in asciialertnameidx:  # Update ASCII Alert to match Alert
                        col = row[colnum - 1]
                    elif colnum in asciidisplaynameidx:  # Update ASCII Display to match Display
                        col = row[colnum - 1]
                    elif colnum in linetextlabelidx:  # Clear the Line text Label - Blank LTL will default to DN
                        col = ""
                    elif colnum in externalmaskidx:
                        col = modexternalnumbermask(col)
                    phone.append(col)
                colnum += 1
            if phone:
                phone.append('')  # 'Caller ID Calling Party Transformation CSS'
                phone.append('t')  # 'Caller ID Use Device Pool Calling Party Transformation CSS'
                phone.append('')  # 'Remote Number Calling party Transformation CSS'
                phone.append('t')  # 'Remote Number Use Device Pool Calling Party Transformation CSS'
                phone.append('f')  # 'Allow iX Applicable Media'
                phone.append('f')  # 'Require off-premise location'
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('')  #
                phone.append('f')  # 'Reject Anonymous Calls 1'
                phone.append('')  # 'Third-party Registration Required'
                phone.append('')  # 'Block Incoming Calls while Roaming'
                phone.append('')  # 'Home Network ID'
                a.writerows([phone])
        newSiteCode = ""
        rownum += 1

finally:
    #for item in interestingdns:
     #   interestingdnsoutput.write("%s\n" % item)
    #for item in interestingdevices:
     #   interestingdevicesoutput.write("%s\n" % item)
    #for item in alldevices:
     #   alldevicesoutput.write("%s\n" % item)
    f.close()  # closing
    logfile.close()  # closing
    # outputfile.close()
    # userfile.close()
    # dnfile.close()


print("Closing Files")
print(".")
print("..")
print("...")
print("....")
print("")
print("")
print("Your Phone Export is complete")
print("")
print("")
