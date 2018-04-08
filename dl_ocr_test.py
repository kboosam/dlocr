# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 15:24:56 2018

@author: kboosam
"""
'''
@@ API TO CAPTURE THE DRIVING LICENSE DETAILS FROM GOOGLE VISION API

'''
# Importing libraries

#import pandas as pd
#from flask import Flask, jsonify, request
import logging
#from flask_cors import CORS
#import numpy as np
from raven.contrib.flask import Sentry ## Sentry logging 
import  json
import http.client

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types
import io, re



# function to build the response from this API with ChatFuel widgets

def build_resp(recallAPI_resp):
    
    try:
        recalls = recallAPI_resp["Results"]  ## Get all results ##
              
        if recallAPI_resp["Count"] > 0:
            # post a simple text about the number of recalls identified - UNUSED BELOW
            #resp_txt = resp_txt + "{ \"text\": \"We found total "+ str(recallAPI_resp["Count"]) + " recalls for your vehicle. Please contact your deals or service agent for more details.\"},"
            
            
            # initialize gallrey list and dictionary for each gallery item.
            gallery_roll = []
            gallery = dict.fromkeys(['title','image_url', 'suntitle','buttons'])
            for recall in recalls:
                 
                 gallery = {
                                "title" : str(recall['Component'])[:30], 
                                "image_url": "https://chryslercapital.files.wordpress.com/2015/09/090115-cc-what-do-i-do-if-my-vehicle-is-recalled-2.jpg?w=80&h=60&ver=3.76.9",
                                "subtitle": str(recall['Conequence'])[:50],
                                "buttons":[
                                            {
                                                "type":"web_url",
                                                "url" : "https://www.nhtsa.gov/vehicle/"+ recall['ModelYear'] + "/"+ recall['Make'] + "/"+ recall['Model'] , 
                                                "title":"View Recalls"                                    
                                            }
                                        ]
                            }
                    
                 gallery_roll.append(gallery)
            # END OF FOR LOOP TO BUILD GALLERY
            
            # build the Full response dictionary        
            resp_dict = {
                        "messages": [
                                     { "text": "We found total " + str(recallAPI_resp["Count"]) + " recalls for your vehicle. Please contact your dealer or service agent for more details." 
                                     },
                                      
                                                                             
                                      { 
                                          "attachment" : {
                                          
                                              "type": "template",
                                              "payload": {
                                                          "template_type":"list",
                                                          "top_element_style": "compact",
                                                          "elements": gallery_roll
                                                       }
                                          }
                                     }
                                    ]
                        }
               
        else:
            #resp_txt = resp_txt + "{ \"text\": \"There are no recalls reported for your vehicle at this point.Please contact your dealer or service agent for any further questions.\"} ] }"
            resp_dict = {
                        "messages": [
                                      {
                                       "text": "Happy to inform you that, there are no active recalls reported for your vehicle at this time."                                       
                                      },
                                      { 
                                       "text": "However recommend to check with your dealer or service agent regularly." 
                                      }
                                    ]
                        }

    except Exception as e:
        print(e)
        sentry.captureMessage(message=e, level=logging.FATAL)
        resp_dict = {
                     "messages": [
                       {"text": "An error occured while fetching the recall details for your vehicle - 102."}
                      ]
                }
    
    return resp_dict;
##
## FUNCTION TO CALL GGOGLE VISION API WITH THE DL IMAGE 
##
def DL_OCR_VISION(path):
  
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()
    image = types.Image()
    image.source.image_uri = path
    
    '''
    # THIS IS FOR LOCAL FILE    
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    
    image = types.Image(content=content) 
    '''
    
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    ret_text = ''
    #if response.error==:
    print('Texts:', texts)
    for text in texts:
        ret_text += text.description
        #print(text , type(text))
        
    #ret_text.replace('\n',' ')  # replace new line charachters
    ret_text = ' '.join(ret_text.split())
    
    
    return ret_text  ## retunrs a string of all text from the driving license


####
### FUNCTION TO PARSE THE TEXTS returned from Vision API to a DL object
####
'''
DL OBject structure

{
     DLN : <drivers license number>,
     DLN_valid: <False / True>
     DOB : <bate of birth as str>,
     EXP_DT : <exp date as str>,
     address: {
     add_ln1: <line 1>,
     add_ln2: <line 2>,
     city: <city>,
     state: <state code>,
     zip: <zip 5 or 5+4>
     
     },
     verified: <False/True> "valid address or not"
}

'''

def parse_DL(full_text):
    
    #print('full text - ', full_text)
   
    if full_text.count('Texas') or full_text.count('TX') > 0 : state = 'TX'
        
    if full_text.count('Florida') > 0 : state='FL'
    
    if full_text.count('Illinois') > 0 : state = 'IL'
           
    if full_text.count('visitPA') > 0 : state='PA'
    
    if full_text.count('WISCONSIN') > 0 : state='WI'
    
    if full_text.count('CALIFORNIA') > 0 : state='CA'
    
    if full_text.count('ALABAMA') > 0 : state='AL'
    
    if state in ['TX', 'PA', 'IL', 'WI']: 
        full_text = full_text.replace(' 1 ',' ')  # replace FIELD LABELS
        full_text = full_text.replace(' 2 ',' ')  # replace FIELD LABELS
        full_text = full_text.replace(' 8 ',' ')  # replace FIELD LABELS
        full_text = full_text.replace('\n',' ')
    else:
        full_text = full_text.replace('\n',' ') 
    
    
     #### Call Smarty Streets API to find address from text
    try:
        conn = http.client.HTTPSConnection("us-extract.api.smartystreets.com")
        
        payload = full_text #send full text
    
        headers = {
            'content-type': "text/plain",
            'host': "us-extract.api.smartystreets.com",
            'cache-control': "no-cache"
            }
    
        conn.request("POST", "/?auth-id=eff0b523-c528-0292-6685-6ad2c5a6e92a&auth-token=V7pWleHG8yLUS8CC7NqQ", payload, headers)
        SSresp = conn.getresponse()
        print('Call to SmartyStreets successful')
    except Exception as e: 
        print('Error occured while calling the SmartyStreets API for address extraction')
        print(e)
        sentry.captureMessage(message=e, level=logging.FATAL) #printing all exceptions to the log
    
    
    SSresp = json.loads(SSresp.read())
    verified = SSresp['addresses'][0]['verified']  # address validity
    if not verified :  ## Checking if the address is valid
        postal_address = {
                         "add_ln1":SSresp['addresses'][0]['text']
                         }
        # when address is not valid we are just sending the identified address string in the line 1
        print('Address on DL is invalid:', SSresp['addresses'][0]['text'] )
    else:
        #extract the address object
        address = SSresp['addresses'][0]['api_output'][0]
        
        ## fomulate address
        postal_address = {
                     "add_ln1": address['delivery_line_1'],
                     "add_ln2": '',
                     "city": address['components']['city_name'],
                     "state": address['components']['state_abbreviation'],
                     "zip": address['components']['zipcode'] + '-' + address['components']['plus4_code']
                }
        
        state = address['components']['state_abbreviation']    # get state code for all other work.
     ### END OF IF ELSE STRUCTURE
        
    ## make a continuous string without spaces by concatenating all individual texts from google
    full_str  = ''.join(full_text.split())
    
    print('Address state is:', state)
    
    # get DL number for IL
    if state == 'IL':
        # IL DLN is 14 digits - X999-999-999
        DLN = re.search('\D\d{3}-\d{4}-\d{4}', full_str).group(0)
        
    # get DL number for TX
    if state == 'TX':
        DLN = re.search('\d{6}9', full_str).group(0)
    
    # get DL number for FL
    if state == 'FL':
        DLN = re.search('\D\d{3}-\d{3}-\d{2}-\d{3}-\d', full_str).group(0) # FL DLN is 17 digits
    
    # get DL number for PA
    if state == 'PA':
         DLN = re.search('DLN\:\d{8}', full_str).group(0)[4:] # PA DLN is 8 digits
    # get DL number for WI
    if state == 'WI':
        DLN =  re.search('\D\d{3}-\d{4}-\d{4}-\d{2}', full_str).group(0) # WI DLN is 14 digits
    
    # get DL number for CA
    if state == 'CA':
        DLN =  re.search('\D\d{7}', full_str).group(0) # WI DLN is 8 digits
   
    # get DL number for AL
    if state == 'AL':
        DLN =  re.search('No.\d{7}', full_str).group(0)[3:] # WI DLN is 7 digits
   
      
    #### GET DOB and EXPIRY DATE
    
    DATES = re.findall('(\\d{1,2}/\\d{1,2}/\\d{4})', full_str) #date separator by slashes
    if len(DATES) == 0: 
        dtformat = False
        DATES = re.findall('(\d{1,2}-\d{1,2}-\d{4})', full_str) # date separator as -
        if len(DATES) == 0: raise Exception('dates not found on drivers license')
    
    imp_DATES = []
    
    for t_date in DATES:
        if t_date not in imp_DATES:
            imp_DATES.append(t_date)
       
    ###
    ### TO CAPTURE Date of Birth and expiry date of the Driving license, SORT dates in scending order
    ### smallet date would be DOB and farthest date would be expiry date
    ###
    import datetime
    if dtformat : 
        imp_DATES = sorted(imp_DATES, key=lambda x: datetime.datetime.strptime(x, '%m/%d/%Y'))
        EXP_datetime = datetime.datetime.strptime(imp_DATES[-1], "%m/%d/%Y")
        DLN_valid = True if EXP_datetime > datetime.datetime.now() else False ## check if DL is still valid
    else:
        imp_DATES = sorted(imp_DATES, key=lambda x: datetime.datetime.strptime(x, '%m-%d-%Y'))
        EXP_datetime = datetime.datetime.strptime(imp_DATES[-1], "%m-%d-%Y")
        DLN_valid = True if EXP_datetime > datetime.datetime.now() else False ## Check if DL is not valid
        
    DOB = imp_DATES[0]
    EXP = imp_DATES[-1]
    
    ret_obj = { 
             "DLN": DLN,
             "DLN_valid": DLN_valid,
             "DL_State": state,
             "DOB": DOB,
             "EXP_DT": EXP,
             "address": postal_address,
             "verified":verified
            }
        # end of else - Verified address
    return ret_obj

##### END OF FUNCTION - build_resp
###################################################################

'''
app = Flask(__name__)
#set sentry for logging the messages
sentry = Sentry(app, dsn='https://e8ddaf32cc924aa295b846f4947a9332:5e52d48fe13a4d2c82babe6833c5f871@sentry.io/273115')
CORS(app) ## cross origin resource whitelisting..

## dl ocr api on flask
@app.route('/dlocr_api', methods=['POST','GET'])
def get_DL():

    """API Call
    Pandas dataframe (sent as a payload) from API Call
    """
    #print("\n\n Started processing the GET request..\n")
'''   
##################
#   REQUEST STRCUTRE
#   imgurl
#################       
'''
try: 
    #req = request.json
    img_path = request.args.get('imgurl', type= str)
    
    print("##This is the request:", request.args , '\n\n')        
        
    #img_path = "testvin2.jpg" # worked well but inserted a space in the VIN
    
    #print("##This is the request JSON:", str(request.get_json()), '\n\n')
    sentry.captureMessage(message='Started processing request- {}'.format(img_path), level=logging.INFO)
    
except Exception as e:
    print(e)
    sentry.captureMessage(message=e, level=logging.FATAL)
    resp = {
             "messages": [
               {"text": "An error occured while fetching the recall details for your vehicle - 102."},
              ]
            }
'''   
try:
    #img_path = "DL Tests\illinois-DL.jpg"
    #img_path = r'DL Tests\FL_DL.jpg'
    img_path = "http://www.northescambia.com/wp-content/uploads/2015/01/driverslicense.jpg" #Florida DL
    # Texas sample DL
    #img_path = "https://4.bp.blogspot.com/-xwv9SOZn-UI/VxY9JDsMViI/AAAAAAAABeY/LoEjWlL62P03JHAR8ubcm8XlBe0ct3MNwCLcB/s1600/jared%2Bcody%2Btexas%2BDL.jpg" 
    # Texas sample DL 2
    img_path = "https://static1.squarespace.com/static/50f9bacee4b0c2d1fa3d2c8d/t/56ac1e1fe32140027603a1e7/1454120484869/"
    #CAlifornia examples
    img_path = "http://www.usaidshop.com/images/img/CALIFORNIA.jpg"
    #Wisconsin example
    img_path = "http://media.graytvinc.com/images/New+ID+Card1.jpg"
    #alabama example
    img_path = "http://www.usaidshop.com/images/img/ALABAMA.jpg"
    
    # call google vision API
    DL_Text = DL_OCR_VISION(img_path)
    
    #parse to DL objects
    dlobj = parse_DL(DL_Text)
    #print ('Parsed Key Info:', json.loads(dlobj))
    
    #build response structure
    #resp = build_resp(dlobj)
    resp = dlobj
    #sentry.captureMessage(message='completed processing the DL OCR: {}'.format(dlobj['DLN']), level=logging.INFO)

except Exception as e:
    
    print(e)
    sentry.captureMessage(message=e, level=logging.FATAL) #printing all exceptions to the log
    resp = {
             "messages": [
               {"text": "An error occured while fetching the recall details for your vehicle - 103."},
              ]
            }
print ("--- Response -->", resp)    
#    return jsonify(resp)
#### END OF  function

