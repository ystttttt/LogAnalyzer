from datetime import datetime, timedelta
import json
import os
import re
import time
import AnalysisConfig
import process_clickdeny

PrivacyLogs = None

def checkTimeOffset(netT,apiT):
    netTZ = time.strptime(netT,"%Y-%m-%d_%H%M%S")
    apiTZ = time.strptime(apiT,"%Y-%m-%d_%H%M%S")

    dt1 = datetime.fromtimestamp(time.mktime(netTZ))
    dt2 = datetime.fromtimestamp(time.mktime(apiTZ))

    diff = dt1 - dt2

    return int(diff.seconds/3600+0.5)
 
def compareTS(noticeT,privacyT):
    noticeTS = time.mktime(time.strptime(noticeT,"%Y-%m-%d_%H%M%S"))
    privacyTS = time.mktime(time.strptime(privacyT,"%Y-%m-%d_%H%M%S"))

    return noticeTS.__lt__(privacyTS)


def ApiLogAnalyze(pkg,dir):

    Log=""
    try:
        with open(os.path.join(dir,'HookApi.txt'),'r') as f:
            Log = f.read()
    except FileNotFoundError as e:
        AnalysisConfig.LogError(pkg,"ApiLog: Missing Api Hook Log")
        return
        # print("\tApiLog: Missing Api Hook Log!!!!!")

    AnalyzeRes = []
    ExistedKeys = []
    SplitRes = re.findall(r'(?P<timestamp>\d{4}-\d{2}-\d{2}-\d{6}): end call (?P<classname>.*?): (?P<methodname>.*?) return :(?P<return>.*?) param: (?P<param>.*?)', Log, re.S)

    if SplitRes:
        for log in SplitRes:
            clazz = log[1]
            method = log[2]
            for api in AnalysisConfig.ApiInfo:
                if clazz==api["classname"] and method==api["classmethod"]:
                    if(len(api["label"])==0): break
                         
                    key = log[0]+","+clazz+":"+method
                    if key in ExistedKeys: break

                    pos = log[0].rfind("-")
                    tmp = list(log[0])
                    tmp[pos] = "_"
                    ts = ''.join(tmp)

                    AnalyzeRes.append({
                        "timestamp": ts,
                        "classname": clazz,
                        "methodname": method,
                        "return": log[3],
                        "param": log[4],
                        "label": api["label"]
                    })
                    ExistedKeys.append(key)
                    break
    else: 
        AnalysisConfig.LogError(pkg,"ApiLog can't parse the result")
        # print("\tApiLog: can't parse the result")


    with open(os.path.join(AnalysisConfig.OutPut,pkg,"ApiHook.json"),'w+') as f:
         json.dump(AnalyzeRes,f,indent=4)

def LoadPrivacyLogs(pkg,dir):
    networkLog = os.path.join(AnalysisConfig.OutPut,pkg,"network.json")
    apiLog = os.path.join(AnalysisConfig.OutPut,pkg,"ApiHook.json")
    noticeLog = os.path.join(AnalysisConfig.OutPut,"NER_final.json")
    TimeCheck = True
    TimeZoneOffset = 0

    timestamp = None
    if os.path.exists(networkLog):
        with open(networkLog,'r') as f:
            logs = json.load(f)
            for log in logs:
                t = log["t"]
                if t=="timestamp":
                    timestamp = log["ts"]
                    continue
                if (log["k"] == "region" and log["v"] == "mobile_app") or log["v"] == "android.GooglePlay" or (log["k"] == "fingerprint" and log["v"] == "OnePlus") or log["k"] == "ct" or (log["k"] == "installation" and log["v"] == "null") or (log["k"] == "location" and log["v"] == "https"):
                    continue
                ts = log["flow_key"]

                key = "network_" + ts + t
                PrivacyLogs[key] = {
                    "key" : "network",
                    "timestamp": ts,
                    "data_type" : t,
                    "third_party" : log["tp"],
                    "detected_key" : log["k"],
                    "detected_value" : log["v"],
                    "notice" : False,
                    "collect_before_notice" : False
                }

        TimeCheck = False
        TimeZoneOffset = 0

    if os.path.exists(apiLog):
        with open(apiLog,'r') as f:
            logs = json.load(f)
            for log in logs:
                ts = log["timestamp"]
                t = log["label"]

                if not TimeCheck:
                    TimeZoneOffset = checkTimeOffset(timestamp,ts)
                    TimeCheck = True
                
                if TimeZoneOffset != 0:
                    origin = datetime.fromtimestamp(time.mktime(time.strptime(ts,"%Y-%m-%d_%H%M%S")))
                    changed = origin + timedelta(hours=TimeZoneOffset)
                    ts = changed.strftime("%Y-%m-%d_%H%M%S")

                key = "api_" + ts + log["methodname"]
                PrivacyLogs[key] = {
                    "key" : "api",
                    "timestamp" : ts,
                    "data_type": log["label"][0],
                    "classname": log["classname"],
                    "methodname": log["methodname"],
                    "return": log["return"],
                    "param": log["param"],
                    "notice" : False,
                    "collect_before_notice" : False
                }
    
    if os.path.exists(noticeLog):
        with open(noticeLog,'r') as f:
            logs = json.load(f)
            for log in logs.keys():
                tmp = log.split("+",1)
                ts = tmp[0]

                if process_clickdeny.check_ifgrantpermission(os.path.join(dir,"states","state_"+ts+".txt")):
                    t = logs[log]["data_type"]

                    key = "permission_"+ts
                    PrivacyLogs[key] = {
                        "key" : "permission",
                        "timestamp": "ts",
                        "data_type" : t,
                        "notice" : False,
                        "collect_before_notice" : False
                    }

def ExistenceCheck(pkg,dir):
    Log = None

    try:
        with open(os.path.join(AnalysisConfig.OutPut,pkg,"NER_final.json"),'r') as f:
            Log = json.load(f)
    except FileNotFoundError:
        # AnalysisConfig.LogError(pkg,"notice not found!")
        with open(os.path.join(AnalysisConfig.OutPut,pkg,"PrivacyLog.json"),'w+') as f:
            json.dump(PrivacyLogs,f,indent=4)
        return
    
    vague_datatype = {}

    for l in Log.keys():
        tmp = l.split("+",1)
        ts = tmp[0]

        key_list = list(Log[l]["predict"].keys())
        if len(key_list) == 1:
            if key_list[0]=="data" or key_list[0]=="Identity":
                continue
                    
        if process_clickdeny.check_ifgrantpermission(os.path.join(dir,"states","state_"+ts+".txt")):
            continue

        if "data_type" in Log[l].keys():
            tmp = l.split("+",1)
            ts = tmp[0]

            notice_label = Log[l]["data_type"]
            
            for key in PrivacyLogs.keys():
                item = PrivacyLogs[key]
                t = item["timestamp"]
                privacy_type = item["data_type"]

                if privacy_type == "cmp": continue
                # print(ts + "vs:" + t + "->" + str(compareTS(ts,t)))
                for notice_type in notice_label:
                    if notice_type == privacy_type:
                        if compareTS(ts,t): item["notice"] = True
                        else: item["collect_before_notice"] = True
                    elif AnalysisConfig.Ontology.is_ancestor(notice_type,privacy_type):
                        if compareTS(ts,t): 
                            item["notice"] = True
                            if l in vague_datatype.keys():
                                    vague_datatype[l].add(notice_type)
                            else: 
                                vague_datatype[l] = set()
                                vague_datatype[l].add(notice_type)
                        else: item["collect_before_notice"] = True

        else: continue

    with open(os.path.join(AnalysisConfig.OutPut,pkg,"PrivacyLog.json"),'w+') as f:
        json.dump(PrivacyLogs,f,indent=4)
    
    if len(vague_datatype.keys()) == 0:
        return
    
    with open(os.path.join(AnalysisConfig.OutPut,pkg,"VagueDataType.json"),'w+') as f:
        for k in vague_datatype.keys():
            vague_datatype[k] = list(vague_datatype[k])
        json.dump(vague_datatype,f,indent=4)

def Analyze(pkg,dir):
    global PrivacyLogs
    PrivacyLogs = {}

    ApiLogAnalyze(pkg,dir)
    LoadPrivacyLogs(pkg,dir)
    ExistenceCheck(pkg,dir)