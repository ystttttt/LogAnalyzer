import os
import json
from treelib import Tree,Node

OntologyFile = "Config/Ontology.json"
ApiFile = "Config/deviceInfoAPIs_filtered.json"
privacy_keyword_path = "Config/2nd_privacy2keyword.json"
Template = "Config/Result_template.json"

CountryFile = "countriesCode.json"
CatFile = "appCategory.json"
AppList = "final_list_country_installs_final.json"
installFile = "sorted_install_list.json"

LogPaths = ["/media/npc/16E22B97E22B7A5F/batch3/","/media/npc/16E22B97E22B7A5F/batch2/","/media/npc/16E22B97E22B7A5F/batch1/"]
OutPut = "/media/npc/16E22B97E22B7A5F/Output-all/"
ErrorLogPath = "/media/npc/16E22B97E22B7A5F/LogAnalyzeErrorLog.txt"

def LogError(pkg,str):
    with open(ErrorLogPath,"+a") as f:
        f.write(pkg+": "+str+"\n")

def mkdir(path):
	folder = os.path.exists(path)
 
	if not folder: 
		os.makedirs(path) 

def init():
    global ApiInfo
    global Output_path
    Output_path = OutPut
    with open(ApiFile,'r') as f:
        ApiInfo = json.load(f)
    
    global Ontology
    Ontology = Tree()
    Ontology.create_node(tag='PII', identifier='PII', data="PII")
    
    with open(OntologyFile,'r') as f:
        OntologyInfo = json.load(f)
        for k in OntologyInfo.keys():
            children = OntologyInfo[k]
            for child in children:
                Ontology.create_node(tag=child, identifier=child, data=child, parent=k)

    Ontology.show()

    global LogList
    LogList = {}
    for LogPath in LogPaths:
        for file in os.listdir(LogPath):
            path = os.path.join(LogPath,file)
            if os.path.isdir(path):
                LogList[file] = path
    print("Logs need to analyze:" + str(len(LogList.keys())))

def init_min():
    global ApiInfo
    with open(ApiFile,'r') as f:
        ApiInfo = json.load(f)
    
    global Ontology
    Ontology = Tree()
    Ontology.create_node(tag='PII', identifier='PII', data="PII")
    
    with open(OntologyFile,'r') as f:
        OntologyInfo = json.load(f)
        for k in OntologyInfo.keys():
            children = OntologyInfo[k]
            for child in children:
                Ontology.create_node(tag=child, identifier=child, data=child, parent=k)

    Ontology.show()

    global app_info
    with open(AppList,'r') as f:
        app_info = json.load(f)

    global LogAllList
    LogAllList = {}
    for LogPath in LogPaths:
        for file in os.listdir(LogPath):
            path = os.path.join(LogPath,file)
            if os.path.isdir(path):
                LogAllList[file] = path

    global log_info
    


def init_country(country,OPT):
    global LogList
    LogList = {}

    country_app = 0
    country_log = 0
    for app,info in app_info.items():
        if country in info["country"]:
            country_app += 1
            for LogPath in LogPaths:
                if app in os.listdir(LogPath):
                    path = os.path.join(LogPath,app)
                    country_log += 1
                    if os.path.isdir(path):
                        LogList[app] = path
    
    print(country + ": " + str(country_app) + ", " + str(country_log))
    mkdir(os.path.join(OPT,country))

def init_category(cat,OPT):
    global LogList
    LogList = {}

    cat_app = 0
    cat_log = 0
    for app,info in app_info.items():
        if cat == info["category"]:
            cat_app += 1
            for LogPath in LogPaths:
                if app in os.listdir(LogPath):
                    path = os.path.join(LogPath,app)
                    cat_log += 1
                    if os.path.isdir(path):
                        LogList[app] = path
    
    print(cat + ": " + str(cat_app) + ", " + str(cat_log))
    mkdir(os.path.join(OPT,cat))

def init_installs(inslevel,app_list,OPT):
    global LogList
    LogList = {}

    install_app = 0
    install_log = 0
    for package in app_list:
        install_app += 1
        for LogPath in LogPaths:
            if package in os.listdir(LogPath):
                path = os.path.join(LogPath,package)
                install_log += 1
                if os.path.isdir(path):
                    LogList[package] = path
    
    print(inslevel + ": " + str(install_app) + ", " + str(install_log))
    mkdir(os.path.join(OPT,inslevel))

def check_logdir(package):
    for LogPath in LogPaths:
        if package in os.listdir(LogPath):
            path = os.path.join(LogPath,package)
            if os.path.isdir(path): return path
            else: return None
                    