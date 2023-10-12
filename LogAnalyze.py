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

def get_Existence(Overall,Existence_Gap,CollectBeforeNotice,logPath):
    if os.path.exists(logPath):
        with open(logPath,'r',encoding='UTF-8')as f:
            count = json.loads(f.read())
        
        if count["privacy_type_collected"]["sum"]!=0: Overall["App_w_privacy_collection_behavior"] +=1
        if count["Existence"]==True : Existence_Gap["App_w_ExistenceGap"] +=1
                    
        Overall["privacy_collection_behavior"] += count["privacy_type_collected"]["sum"]
        Existence_Gap["privacy_collection_behavior_w/o_RPN"] += count["non_existence_all"]["sum"]
                    
        if len(count["collect_before_notice"].keys()) > 1:
            CollectBeforeNotice["App_w_collect_before_notice"] += 1

            for type in count["collect_before_notice"].keys():
                if type == "sum" or type == "cmp" : continue
                if type in CollectBeforeNotice["collect_before_notice_detail_category"].keys():
                    CollectBeforeNotice["collect_before_notice_detail_category"][type] += count["privacy_type_collected"][type]
                else: CollectBeforeNotice["collect_before_notice_detail_category"][type] = count["privacy_type_collected"][type]

        for type in count["privacy_type_collected"].keys():
            if type == "sum" or type == "cmp" : continue
            if type in Overall["privacy_collection_behavior_detail_category"].keys():
                Overall["privacy_collection_behavior_detail_category"][type] += count["privacy_type_collected"][type]
            else: Overall["privacy_collection_behavior_detail_category"][type] = count["privacy_type_collected"][type]

        for type in count["non_existence_all"].keys():
            if type == "sum" or type == "cmp": continue
            if type in Overall["privacy_collection_behavior_w/o_RPN_detail_category"].keys():
                Overall["privacy_collection_behavior_w/o_RPN_detail_category"][type] += count["non_existence_all"][type]
            else: Overall["privacy_collection_behavior_w/o_RPN_detail_category"][type] = count["non_existence_all"][type]

def get_Quality_Element(Overall,QP_Element,logPath,logPath2,VagueLabel,Vague_Notice_label):
    if os.path.exists(logPath):
        Overall["App_w_RPN"] += 1
        with open(logPath2, 'r', encoding='UTF-8')as json_file:
            page_dict = json.loads(json_file.read())

        original_right = QP_Element["Elements_in_RPN"]["Right"]
        original_identity = QP_Element["Elements_in_RPN"]["Identity"]

        for key,value in page_dict.items():
            if not process_clickdeny.check_ifgrantpermission(os.path.join(states_dir,"state_"+key+".txt")):
                key_list = list(value["predict"].keys())
                key_list.sort()
                element_num = len(key_list)
                if element_num == 1 and (key_list[0]=="data" or key_list[0]=="Identity"):
                    continue

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
                        
                if "data" in key_list:
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
                
                if original_right < QP_Element["Elements_in_RPN"]["Right"]:
                    QP_Element["Elements_in_RPN"]["App_w_Right"] += 1
                if original_identity < QP_Element["Elements_in_RPN"]["Identity"]:
                    QP_Element["Elements_in_RPN"]["App_w_Identity"] += 1

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
    
    if(VagueLabel["Vague_identity"]): QP_Vague["identity_vague_expression"]["app"]["app"] +=1
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
            original_num = Result["quality"]["click_deny"]["notice_num"]
            for key,value in clickdeny_dict.items():
                if value["start_timestamp"] in NoticeTime: 
                            if not process_clickdeny.check_ifgrantpermission(os.path.join(states_dir,"state_"+value["start_timestamp"]+".txt")):
                                continue
                        userinput_all = 0
                        permission_all = 0
                        device_all = 0
                        userinput_positive = 0
                        permission_positive = 0
                        device_positive = 0
                        start_data_type = value["start_data_type"]
                        notice_data_type = value["notice_data_type"] 
                        if len(value["notice_key"]) != 0:
                            for datatype in notice_data_type:
                                if (AnalysisConfig.Ontology.is_ancestor("user_input",datatype) or datatype == "user_input") and not AnalysisConfig.Ontology.is_ancestor("user_credentials",datatype):
                                    userinput_positive=1
                                elif AnalysisConfig.Ontology.is_ancestor("permission",datatype) or datatype == "permission":
                                    permission_positive = 1
                                elif datatype != "general_location" and (AnalysisConfig.Ontology.is_ancestor("device_information",datatype) or datatype == "device_information"):
                                    device_positive = 1
                        for datatype in start_data_type:
                            if AnalysisConfig.Ontology.is_ancestor("user_input",datatype) and not AnalysisConfig.Ontology.is_ancestor("user_credentials",datatype):
                                userinput_all = 1
                            elif AnalysisConfig.Ontology.is_ancestor("permission",datatype) or datatype == "permission":
                                permission_all = 1
                            elif datatype != "general_location" and (AnalysisConfig.Ontology.is_ancestor("device_information",datatype) or datatype == "device_information"):
                                device_all = 1
                        Result["quality"]["click_deny"]["userinput_all"]+=userinput_all
                        Result["quality"]["click_deny"]["permission_all"]+=permission_all
                        Result["quality"]["click_deny"]["device_all"]+=device_all
                        Result["quality"]["click_deny"]["notice_num"]+=(userinput_positive|permission_positive|device_positive)
                        Result["quality"]["click_deny"]["userinput_positive"]+=userinput_positive
                        Result["quality"]["click_deny"]["permission_positive"]+=permission_positive
                        Result["quality"]["click_deny"]["device_positive"]+=device_positive
                                
                    if original_num < Result["quality"]["click_deny"]["notice_num"]:
                        Result["quality"]["click_deny"]["app_num"]+=1


def getTP(logPath):
    if os.path.exists(logPath):
        TPCount.app_init()
    with open(logPath,'r') as f:
        Log = json.load(f)
    for key,log in Log.items():
        if key.find("network") != -1:
            if log["third_party"] != "None": TPCount.add(log["timestamp"],log["third_party"],log["data_type"],log["notice"])
            else: TPCount.add_flow(log["timestamp"])

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
        
        NoticeTime = []

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

            get_Existence(Result["Overall"],Result["Existence_Gap"],Result["Existence_Gap_collect_before_notice"],AppCount_Path)
            get_Quality_Element(Result["Overall"],Result["Quality_Gap_Element"],NERfinal_path,pagefinal_path,VagueLabel,Vague_Notice_label)
            get_Quality_Vague(Result["Quality_Gap_Vague_expression"],VagueType_path,VagueLabel,Vague_Notice_label)
            get_Quality_RPN_after_denying_request(Result["Quality_Gap_RPN_after_denying_request"],clickdeny_final_path)
            getTP(PrivacyLog_path)        


    Result["vague"]["Identity_vagueness"]["notice"] = VagueClassifier.Vague_Identity_Notice_Count
    Result["vague"]["Receiver_vagueness"]["notice"] = VagueClassifier.Vague_Receiver_Notice_Count
    Result["vague"]["Purpose_vagueness"]["notice"] = VagueClassifier.Vague_Purpose_Notice_Count

    Result["vague"]["Identity_vagueness"]["detail"] = VagueClassifier.Vague_Identity
    Result["vague"]["Receiver_vagueness"]["detail"] = VagueClassifier.Vague_Receiver
    Result["vague"]["Purpose_vagueness"]["detail"] = VagueClassifier.Vague_Purpose

    Result["existence"]["overall_app_coverage"] = float(Result["existence"]["App_privacy_no_notice"]/Result["App"])
    Result["existence"]["overall_behavior_coverage"] = float(Result["existence"]["privacy_collection_behavior_non_existence"]/Result["existence"]["privacy_collection_behavior"])
    Result["existence"]["TP_network_behavior_coverage"] = float(Result["existence"]["privacy_collection_behavior_non_existence_TP"]/Result["existence"]["privacy_collection_behavior_non_existence_Net"])
    Result["existence"]["collect_before_notice_type_coverage"] = float(Result["existence"]["collect_before_notice_type"]/Result["existence"]["notice_type"])

    for type in Result["existence"]["privacy_collection_data_type"].keys():
        sum = Result["existence"]["privacy_collection_data_type"][type]
        if type in Result["existence"]["non_existence_data_type"].keys():
            Result["existence"]["data_type_coverage"][type] = float(Result["existence"]["non_existence_data_type"][type]/sum)
        else: Result["existence"]["data_type_coverage"][type] = 0.0

        if AnalysisConfig.Ontology.is_ancestor("device_information",type) or type == "device_information":
            Result["existence"]["privacy_collection_behavior_main"]["device_information"] += Result["existence"]["privacy_collection_data_type"][type]
        elif AnalysisConfig.Ontology.is_ancestor("personal_information",type) or type == "personal_information":
            Result["existence"]["privacy_collection_behavior_main"]["personal_information/user_input"] += Result["existence"]["privacy_collection_data_type"][type]
        elif AnalysisConfig.Ontology.is_ancestor("permission",type) or type == "permission":
            Result["existence"]["privacy_collection_behavior_main"]["permission"] += Result["existence"]["privacy_collection_data_type"][type]

    for type in Result["existence"]["non_existence_data_type"].keys():
        if AnalysisConfig.Ontology.is_ancestor("device_information",type) or type == "device_information":
            Result["existence"]["privacy_collection_behavior_non_existence_main"]["device_information"] += Result["existence"]["non_existence_data_type"][type]
        elif AnalysisConfig.Ontology.is_ancestor("personal_information",type) or type == "personal_information":
            Result["existence"]["privacy_collection_behavior_non_existence_main"]["personal_information/user_input"] += Result["existence"]["non_existence_data_type"][type]
        elif AnalysisConfig.Ontology.is_ancestor("permission",type) or type == "personal_information":
            Result["existence"]["privacy_collection_behavior_non_existence_main"]["permission"] += Result["existence"]["non_existence_data_type"][type]

    for type in Result["existence"]["privacy_collection_behavior_non_existence_Net_detail"].keys():
        sum = Result["existence"]["privacy_collection_behavior_non_existence_Net_detail"][type]
        if type in Result["existence"]["privacy_collection_behavior_non_existence_TP_detail"].keys():
            Result["existence"]["TP_data_type_coverage"][type] = float(Result["existence"]["privacy_collection_behavior_non_existence_TP_detail"][type]/sum)
        else: Result["existence"]["TP_data_type_coverage"][type] = 0.0

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

        


