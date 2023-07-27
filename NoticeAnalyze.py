import torch
from Model.config import Config
from Model.NERconfig import NERConfig
from Model.preprocess import dataloader
from Model.model_bert import Model,NERModel
import json,time,os
import re
from json import loads
from transformers import BertTokenizer
from transformers import BertConfig
from Model.NoticeReco import test
from Model.NERReco import NERtest
from torch.utils.data import random_split
from pygtrans import Translate
import langid
import easyocr
from process_clickdeny import match_clickdeny,match_privacykeywords
import AnalysisConfig

client = Translate()
reader = easyocr.Reader(['en','de','fr','it','nl','es','sv','hr','cs','da','et','hu','ga','lv','lt','mt','pl','pt','ro','sk'])
package = ""
 

def check_ifbrowser(json_file):
    with open(json_file, 'r', encoding='UTF-8')as f:
        load_dict = loads(f.read())
    for activity in load_dict["activity_stack"]:
        if "chromium.chrome.browser" in activity or "com.google.android.finsky.activities.MainActivity" in activity:
            return True


def build_finaloutput(NERlabelfile,NERtimestampfile,data_output_path):
    if os.path.exists(data_output_path):
        return
    with open(NERlabelfile, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    with open(NERtimestampfile, 'r', encoding='utf-8') as f:
        timestamp_lines = [line.strip() for line in f.readlines() if line.strip()]
    NER_dict={}
    for index,line in enumerate(lines):
        timestamp = timestamp_lines[index]
        privacykeywords = set()
        dict_line = loads(line)
        if len(dict_line["predict"]) == 0:
            continue
        if dict_line.__contains__("real"):
            dict_line.pop("real")
        if dict_line.__contains__("error"):
            dict_line.pop("error")
        dict_predict = dict_line["predict"]
        for key, value in dict_predict.items():
            new_value = []
            for words in value:
                sentence = " ".join(words)
                new_value.append(sentence)
            print(new_value)
            dict_predict[key]=new_value
        if dict_line["predict"].__contains__("data"):
            data_array = dict_line["predict"]["data"]
            for data in data_array:
                print(data)
                key_list=match_privacykeywords(data)
                privacykeywords = privacykeywords.union(key_list)
            dict_line["data_type"] = list(privacykeywords)
        NER_dict[timestamp] = dict_line
    json_str = json.dumps(NER_dict, indent=4)
    with open(data_output_path, 'a', encoding='utf-8') as f:
        f.write(json_str)

def build_pageoutput(data_output_path, page_output_path):
    with open(data_output_path, 'r', encoding='UTF-8') as json_file:
        final_dict = loads(json_file.read())
    page_dict = {}
    timestamp_record = []
    for key_i, value_i in final_dict.items():
        timestamp = key_i.split("++++++++++")[0]
        if timestamp in timestamp_record:
            continue
        timestamp_record.append(timestamp)
        new_value = value_i
        for key_j, value_j in final_dict.items():
            if key_i != key_j and timestamp == key_j.split("++++++++++")[0]:
                for label in value_j["label"]:
                    label[0] += (len(new_value["text"].split()))
                    label[1] += (len(new_value["text"].split()))
                new_value["label"] = new_value["label"] + value_j["label"]
                new_value["text"] = new_value["text"] + " " + value_j["text"] 
                if value_j.__contains__("data_type"):
                    if new_value.__contains__("data_type"):
                        new_value["data_type"] = list(set(new_value["data_type"]).union(set(value_j["data_type"])))
                    else:
                        new_value["data_type"] = value_j["data_type"]
                for key in value_j["predict"].keys():
                    if new_value["predict"].__contains__(key):
                        new_value["predict"][key].extend(value_j["predict"][key])
                    else:
                        new_value["predict"][key] = value_j["predict"][key]
        page_dict[timestamp] = new_value
    json_str = json.dumps(page_dict, indent=4)
    with open(page_output_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
                
                
def process_line(line):
    try:
        if langid.classify(line)[0] != 'en':
            print("Need Translate")    
            translate_line = client.translate(line, target='en')
            print(line)
            line = translate_line.translatedText
        line = re.sub("]-·[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+"," ", line)
        line = re.sub("[`,.;:'?!()\{\}]","", line)
        line = re.sub('"','', line)
        line = re.sub("\r\n","", line)        
        return line
    except Exception as e:
        print(e)
        AnalysisConfig.LogError(package,"NoticeAnalyze--"+str(e))
        line = re.sub("]-·[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+"," ", line)
        line = re.sub("[`,.;:'?!()\{\}]","", line)
        line = re.sub('"','', line)
        line = re.sub("\r\n","", line)
        return line
    
def ocr_get_text(jpg_path):
    try:
        print("ocr" + jpg_path)
        hiddentext = reader.readtext(jpg_path, detail=0, paragraph=True)
        for text in hiddentext:
            text = process_line(text)
            with open(jpg_path.replace(".jpg",".txt").replace("screen","state"), 'a', encoding='utf-8') as f:
                f.write(text + "\n")
    except Exception as e:
        print(e)
        AnalysisConfig.LogError(package,"NoticeAnalyze--"+str(e))                            

def get_afterdeny_text(clickdeny_log,pkg):
    '''
    For every log of clicking deny, judge whether the from-activity is same as to-activity.
    If not, apply OCR to the following three images. 
    ''' 
    input_dir = clickdeny_log.replace("ourlogs","states")
    clickdeny_log = os.path.join(clickdeny_log,pkg)
    with open(clickdeny_log, 'r', encoding='UTF-8')as log_file:
        lines = [line.strip() for line in log_file.readlines() if line.strip()]
    for line in lines:
        print(line)
        if line.startswith("-----"):
            continue
        if "from_activity" in line:
            from_activity = re.findall(".*from_activity]:(.*);.*",line)[0]
            to_activity = line.split("[to_activity]:")[-1]
            print(from_activity)
            print(to_activity)
            if from_activity == to_activity:
                continue
        a = line.split(" ")
        b = a[1].split(":")
        timestamp = a[0] + "_" + b[0] + b[1] + b[2]
        count = 0
        for root, _, files in os.walk(input_dir):
            files.sort()
            for file in files:
                if count >= 3:
                    break
                if file.endswith('.jpg'):
                    file_timestamp = file.replace("screen_","").replace(".jpg","")
                    if file_timestamp > timestamp:
                        count = count + 1
                        jpg_path = os.path.join(root, file)
                        txt_path = jpg_path.replace(".jpg",".txt").replace("screen","state")
                        if not os.path.exists(txt_path):
                            ocr_get_text(jpg_path)        

def readjson_for_longsentence(input_dir,notice_input_path):
    if os.path.exists(notice_input_path):
        return
    with open(notice_input_path, 'a', encoding='utf-8') as f:
        f.write("text" + "\n")
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json') and file != "NER_final.json" and file != "clickdeny_final.json":
                if check_ifbrowser(os.path.join(root, file)):
                    print(file," is a browser activity")
                    continue
                print(file)
                txtfile_path = os.path.join(root, file.replace(".json",".txt"))
                long_sentence = ""
                if os.path.exists(txtfile_path):
                    with open(txtfile_path, 'r', encoding='UTF-8')as txt_file:
                        lines = [line.strip() for line in txt_file.readlines() if line.strip()]
                    for line in lines: 
                        long_sentence = long_sentence + " " + line.split("++++++++++")[0]
                else:
                    with open(os.path.join(root, file), 'r', encoding='UTF-8')as json_file:
                        load_dict = loads(json_file.read())
                    for view in load_dict["views"]:
                        if not view["visible"]:
                            continue
                        text = view["text"]
                        if isinstance(text, str) and len(text) > 0:
                            text = process_line(text)
                            text = text.replace("\n","")
                            if len(text) > 0:
                                long_sentence = long_sentence + " " + text
                            bounds = view["bounds"]
                            with open(txtfile_path, 'a', encoding='UTF-8')as txt_file:
                                txt_file.write(text + "++++++++++" + str(bounds) + "\n")
                if len(long_sentence) > 0 and len(long_sentence) < 1000:
                    with open(notice_input_path, 'a', encoding='utf-8') as f:
                        f.write('++++++++++' + os.path.join(root, file) + "\n")
                        f.write(long_sentence + "\n")
                print('[DONE]: ' + file)

def readjson_for_shortsentence(notice_output_path,element_input_path,element_timestamp_path):
    if os.path.exists(element_input_path):
        return
    with open(element_input_path, 'a', encoding='utf-8') as f:
        f.write("text" + "\n")
    with open(notice_output_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    for line in lines:
        if line.startswith('++++++++++'):
            filename = line.split(',')[0].replace('++++++++++','')
        else:
            if line.split(',')[-1] == "0":
                print(filename + " is a notice page")
                timestamp = filename.split('/')[-1].replace("state_","").replace(".json","")
                with open(filename.replace(".json",".txt"), 'r', encoding='UTF-8')as txt_file:
                    lines = [line.strip() for line in txt_file.readlines() if line.strip()]
                for line in lines:
                    if "state_2023-04-17_130331" in filename:
                        print(line)
                        print(len(line))
                    if line.split("++++++++++")[0] != "null": 
                        with open(element_input_path, 'a', encoding='utf-8') as f:
                            f.write(line.split("++++++++++")[0] + "\n")
                        with open(element_timestamp_path, 'a', encoding='utf-8') as f:
                            f.write(timestamp + "++++++++++" + line.split("++++++++++")[-1] + "\n")

def process_states(pkg,input_dir):
    global package
    package = pkg
    ourlogs_dir = os.path.join(input_dir,"ourlogs")
    input_dir = os.path.join(input_dir,"states")

    output_dir = os.path.join(AnalysisConfig.OutPut, package)
    if not os.path.exists(input_dir):
        AnalysisConfig.LogError(pkg,input_dir+" does not exist")
        return
    
    AnalysisConfig.mkdir(os.path.join(output_dir,"NER_log"))

    notice_input_path = os.path.join(output_dir,"NER_log/long_sentence.txt")
    notice_output_path = os.path.join(output_dir ,"NER_log/long_sentence_label.txt")
    element_input_path = os.path.join(output_dir ,"NER_log/element_sentence.txt")
    element_output_path = os.path.join(output_dir, "NER_log/element_sentence_label.txt")
    element_timestamp_path = os.path.join(output_dir, "NER_log/element_timestamp.txt")
    NER_timestamp_path = os.path.join(output_dir, "NER_log/NER_timestamp.txt")
    NER_input_path = os.path.join(output_dir, "NER_log/NER_sentence.txt")
    NER_output_path = os.path.join(output_dir, "NER_log/NER_sentence_label.txt")
    data_output_path = os.path.join(output_dir, "NER_final.json")
    page_output_path = os.path.join(output_dir, "page_final.json")
    clickdeny_final_path = os.path.join(output_dir, "clickdeny_final.json")
    
    get_afterdeny_text(ourlogs_dir,pkg)
    readjson_for_longsentence(input_dir,notice_input_path)
    
    # Judge whether the page is runtime privacy page through long text
    if not os.path.exists(notice_output_path):            
        config = Config()
        config.device = torch.device("cuda" if torch.cuda.is_available() and not config.no_cuda else "cpu")
        if config.local_rank == -1 or config.no_cuda: 
            config.n_gpu = torch.cuda.device_count()
        notice_classifier_checkpoint = "./Model/final_model/Notice_model"
        bertconfig = BertConfig.from_pretrained(notice_classifier_checkpoint, num_labels=config.num_classes)
        model = Model.from_pretrained(notice_classifier_checkpoint, config=bertconfig)
        model.to(config.device)
        testloader = dataloader(dtype='classifier', config=config, classifier_path = notice_input_path)
        testdata, testTexts = testloader.load_data()
        test(config, model, testdata, testTexts, output_path = notice_output_path)
    readjson_for_shortsentence(notice_output_path, element_input_path, element_timestamp_path)
    if not os.path.exists(element_timestamp_path):
        return

    # Determine whether the six elements are in the sentences separately
    if not os.path.exists(NER_input_path):
        config = Config()
        config.device = torch.device("cuda" if torch.cuda.is_available() and not config.no_cuda else "cpu")
        if config.local_rank == -1 or config.no_cuda: 
            config.n_gpu = torch.cuda.device_count()
        element_classifier_checkpoint = ["Right_model","Identity_model","Legalbasis_model","Storage_model","Receiver_model","Purpose_model"]
        lines_index = set()
        for checkpoint in element_classifier_checkpoint:
            checkpoint_path = "./Model/final_model/" + checkpoint
            print(checkpoint_path)
            bertconfig = BertConfig.from_pretrained(checkpoint_path, num_labels=config.num_classes)
            model = Model.from_pretrained(checkpoint_path, config=bertconfig)
            model.to(config.device)
            testloader = dataloader(dtype='classifier', config=config, classifier_path = element_input_path)
            testdata, testTexts = testloader.load_data()
            test(config, model, testdata, testTexts, output_path = element_output_path)
            with open(element_output_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            for index,line in enumerate(lines):
                if line.split(',')[1] == "0":
                    print(line)
                    print(index)
                    lines_index.add(index)
        # Write a sentence with one of the six elements and its timestamp into the file
        with open(element_output_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        with open(element_timestamp_path, 'r', encoding='utf-8') as f:
            timestamps = [line.strip() for line in f.readlines() if line.strip()]            
        for index in lines_index:
            with open(NER_timestamp_path, 'a', encoding='utf-8') as f:
                f.write(timestamps[index] + "\n")
            words = lines[index].split(',')[0].split()
            with open(NER_input_path, 'a', encoding='utf-8') as f:
                for word in words:
                    if langid.classify(word)[0] == 'en':
                        f.write(word + "\n")
        with open(NER_input_path, 'a', encoding='utf-8') as f:
            f.write("\n")
    
    # Mark the position of six elements in a sentence
    if (not os.path.exists(NER_output_path)) and os.path.exists(NER_input_path):
        with open(NER_input_path, 'a', encoding='utf-8') as f:
            line = f.readline()
        if len(line) != 0:
            NERconfig = NERConfig()
            NERconfig.device = torch.device("cuda" if torch.cuda.is_available() and not NERconfig.no_cuda else "cpu")
            if NERconfig.local_rank == -1 or NERconfig.no_cuda: 
                NERconfig.n_gpu = torch.cuda.device_count()
            NER_classifier_checkpoint = "./Model/final_model/NER_model"
            bertconfig = BertConfig.from_pretrained(NER_classifier_checkpoint, num_labels=NERconfig.num_classes)
            model = NERModel.from_pretrained(NER_classifier_checkpoint, config=bertconfig)
            model.to(NERconfig.device)
            testloader = dataloader(dtype='NERclassifier', config=NERconfig, classifier_path = NER_input_path)
            testdata, testTexts, tokens = testloader.load_NERdata()
            NERtest(NERconfig, model, testdata, testTexts, tokens, output_path = NER_output_path)
            
            build_finaloutput(NER_output_path,NER_timestamp_path,data_output_path)
    if (not os.path.exists(page_output_path)) and os.path.exists(data_output_path):
        build_pageoutput(data_output_path, page_output_path)

    NERconfig = NERConfig()
    NERconfig.device = torch.device("cuda" if torch.cuda.is_available() and not NERconfig.no_cuda else "cpu")
    if NERconfig.local_rank == -1 or NERconfig.no_cuda: 
        NERconfig.n_gpu = torch.cuda.device_count()
    NER_classifier_checkpoint = "./Model/final_model/NER_model"
    bertconfig = BertConfig.from_pretrained(NER_classifier_checkpoint, num_labels=NERconfig.num_classes)
    model = NERModel.from_pretrained(NER_classifier_checkpoint, config=bertconfig)
    model.to(NERconfig.device)
    clickdeny_log = input_dir.replace("/states","/ourlogs")+"/"+input_dir.split("/")[-2]
    if (not os.path.exists(clickdeny_final_path)) and os.path.exists(clickdeny_log) and os.path.exists(data_output_path):
        match_clickdeny(input_dir,data_output_path,model,NERconfig,clickdeny_final_path)
