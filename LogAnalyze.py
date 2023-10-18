import os
import AnalysisConfig  
import json
import LoadPrivacyLog
import NoticeAnalyze
import process_clickdeny
import VagueClassifier
import ThirdPartyCount
import SingleAppCount
import shutil

TPCount = None
Notice_Type_Count = 0
Notice_Type_CBN_Count = 0

App_Collect_Before_Notice = None
NoticeTime = None

def get_Existence(Overall,Existence_Gap,CollectBeforeNotice,logPath):
    if os.path.exists(logPath):
        with open(logPath,'r',encoding='UTF-8')as f:
            count = json.loads(f.read())
        
        if count["privacy_type_collected"]["sum"]!=0: Overall["App_w_privacy_collection_behavior"] +=1
        if count["Existence"]==True : Existence_Gap["App_w_ExistenceGap"] +=1
                    
        Overall["privacy_collection_behavior"] += count["privacy_type_collected"]["sum"]
        Existence_Gap["privacy_collection_behavior_w/o_RPN"] += count["non_existence_all"]["sum"]

        global App_Collect_Before_Notice
        App_Collect_Before_Notice = set()
                    
        if len(count["collect_before_notice"].keys()) > 1:
            CollectBeforeNotice["App_w_collect_before_notice"] += 1
            
            for type in count["collect_before_notice"].keys():
                if type == "sum" or type == "cmp" : continue
                App_Collect_Before_Notice.add(type)
                
        for type in count["privacy_type_collected"].keys():
            if type == "sum" or type == "cmp" : continue
            if type in Overall["privacy_collection_behavior_detail_category"].keys():
                Overall["privacy_collection_behavior_detail_category"][type] += count["privacy_type_collected"][type]
            else: Overall["privacy_collection_behavior_detail_category"][type] = count["privacy_type_collected"][type]

        for type in count["non_existence_all"].keys():
            if type == "sum" or type == "cmp": continue
            if type in Existence_Gap["privacy_collection_behavior_w/o_RPN_detail_category"].keys():
                Existence_Gap["privacy_collection_behavior_w/o_RPN_detail_category"][type] += count["non_existence_all"][type]
            else: Existence_Gap["privacy_collection_behavior_w/o_RPN_detail_category"][type] = count["non_existence_all"][type]

def get_Quality_Element(Overall,QP_Element,logPath,logPath2,VagueLabel,Vague_Notice_label):
    if os.path.exists(logPath):
        Overall["App_w_RPN"] += 1
        with open(logPath2, 'r', encoding='UTF-8')as json_file:
            page_dict = json.loads(json_file.read())

        original_right = QP_Element["Elements_in_RPN"]["Right"]
        original_identity = QP_Element["Elements_in_RPN"]["Identity"]

        notice_type = []
        global NoticeTime
        NoticeTime = []
        for key,value in page_dict.items():
            if not process_clickdeny.check_ifgrantpermission(os.path.join(states_dir,"state_"+key+".txt")):
                key_list = list(value["predict"].keys())
                key_list.sort()
                element_num = len(key_list)
                if element_num == 1 and (key_list[0]=="data" or key_list[0]=="Identity"):
                    continue

                timestamp = key.split("++++++++++")[0]
                NoticeTime.append(timestamp)
                QP_Element["RPN"] += 1
                if element_num == 1:
                    QP_Element["RPN_w_specific_number_of_elements"]["one_element"]+=1
                elif element_num == 2:
                    QP_Element["RPN_w_specific_number_of_elements"]["two_elements"]+=1
                elif element_num == 3:
                    QP_Element["RPN_w_specific_number_of_elements"]["three_elements"]+=1
                elif element_num == 4:
                    QP_Element["RPN_w_specific_number_of_elements"]["four_elements"]+=1
                elif element_num == 5:
                    QP_Element["RPN_w_specific_number_of_elements"]["five_elements"]+=1
                elif element_num == 6:
                    QP_Element["RPN_w_specific_number_of_elements"]["six_elements"]+=1
                elif element_num == 7:
                    QP_Element["RPN_w_specific_number_of_elements"]["seven_elements"]+=1
                        
                for label in key_list:
                    QP_Element["Elements_in_RPN"][label]+=1
                    if label == "Identity":
                        if(VagueClassifier.classify_Identity(value["predict"][label])):
                            VagueLabel["Vague_identity"] = True
                            Vague_Notice_label.add(key)
                    elif label == "Receiver":
                        if(VagueClassifier.classify_Receiver(value["predict"][label])):
                            VagueLabel["Vague_receiver"] = True
                            Vague_Notice_label.add(key)
                    elif label == "Purpose":
                        if(VagueClassifier.classify_Purpose(value["predict"][label])):
                            VagueLabel["Vague_purpose"] = True
                            Vague_Notice_label.add(key)
                
                if "data_type" in value.keys():
                    notice_type.extend(value["data_type"])
                
        if original_right < QP_Element["Elements_in_RPN"]["Right"]:
            QP_Element["Elements_in_RPN"]["App_w_Right"] += 1
        if original_identity < QP_Element["Elements_in_RPN"]["Identity"]:
            QP_Element["Elements_in_RPN"]["App_w_Identity"] += 1
        
        notice_type = list(set(notice_type))
        for type in notice_type:
            global Notice_Type_Count
            Notice_Type_Count += 1
            for t in App_Collect_Before_Notice:
                if AnalysisConfig.Ontology.is_ancestor(type,t) or type == t:
                    global Notice_Type_CBN_Count
                    Notice_Type_CBN_Count += 1
                    break
                    

def get_Quality_Vague(QP_Vague,logPath,VagueLabel,Vague_Notice_label):
    if os.path.exists(logPath):
        VagueLabel["Vague_type"] = True
        QP_Vague["data_type_vague_expression"]["app"] +=1

        with open(logPath, 'r', encoding='UTF-8')as f:
            vagueType_dict = json.loads(f.read())
        
        for key,value in vagueType_dict.items():
            Vague_Notice_label.add(key.split("++++++++++")[0])
            QP_Vague["data_type_vague_expression"]["notice"] +=1
            for label in value:
                if label in QP_Vague["data_type_vague_expression"]["detail"].keys():
                    QP_Vague["data_type_vague_expression"]["detail"][label]+=1
                else: QP_Vague["data_type_vague_expression"]["detail"][label] = 1
    
    if(VagueLabel["Vague_identity"]): QP_Vague["identity_vague_expression"]["app"] +=1
    if(VagueLabel["Vague_receiver"]): QP_Vague["receiver_vague_expression"]["app"] +=1
    if(VagueLabel["Vague_purpose"]): QP_Vague["purpose_vague_expression"]["app"] +=1

    if(VagueLabel["Vague_type"]|VagueLabel["Vague_identity"]|VagueLabel["Vague_receiver"]|VagueLabel["Vague_purpose"]):  
        QP_Vague["App_w_RPN_using_vague_expression"] +=1
        QP_Vague["RPN_using_vague_expression"] += len(Vague_Notice_label)

def get_Quality_RPN_after_denying_request(QP_RPN_after_denying_request,logPath):
    if os.path.exists(logPath):
        with open(logPath, 'r', encoding='UTF-8')as f:
            clickdeny_dict = json.loads(f.read())

        if len(clickdeny_dict)!=0:
            original_num = QP_RPN_after_denying_request["RPN_after_denying_request"]
            for key,value in clickdeny_dict.items():
                if value["start_timestamp"] in NoticeTime: 
                    if not process_clickdeny.check_ifgrantpermission(os.path.join(states_dir,"state_"+value["start_timestamp"]+".txt")):
                        continue
                    
                userinput_all = 0
                permission_all = 0
                device_all = 0
                others_all = 0

                userinput_positive = 0
                permission_positive = 0
                device_positive = 0
                others_positive = 0

                start_data_type = value["start_data_type"]
                notice_data_type = value["notice_data_type"] 
                        
                if len(value["notice_key"]) != 0:
                    for datatype in notice_data_type:
                        if (AnalysisConfig.Ontology.is_ancestor("user_input",datatype) or datatype == "user_input") and not AnalysisConfig.Ontology.is_ancestor("user_credentials",datatype):
                            userinput_positive = 1
                        elif AnalysisConfig.Ontology.is_ancestor("permission",datatype) or datatype == "permission":
                            permission_positive = 1
                        elif datatype != "general_location" and (AnalysisConfig.Ontology.is_ancestor("device_information",datatype) or datatype == "device_information"):
                            device_positive = 1
                        elif AnalysisConfig.Ontology.is_ancestor("others",datatype):
                            others_positive = 1

                for datatype in start_data_type:
                    if AnalysisConfig.Ontology.is_ancestor("user_input",datatype) and not AnalysisConfig.Ontology.is_ancestor("user_credentials",datatype):
                        userinput_all = 1
                    elif AnalysisConfig.Ontology.is_ancestor("permission",datatype) or datatype == "permission":
                        permission_all = 1
                    elif datatype != "general_location" and (AnalysisConfig.Ontology.is_ancestor("device_information",datatype) or datatype == "device_information"):
                        device_all = 1
                    elif AnalysisConfig.Ontology.is_ancestor("others",datatype):
                        others_all = 1

                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["Denied_requests_userinput"]+=userinput_all
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["Denied_requests_permission"]+=permission_all
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["Denied_requests_device_info"]+=device_all
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["Denied_requests_others"]+=others_all
                QP_RPN_after_denying_request["RPN_after_denying_request"]+=(userinput_positive|permission_positive|device_positive|others_positive)
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["RPN_after_denying_request_userinput"]+=userinput_positive
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["RPN_after_denying_request_permission"]+=permission_positive
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["RPN_after_denying_request_device_info"]+=device_positive
                QP_RPN_after_denying_request["Data_type_RPN_after_denying_request_main"]["RPN_after_denying_request_others"]+=others_positive
                                
            if original_num < QP_RPN_after_denying_request["RPN_after_denying_request"]:
                QP_RPN_after_denying_request["App_w_RPN_after_denying_request"]+=1        


def getTP(logPath):
    if os.path.exists(logPath):
        TPCount.app_init()
    with open(logPath,'r') as f:
        Log = json.load(f)
    for key,log in Log.items():
        if key.find("network") != -1:
            if log["third_party"] != "None": TPCount.add(log["timestamp"],log["third_party"],log["data_type"],log["notice"])
            else: TPCount.add_flow(log["timestamp"])

def sort(Result):
    Result["Quality_Gap_Vague_expression"]["identity_vague_expression"]["notice"] = VagueClassifier.Vague_Identity_Notice_Count
    Result["Quality_Gap_Vague_expression"]["receiver_vague_expression"]["notice"] = VagueClassifier.Vague_Receiver_Notice_Count
    Result["Quality_Gap_Vague_expression"]["purpose_vague_expression"]["notice"] = VagueClassifier.Vague_Purpose_Notice_Count

    Result["Quality_Gap_Vague_expression"]["identity_vague_expression"]["detail"] = VagueClassifier.Vague_Identity
    Result["Quality_Gap_Vague_expression"]["receiver_vague_expression"]["detail"] = VagueClassifier.Vague_Receiver
    Result["Quality_Gap_Vague_expression"]["purpose_vague_expression"]["detail"] = VagueClassifier.Vague_Purpose

    Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_ratio"] = float(Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN"]/Result["Overall"]["privacy_collection_behavior"])
    Result["Existence_Gap"]["App_w_ExistenceGap_ratio"] = float(Result["Existence_Gap"]["App_w_ExistenceGap"]/Result["Tested_App"])
    Result["Quality_Gap_collect_before_notice"]["Data_type_RPN_collected_before_notice_ratio"] = float(Notice_Type_CBN_Count/Notice_Type_Count)

    for type in Result["Overall"]["privacy_collection_behavior_detail_category"].keys():
        sum = Result["Overall"]["privacy_collection_behavior_detail_category"][type]

        if AnalysisConfig.Ontology.is_ancestor("device_information",type) or type == "device_information":
            Result["Overall"]["privacy_collection_behavior_main_category"]["device_information"] += Result["Overall"]["privacy_collection_behavior_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("personal_information",type) or type == "user_input":
            Result["Overall"]["privacy_collection_behavior_main_category"]["user_input"] += Result["Overall"]["privacy_collection_behavior_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("permission",type) or type == "permission":
            Result["Overall"]["privacy_collection_behavior_main_category"]["permission"] += Result["Overall"]["privacy_collection_behavior_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("others",type) or type == "others":
            Result["Overall"]["privacy_collection_behavior_main_category"]["others"] += Result["Overall"]["privacy_collection_behavior_detail_category"][type]

    for type in Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_detail_category"].keys():
        if AnalysisConfig.Ontology.is_ancestor("device_information",type) or type == "device_information":
            Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_main_category"]["device_information"] += Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("personal_information",type) or type == "user_input":
            Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_main_category"]["user_input"] += Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("permission",type) or type == "permission":
            Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_main_category"]["permission"] += Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_detail_category"][type]
        elif AnalysisConfig.Ontology.is_ancestor("others",type) or type == "others":
            Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_main_category"]["others"] += Result["Existence_Gap"]["privacy_collection_behavior_w/o_RPN_detail_category"][type]

def countFinal(OPT):
    VagueClassifier.init()
    global TPCount
    TPCount = ThirdPartyCount.ThirdPartyLog()

    with open(AnalysisConfig.Template,'r',encoding='UTF-8')as f:
        Result = json.loads(f.read())

    for package in AnalysisConfig.LogList.keys():
        print(package)
        app_dir = AnalysisConfig.LogList[package]
        OutPutPath = os.path.join(AnalysisConfig.OutPut,package)

        Vague_Notice_label = set()
        VagueLabel = {
            "Vague_type": False,
            "Vague_identity": False,
            "Vague_receiver": False,
            "Vague_purpose": False
        }

        if os.path.exists(OutPutPath):
            Result["Tested_App"] += 1

            global states_dir
            states_dir = os.path.join(app_dir,"states")

            PrivacyLog_path = os.path.join(AnalysisConfig.OutPut,package,"PrivacyLog.json")
            AppCount_Path = os.path.join(AnalysisConfig.OutPut,package,"AppCount.json")
            NERfinal_path = os.path.join(AnalysisConfig.OutPut,package,"NER_final.json")
            pagefinal_path = os.path.join(AnalysisConfig.OutPut,package,"page_final.json")
            clickdeny_final_path = os.path.join(AnalysisConfig.OutPut,package,"clickdeny_final.json")
            VagueType_path = os.path.join(AnalysisConfig.OutPut,package,"VagueDataType.json")

            get_Existence(Result["Overall"],Result["Existence_Gap"],Result["Quality_Gap_collect_before_notice"],AppCount_Path)
            get_Quality_Element(Result["Overall"],Result["Quality_Gap_Element"],NERfinal_path,pagefinal_path,VagueLabel,Vague_Notice_label)
            get_Quality_Vague(Result["Quality_Gap_Vague_expression"],VagueType_path,VagueLabel,Vague_Notice_label)
            get_Quality_RPN_after_denying_request(Result["Quality_Gap_RPN_after_denying_request"],clickdeny_final_path)
            getTP(PrivacyLog_path)        

    sort(Result)

    print(str(Result))

    json_str = json.dumps(Result, indent=4)
    with open(os.path.join(OPT,"Result.json"), 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    TPCount.output(os.path.join(OPT,"TPCount.json"))


if __name__ == '__main__':
    
    AnalysisConfig.init()
    count = 0

    for package in AnalysisConfig.LogList.keys():
        count +=1
        print(count)
        print("Now processing: "+package)

        if not os.path.exists(os.path.join(AnalysisConfig.OutPut,package)):
             AnalysisConfig.LogError(package,"No Network Log!!!!")
             continue

        if os.path.exists(os.path.join(AnalysisConfig.OutPut,package,"PrivacyLog.json")):
            print("\tAnalysis Done, skipping")
            continue

        # process screenshots and XML files
        NoticeAnalyze.process_states(package,AnalysisConfig.LogList[package])
        print("\tNoticeAnalysis Done")

        # process Api and network log
        LoadPrivacyLog.Analyze(package,AnalysisConfig.LogList[package])
        print("\tExistenceCheck Done")

        SingleAppCount.count(package,AnalysisConfig.LogList[package])
        
    countFinal(AnalysisConfig.Output_path)

        


