import re


TheApp_pattern = re.compile('^(the|this|our)?\s?app(lication)?')



Server_pattern = re.compile('^(our|their)?\s?server(s)?')
Third_pattern = re.compile('(third|3rd)(-|\s)(part|countr)(y|ies)')


ForPurpose_pattern = re.compile('^(used\s)?(for\s)?(the\s)?(special|commercial|(generic\s)?marketing|analytical|technical|advertising|research|any other|(product\s)?development)?\s?purpose(s)?$')
Continue_pattern = re.compile('continue\sto\s[a-z0-9\s]*')
WorkProperly_pattern = re.compile('(work|function|use)[a-z0-9\s]*properly')

def init():
    global Vague_Purpose,Vague_Identity,Vague_Receiver,Vague_Purpose_Notice_Count,Vague_Identity_Notice_Count,Vague_Receiver_Notice_Count
    Vague_Identity_Notice_Count = 0
    Vague_Identity = {"We":0,"The App":0,"Partner and Vendor":0}
    Vague_Receiver_Notice_Count = 0
    Vague_Receiver = {"Server":0,"Third Party and country":0,"Partner and Vendor":0}
    Vague_Purpose_Notice_Count = 0
    Vague_Purpose = {"ForPurpose":0,"Continue":0,"WorkProperly":0}


def classify_Identity(label_list):
    global Vague_Identity_Notice_Count
    noticeLevel = False
    for Identity_label in label_list:
        Identity_label = Identity_label.lower()
        if Identity_label=="we" or Identity_label=="us":
            Vague_Identity["We"]+=1
            noticeLevel = True
        elif "partner" in Identity_label or "vendor" in Identity_label:
            Vague_Identity["Partner and Vendor"]+=1
            noticeLevel = True
        elif TheApp_pattern.search(Identity_label) is not None:
            Vague_Identity["The App"]+=1
            noticeLevel = True

    if(noticeLevel): Vague_Identity_Notice_Count +=1
    return noticeLevel


def classify_Receiver(label_list):
    global Vague_Receiver_Notice_Count
    noticeLevel = False
    for Receiver_label in label_list:
        Receiver_label = Receiver_label.lower()
        if Server_pattern.search(Receiver_label) is not None:
            Vague_Receiver["Server"]+=1
            noticeLevel = True
        elif Third_pattern.search(Receiver_label) is not None:
            Vague_Receiver["Third Party and country"]+=1
            noticeLevel = True
        elif "partner" in Receiver_label or "vendor" in Receiver_label:
            Vague_Receiver["Partner and Vendor"]+=1
            noticeLevel = True
    
    if(noticeLevel): Vague_Receiver_Notice_Count +=1
    return noticeLevel

def classify_Purpose(label_list):
    global Vague_Purpose_Notice_Count
    noticeLevel = False

    for Purpose_label in label_list:
        Purpose_label = Purpose_label.lower()
        if ForPurpose_pattern.search(Purpose_label) is not None:
            Vague_Purpose["ForPurpose"]+=1
            noticeLevel = True
        elif Continue_pattern.search(Purpose_label) is not None:
            Vague_Purpose["Continue"]+=1
            noticeLevel = True
        elif WorkProperly_pattern.search(Purpose_label) is not None:
            Vague_Purpose["WorkProperly"]+=1
            noticeLevel = True

    if(noticeLevel): Vague_Purpose_Notice_Count +=1
    return noticeLevel
