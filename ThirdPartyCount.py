import json
import os

class ThirdParty:

    def __init__(self,name):
        self.ThirdParty_name = name
        self.related_flow_count = 0
        self.related_label_count = 0
        self.related_bahavior_count = 0
        self.related_non_existence_count = 0
        self.label_detail = {}


class ThirdPartyLog:
    def __init__(self):
        global TPLog 
        
        self.flow_count = 0
        self.flow_TP_count = 0
        TPLog = {}

    def app_init(self):
        global app_flow
        app_flow = {}

    def add_flow(self,flow):
        if not flow in app_flow:
            self.flow_count += 1
            app_flow[flow] = []

    
    def add(self,flow,name,label,existence):
        if not name in TPLog.keys(): TPLog[name] = ThirdParty(name)
        TPitem = TPLog[name]
        
        if not flow in app_flow: 
            TPitem.related_flow_count += 1
            self.flow_TP_count += 1
            app_flow[flow] = []
        
        if not label in TPitem.label_detail.keys(): 
            TPitem.label_detail[label] = 0
            TPitem.related_label_count += 1

        if not label in app_flow[flow]:
            app_flow[flow].append(label)
            TPitem.label_detail[label] += 1
            TPitem.related_bahavior_count += 1
            if not existence: TPitem.related_non_existence_count += 1

    def output(self,optPath):
        output = {}

        non_existence = 0
        behavior = 0
        
        for key,item in TPLog.items():
            non_existence += item.related_non_existence_count
            behavior += item.related_bahavior_count
            output[key] = {
                "related_flow_count" : item.related_flow_count,
                "related_label_count" : item.related_label_count,
                "related_bahavior_count" : item.related_bahavior_count,
                "related_non_existence_count" : item.related_non_existence_count,
                "label_detail" : item.label_detail
            }
        
        output["bahavior"] = behavior
        output["non_existence"] = non_existence
        output["flow_count"] = self.flow_count
        output["flow_TP_count"] = self.flow_TP_count
        output["flow_TP_coverage"] = float(self.flow_TP_count/self.flow_count)

        with open(optPath,'w+') as f:
            json.dump(output,f,indent=4)
        



