
import datetime
import email
import os
import imaplib
from time import sleep
from threading import Thread
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.message import EmailMessage
import re
import pdb
from decode_satellite_message import unpack_data, bpFormat
import uuid
#Fri May 24 15:51:32 2019
# Modified by FLB for oshen USV.



def decode_hex_message(hex_data):
    binary_data = bytes.fromhex(hex_data)
    unpacked_data = unpack_data(binary_data, bpFormat)
    return unpacked_data['Latitude'],unpacked_data['Longitude'],unpacked_data['Timestamp'],unpacked_data

class EmailSniffer():

    def __init__(self,
                 email_account,
                 username=None, pw=None,
                 check_rate_min=1,
                 imap_svr=None, imap_port=None,
                 smtp_svr=None, smtp_port=None,
                 imei=None,
                 arrival_email_filt=None,
                 attachment_ext_filt=None):
        self.IMEI = imei
        self.SENDER = arrival_email_filt
        #self.SENDER='RockBLOCK'
        self.FROM = email_account
        self.email_username = username
        self.email_pw = pw
        self.email_check_rate = check_rate_min
        self.email_incoming_svr = imap_svr
        self.email_outgoing_svr = smtp_svr
        self.email_incoming_port = imap_port
        self.email_outgoing_port = smtp_port
        self.attachment_ext_filt = attachment_ext_filt

        self.EMAILTEXT = "MOMSN: {0}\nMTMSN: 0\nTime of Session (UTC): {1}\nSession Status: 00 - Transfer OK\nMessage Size (bytes): {2}"
        self.momsn = 900000

        self.incoming_attachment_queues = []

        #self.last_read = datetime.datetime.now()
        self.last_read = datetime.datetime.utcnow()
        self.alive = True

        self._threadL = Thread(target=self._listen)
        self._threadL.setDaemon(True)
        self._threadL.start()

    


    def _listen(self):
        wmoid='5001000'
        icount=0
        print('Listen thread started')
        #
        # create header line string for csv file
        #
        hdrcsv_str='wsi_series,wsi_issuer,wsi_issue_number,wsi_local,uuid,year,month,day,hour,minute,latitude,longitude,'
        hdrcsv_str=hdrcsv_str+'speed,cog,wind,wdir,pres,airt,rh,sst\n'
        # test file to output data to
        #f=open('oshen_pos_test.txt','w')
        while self.alive:
            #icount=icount+1
            #if icount > 10:
            #    break
            try:
                # change hours back to what is appropriate for testing to read message if there are no new ones.
                date = (datetime.datetime.now() - datetime.timedelta(hours=400)).strftime("%d-%b-%Y")

                M = imaplib.IMAP4(self.email_incoming_svr)

                response, details = M.login(self.email_username, self.email_pw)
                M.select('INBOX/ignored')
                #M.select('INBOX')
                #pdb.set_trace()

                print('Checking INBOX/ignored')
                #Search for messages in the past hour with subject line specified and from sender specified
                #response, items = M.search(None,
                #                           '(UNSEEN SENTSINCE {date} HEADER Subject "{subject}" FROM "{sender}")'.format(
                #                               date=date,
                #                               subject=self.IMEI,
                #                               sender=self.SENDER
                #                           ))
                # note need to change back to UNSEEN for real code
                # for test use SEEN to look at messages that have already been read
                response, items = M.search(None,
                                           '(SEEN SENTSINCE {date} HEADER Subject "{subject}" FROM "{sender}")'.format(
                                               date=date,
                                               subject=self.IMEI,
                                               sender='RockBLOCK'
                                           ))
                #print(response)
                #print(items)
                #pdb.set_trace()
                # problem is data is multiple lines and has characters =\r\n inbetween parts of the message
                # this is a big issue.
                for emailid in items[0].split():
                    response, data = M.fetch(emailid, '(RFC822)')

                    mail = email.message_from_string((data[0][1]).decode('utf-8'))
                    #
                    
                    junk=data[0][1].decode('utf-8')
                    # This is the code to fix the multiple lines in the hex data message
                    atest=re.sub('=\r\n','',junk)
                    
                    hex_data_match = re.search(r'Data:\s*([0-9a-fA-F]+)', atest)
                    #hex_data_match = re.search(r'Data:\s*([0-9a-fA-F]+)', junk)
                    if hex_data_match:
                        # open file to write to
                        # need to define a file name for output
                        hex_data = hex_data_match.group(1)
                        # variables are:
                        # 'Average GPS Speed'
                        # 'Average Course Over Ground'
                        # 'Avg Wind Speed'
                        # 'Avg Wind Direction'
                        # 'Average Barometric Pressure'
                        # 'Average Air Temperature'
                        # 'Average Relative Humidity'
                        # 'Average Sea Surface Temperature 1'
                        # 'Average Sea Surface Temperature 2'
                        # example of how to get the actual values
                        # sst1=dataum['Average Sea Surface Temperature 1']
                        # sst2=dataum['Average Sea Surface Temperature 2']
                        decoded_lat, decoded_lon, decoded_time,dataum = decode_hex_message(hex_data)
                        latitude = decoded_lat
                        longitude = decoded_lon
                        timeformail = datetime.datetime.utcfromtimestamp(decoded_time)
                        syear=str(timeformail.year)
                        if timeformail.month < 10:
                            smon='0'+str(timeformail.month)
                        else:
                            smon=str(timeformail.month)
                        if timeformail.day < 10:
                            sday='0'+str(timeformail.day)
                        else:
                            sday=str(timeformail.day)
                        if timeformail.hour < 10:
                            shour='0'+str(timeformail.hour)
                        else:
                            shour=str(timeformail.hour)
                        if timeformail.minute < 10:
                            smin='0'+str(timeformail.minute)
                        else:
                            smin=str(timeformail.minute)
                        filename='oshen_'+syear+smon+sday+'T'+shour+smin+'.csv'
                        f=open(filename,'w') # filename has to be determined for how this code will work...
                        f.write(hdrcsv_str)
                        speed=dataum['Average GPS Speed']
                        speed=speed*0.5144
                        cog=dataum['Average Course Over Ground']
                        wdir=dataum['Avg Wind Direction']
                        wind=dataum['Avg Wind Speed']
                        wind=wind*0.5155
                        pres=dataum['Average Barometric Pressure']
                        pres=pres*100 # convert from mb to Pascals
                        airt=dataum['Average Air Temperature']
                        airt=airt+274.15 # convert from C to K
                        rh=dataum['Average Relative Humidity']
                        sst=dataum['Average Sea Surface Temperature 1']
                        sst=sst+274.15 # convert from C to K
                        myuuid=uuid.uuid4()
                        #pdb.set_trace()
                        f.write('0,22000,0,'+str(wmoid)+','+str(myuuid)+',')
                        f.write(syear+','+smon+','+sday+',')
                        f.write(shour+','+smin+','+str(latitude)+','+str(longitude)+',')
                        f.write(str(speed)+','+str(cog)+','+str(wind)+','+str(wdir)+',')
                        f.write(str(pres)+','+str(airt)+','+str(rh)+','+str(sst)+'\n')
                        f.close()
                        # So we can write all this out but to make sure the buffer is flushed you need to close the file.
                        # this is the code to send to ODSS
                        # commented out for now
                        #mymsg=EmailMessage()
                        #mymsg['Subject']='Emperor,'+str(decoded_time)+','+str(longitude)+','+str(latitude)
                        ##mymsg['Subject']='Emperor,'+str(timeformail)+','+str(longitude)+','+str(latitude)
                        #mymsg['From']='flbahr@mbari.org'
                        #mymsg['To']='flbahr@mbari.org'
                        ##mymsg['To']='auvtrack@mbari.org'
                        ##mymsgtxt='Emperor,'+str(timeformail)+','+str(longitude)+','+str(latitude)
                        #mymsgtxt='Emperor,'+str(decoded_time)+','+str(longitude)+','+str(latitude)
                        #mymsg.set_payload(mymsgtxt)
                        #stest=smtplib.SMTP('localhost')
                        #stest.send_message(mymsg)
                        #stest.quit()
                        cmd='csv2bufr data transform /home/flbahr/oshen/'+filename+' --bufr-template /home/flbahr/oshen/bufr_oshen_template.json --output-dir /home/flbahr/oshen/'
                        # os.system(cmd) # will this work?
                        pdb.set_trace()
                        # mail message to tracking database
                        # To: auvtrack@mbari.org
                        # From: usv_track
                        # Subject:Emporor,time,long,lat
                        # body Emporor,time,lon,lat
                    

                    if not mail.is_multipart():
                        x1=mail.get('Content-Disposition')
                        x2=mail.get_filename()
                        x3=mail.get_payload(decode=True)
                        continue
                    for part in mail.walk():
                        x1=part.get('Content-Disposition')
                        x2=part.get_filename()
                        x3=part.get_payload(decode=True)
                        
                        if part.is_multipart() and x2 is None:
                            continue
                        if x1 is None:
                            continue
                        #if part.get('Content-Disposition') is None:
                        #    continue
                        file_nm = part.get_filename()
                        if x2 is None:
                            continue
                        filename, fileext = os.path.splitext(file_nm)
                        msg=part.get_payload(decode=True)
                        if self.attachment_ext_filt is not None:
                            if fileext != self.attachment_ext_filt:
                                continue
                        msg = part.get_payload(decode=True)

                        sleep(1)
                        for q in self.incoming_attachment_queues:
                            q.put_nowait(msg)
                            sleep(5)

                        temp = M.store(emailid, '+FLAGS', '\\Seen')
                M.close()
                M.logout()
                sleep(self.email_check_rate * 60)
            except:
                # Could probably handle this better, but just so we don't kill the thread...
                print('Failed to access email')
                pass

    def write(self, msg):
        print('Writing e-mail')
        email_msg = MIMEMultipart()
        email_msg['Subject'] = "SBD Msg From Unit: " + "{0}".format(self.IMEI)
        email_msg['To'] = self.SENDER
        email_msg['From'] = self.FROM

       #part = MIMEText(self.EMAILTEXT.format(self.momsn, datetime.datetime.now().ctime(), len(msg)))
        part = MIMEText(self.EMAILTEXT.format(self.momsn, datetime.datetime.utcnow().ctime(), len(msg)))

        email_msg.attach(part)

        attachment = MIMEApplication(msg)

        attachment.add_header('Content-Disposition', 'attachment',
                              filename="{0}_{1}{2}".format(self.IMEI, self.momsn,
                                                            self.attachment_ext_filt))
        email_msg.attach(attachment)
        print('SMTP connect')
        print(self.email_outgoing_svr)
        print(self.email_outgoing_port)
        smtp = smtplib.SMTP('mbarimail.mbari.org', self.email_outgoing_port)
        #smtp = smtplib.SMTP('outbox.whoi.edu', self.email_outgoing_port)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(self.email_username, self.email_pw)
        print('SMTP send')
        smtp.sendmail(self.FROM, [email_msg['To'], self.FROM], email_msg.as_string())
        print('SMTP quit')
        smtp.quit()

        self.momsn = self.momsn + 1

    def close(self):
        self.alive = False

    def append_incoming_attachment_queue(self, queue_to_append):
        self.incoming_attachment_queues.append(queue_to_append)
