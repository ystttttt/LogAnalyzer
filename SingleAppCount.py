import os
import json
import AnalysisConfig
from datetime import datetime

def dict_add(dict,value):
    if value in dict.keys():
        dict[value] +=1
    else: dict[value] = 1

def check_timegap(first_timestamp,log_timestamp):
    first_date = datetime.strptime(first_timestamp,"%Y-%m-%d_%H%M%S")
    log_date = datetime.strptime(log_timestamp,"%Y-%m-%d_%H%M%S")
    if log_date < first_date:
        return True
    else:
        return False

def count(pkg, dir):
    Output = {
        "Existence" : False,
        "collect_when_start": 0,
        "privacy_type_collected" : {},
        "network_all" : 0,
        "non_existence_all" : {},
        "non_existence_network" : {},
        "non_existence_third_party": {},
        "collect_before_notice": {},
        "CMP" : False,
        "CMP_class" : []
    }
    first_timestamp = ""
    for _, _, files in os.walk(os.path.join(dir,"states")):
        for file in files:
            if file.endswith('.jpg'):
                timestamp = file.replace(".jpg", "").replace("screen_","")
                if timestamp < first_timestamp or first_timestamp == "":
                     first_timestamp = timestamp
    with open(os.path.join(AnalysisConfig.OutPut,pkg,"PrivacyLog.json"),'r+') as f:
        Log = json.load(f)

        collection_count = 0
        network_count = 0
        non_existence_overall_count = 0
        non_existence_network_count = 0
        non_existence_third_party_count = 0
        collect_before_notice = 0

        for k,l in Log.items():
            type = l["data_type"]
            dict_add(Output["privacy_type_collected"],type)
            collection_count += 1
            
            if first_timestamp != "":
                if check_timegap(first_timestamp, l["timestamp"]):
                    Output["collect_when_start"] += 1

            if l["key"] == "network":
                network_count += 1

            if l["notice"] == False: 
                Output["Existence"] = True
                dict_add(Output["non_existence_all"],type)
                non_existence_overall_count += 1

                if l["key"] == "network":
                    dict_add(Output["non_existence_network"],type)
                    non_existence_network_count += 1

                    if l["third_party"] != "None":
                        dict_add(Output["non_existence_third_party"],type)
                        non_existence_third_party_count += 1

            if l["collect_before_notice"] == True:
                dict_add(Output["collect_before_notice"],type)
                collect_before_notice += 1

            # cmp should be excluded in the count
            if l["key"] == "api" and l["data_type"] == "cmp": 
                Output["CMP"] = True
                Output["CMP_class"].append(l["classname"])     


        
        Output["privacy_type_collected"]["sum"] = collection_count
        Output["non_existence_all"]["sum"] = non_existence_overall_count
        Output["non_existence_network"]["sum"] = non_existence_network_count
        Output["non_existence_third_party"]["sum"] = non_existence_third_party_count
        Output["collect_before_notice"]["sum"] = collect_before_notice
        Output["network_all"] = network_count
        Output["CMP_class"] = list(set(Output["CMP_class"]))


    with open(os.path.join(AnalysisConfig.OutPut,pkg,"AppCount.json"),"w") as f:
        json.dump(Output,f,indent=4)
            


            


