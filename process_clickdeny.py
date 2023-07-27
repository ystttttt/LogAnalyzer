import json,time,os
import re
from json import loads
from Model.preprocess import dataloader
from Model.model_bert import NERModel
from Model.NERReco import NERtest
import AnalysisConfig
from datetime import datetime

def match_privacykeywords(data):
    with open(AnalysisConfig.privacy_keyword_path, 'r', encoding='UTF-8')as json_file:
        load_dict = loads(json_file.read())
    key_list = set()
    add_flag = 0
    data = data.lower()
    for key, keywords in load_dict.items():
        for keyword in keywords:
            keyword = keyword.lower()
            if data.find(keyword) != -1:
                start = data.find(keyword)
                end = start + len(keyword)
                if start == 0:
                    if end>=len(data):
                        add_flag = 1
                    elif data[end]==' ':
                        add_flag = 1
                elif data[start-1]==' ':
                    if end>=len(data):
                        add_flag = 1
                    elif data[end]==' ':
                        add_flag = 1
        if add_flag:
            for al_key in key_list:
                if AnalysisConfig.Ontology.is_ancestor(al_key,key):
                    key_list.remove(al_key)
                    add_flag = 0
                    break
                elif AnalysisConfig.Ontology.is_ancestor(key,al_key):
                    add_flag = 0
                    break
        if add_flag:
            key_list.add(key)
            add_flag = 0
    return key_list

def check_ifgrantpermission(txt_file):
    with open(txt_file, 'r', encoding='utf-8') as f:
        txtlines = [line.strip().split("++++++++++")[0] for line in f.readlines() if line.strip()]
    long_sentence = " ".join(txtlines)
    allow_pattern = re.compile('Allow[a-zA-Z0-9-:\s]*to')
    if ("WHILE USING THE APP" in long_sentence and "ONLY THIS TIME" in long_sentence and "DENY" in long_sentence):
        return True
    if allow_pattern.search(long_sentence) is not None and "DENY" in long_sentence:
        return True

def check_timegap(key,timestamp):
    key_date = datetime.strptime(key,"%Y-%m-%d_%H%M%S")
    clickdeny_date = datetime.strptime(timestamp,"%Y-%m-%d_%H%M%S")
    delta = key_date - clickdeny_date
    if delta.seconds > 60:
        return False
    else:
        return True

def find_clickdeny_timastamp(input_dir,timestamp):
    '''
    find the timestamp of the latest screenshot before clicking deny,
    and the timestamp of the next three screenshots after clicking deny
    ''' 
    count = 0
    end_timestamp = "0"
    for root, _, files in os.walk(input_dir):
        files.sort()
        for file in files:
            if count >= 3:
                break
            if file.endswith('.jpg'):
                file_timestamp = file.replace("screen_","").replace(".jpg","")
                if file_timestamp >= timestamp:
                    count = count + 1
                    end_timestamp = file.replace(".jpg","").replace("screen_","")
                else:
                    start_file = os.path.join(root, file).replace(".jpg",".txt").replace("screen","state")
                    start_timestamp = file.replace(".jpg","").replace("screen_","")
    return start_timestamp,end_timestamp,start_file    

def get_datatype(start_file,temp_NER_inputpath,temp_NER_outputpath,model,NERconfig):
    '''
    use NER to identify data type on the click-deny page
    '''
    if not os.path.exists(start_file):
        print(start_file+" does not exist!!!!!")
        return set()
    with open(start_file, 'r', encoding='utf-8') as f:
        txtlines = [line.strip().split("++++++++++")[0] for line in f.readlines() if line.strip()]
    if os.path.exists(temp_NER_inputpath):
        os.remove(temp_NER_inputpath)        
    for txtline in txtlines:
        words = txtline.split()
        with open(temp_NER_inputpath, 'a', encoding='utf-8') as f:
            for word in words:
                f.write(word + "\n")
            f.write("\n")
    testloader = dataloader(dtype='NERclassifier', config=NERconfig, classifier_path = temp_NER_inputpath)
    testdata, testTexts, tokens = testloader.load_NERdata()
    NERtest(NERconfig, model, testdata, testTexts, tokens, output_path = temp_NER_outputpath)
    with open(temp_NER_outputpath, 'r', encoding='utf-8') as f:
        NERlines = [line.strip() for line in f.readlines() if line.strip()]
    privacykeywords = set()
    for NERline in NERlines:
        dict_line = loads(NERline)
        if dict_line["predict"].__contains__("data"):
            data_array = dict_line["predict"]["data"]
            for words in data_array:
                sentence = " ".join(words)
                key_list=match_privacykeywords(sentence)
                privacykeywords = privacykeywords.union(key_list)
    if len(privacykeywords) == 0:
        for txtline in txtlines:
            key_list=match_privacykeywords(txtline)
            privacykeywords = privacykeywords.union(key_list)   
    return  privacykeywords

def match_clickdeny(input_dir, data_output_path,model,NERconfig,clickdeny_final_path):
    '''
    On the next three pages after clicking deny, judge whether there is a notice of the same data type as the one on the click-deny page
    '''
    clickdeny_log = input_dir.replace("/states","/ourlogs")+"/"+input_dir.split("/")[-2]
    print("process", clickdeny_log)
    temp_NER_inputpath = input_dir + "/temp_NER_input.txt"
    temp_NER_outputpath = input_dir + "/temp_NER_output.txt"
    clickdeny_dict = {}
    with open(clickdeny_log, 'r', encoding='UTF-8')as log_file:
        lines = [line.strip() for line in log_file.readlines() if line.strip()]
    for line in lines:
        print(line)
        if line.startswith("-----"):
            continue
        if "from_activity" in line:
            from_activity = re.findall(".*from_activity]:(.*);.*",line)[0]
            to_activity = line.split("[to_activity]:")[-1]
            if from_activity == to_activity:
                continue
        a = line.split(" ")
        b = a[1].split(":")
        timestamp = a[0] + "_" + b[0] + b[1] + b[2]
        start_timestamp,end_timestamp,start_file = find_clickdeny_timastamp(input_dir,timestamp)
        print("start_timestamp " + start_timestamp + "end_timestamp " + end_timestamp)
        privacykeywords = get_datatype(start_file,temp_NER_inputpath,temp_NER_outputpath,model,NERconfig)
        print("privacykeywords " + str(privacykeywords))
        if len(privacykeywords) != 0:
            oneclick_dict = {}
            oneclick_dict["start_timestamp"]=start_timestamp
            oneclick_dict["end_timestamp"]=end_timestamp
            oneclick_dict["notice_key"]=[]
            oneclick_dict["start_data_type"]=list(privacykeywords)
            oneclick_dict["notice_data_type"]=[]
            oneclick_dict["before_purpose"]=""
            with open(data_output_path, 'r', encoding='UTF-8')as json_file:
                final_dict = loads(json_file.read())
            purpose = ""
            for key, value in final_dict.items():
                if not value.__contains__("data_type"):
                    continue
                if key.split("++++++++++")[0] <= start_timestamp:
                    for data_type in value["data_type"]:
                        if data_type in privacykeywords and value["predict"].__contains__("Purpose"):
                            purpose = key.split("++++++++++")[0] + " " + value["predict"]["Purpose"][0]
                if key.split("++++++++++")[0] > start_timestamp and key.split("++++++++++")[0] <= end_timestamp:
                    if check_timegap(key.split("++++++++++")[0],timestamp) and not check_ifgrantpermission(input_dir+"/state_"+key.split("++++++++++")[0]+".txt"):
                        for data_type in value["data_type"]:
                            if data_type in privacykeywords:
                                oneclick_dict["notice_key"].append(key)
                                oneclick_dict["notice_data_type"].append(data_type)
                                oneclick_dict["before_purpose"]=purpose
            clickdeny_dict[timestamp] = oneclick_dict
    json_str = json.dumps(clickdeny_dict, indent=4)
    with open(clickdeny_final_path, 'w', encoding='utf-8') as f:
        f.write(json_str)