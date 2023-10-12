import os
import json
from treelib import Tree,Node

OntologyFile = "Config/Ontology.json"
ApiFile = "Config/deviceInfoAPIs_filtered.json"
privacy_keyword_path = "Config/2nd_privacy2keyword.json"
Template = "Config/Result_template.json"

# AppAutoRun output path
LogPaths = ["/media/npc/16E22B97E22B7A5F/batch3/","/media/npc/16E22B97E22B7A5F/batch2/","/media/npc/16E22B97E22B7A5F/batch1/"]
# Analysis output path
OutPut = "/media/npc/16E22B97E22B7A5F/Output-all/"
# LogFile
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
    Ontology.create_node(tag='privacy_data', identifier='privacy_data', data="privacy_data")
    
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