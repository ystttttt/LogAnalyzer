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

def checkInfo():
    print(AnalysisConfig.ApiInfo)
    print(AnalysisConfig.LogList)
    AnalysisConfig.Ontology.show()


def countFinal(OPT):
    VagueClassifier.init()
    TPCount = ThirdPartyCount.ThirdPartyLog()

    with open(AnalysisConfig.Template,'r',encoding='UTF-8')as f:
        Result = json.loads(f.read())

    for package in AnalysisConfig.LogList.keys():
        print(package)
        app_dir = AnalysisConfig.LogList[package]
        OutPutPath = os.path.join(AnalysisConfig.OutPut,package)

        Vague_Notice_label = set()
        Vague_type = False
        Vague_identity = False
        Vague_receiver = False
        Vague_purpose = False

        Collect_Before_Notice = set()
        NoticeTime = []

        if os.path.exists(OutPutPath):
            Result["App"] += 1

            states_dir = os.path.join(app_dir,"states")
            PrivacyLog_path = os.path.join(AnalysisConfig.OutPut,package,"PrivacyLog.json")
            AppCount_Path = os.path.join(AnalysisConfig.OutPut,package,"AppCount.json")
            NERfinal_path = os.path.join(AnalysisConfig.OutPut,package,"NER_final.json")
            pagefinal_path = os.path.join(AnalysisConfig.OutPut,package,"page_final.json")
            clickdeny_final_path = os.path.join(AnalysisConfig.OutPut,package,"clickdeny_final.json")
            VagueType_path = os.path.join(AnalysisConfig.OutPut,package,"VagueDataType.json")

            if os.path.exists(AppCount_Path):
                with open(AppCount_Path,'r',encoding='UTF-8')as f:
                    count = json.loads(f.read())
                    if count["privacy_type_collected"]["sum"]!=0: Result["existence"]["App_privacy"] +=1

                    if count["Existence"]==True : Result["existence"]["App_privacy_no_notice"] +=1
                    if count["collect_when_start"]!=0 : Result["existence"]["collect_when_start"] +=1

                    Result["existence"]["privacy_collection_behavior"] += count["privacy_type_collected"]["sum"]
                    Result["existence"]["privacy_collection_behavior_non_existence"] += count["non_existence_all"]["sum"]
                    Result["existence"]["privacy_collection_behavior_non_existence_Net"] += count["non_existence_network"]["sum"]
                    Result["existence"]["privacy_collection_behavior_non_existence_TP"] += count["non_existence_third_party"]["sum"]
                    Result["existence"]["privacy_collection_behavior_net"] += count["network_all"]
                    if len(count["collect_before_notice"].keys()) > 1:
                        Result["existence"]["collect_before_notice_app"] += 1

                        for type in count["collect_before_notice"].keys():
                            if type == "sum" or type == "cmp" : continue
                            Collect_Before_Notice.add(type)

                    if len(count["non_existence_network"].keys()) > 1:
                        for type in count["non_existence_network"].keys():
                            if type == "sum" or type == "cmp" : continue
                            if type in Result["existence"]["privacy_collection_behavior_non_existence_Net_detail"].keys():  Result["existence"]["privacy_collection_behavior_non_existence_Net_detail"][type] += 1
                            else: Result["existence"]["privacy_collection_behavior_non_existence_Net_detail"][type] = 1
                    
                    if len(count["non_existence_third_party"].keys()) > 1:
                        for type in count["non_existence_third_party"].keys():
                            if type == "sum" or type == "cmp" : continue
                            if type in Result["existence"]["privacy_collection_behavior_non_existence_TP_detail"].keys():  Result["existence"]["privacy_collection_behavior_non_existence_TP_detail"][type] += 1
                            else: Result["existence"]["privacy_collection_behavior_non_existence_TP_detail"][type] = 1

                    if count["CMP"] : 
                        Result["existence"]["cmp_app"] += 1
                        for cl in count["CMP_class"]:
                            if cl in Result["existence"]["cmp"].keys():  Result["existence"]["cmp"][cl] += 1
                            else: Result["existence"]["cmp"][cl] = 1

                    for type in count["privacy_type_collected"].keys():
                        if type == "sum" or type == "cmp" : continue
                        if type in Result["existence"]["privacy_collection_data_type"].keys():
                            Result["existence"]["privacy_collection_data_type"][type] += count["privacy_type_collected"][type]
                        else: Result["existence"]["privacy_collection_data_type"][type] = count["privacy_type_collected"][type]

                    for type in count["non_existence_all"].keys():
                        if type == "sum" or type == "cmp": continue
                        if type in Result["existence"]["non_existence_data_type"].keys():
                            Result["existence"]["non_existence_data_type"][type] += count["non_existence_all"][type]
                        else: Result["existence"]["non_existence_data_type"][type] = count["non_existence_all"][type]
            
            if os.path.exists(PrivacyLog_path):
                TPCount.app_init()
                with open(PrivacyLog_path,'r') as f:
                    Log = json.load(f)

                    for key,log in Log.items():
                        if key.find("network") != -1:
                            if log["third_party"] != "None": TPCount.add(log["timestamp"],log["third_party"],log["data_type"],log["notice"])
                            else: TPCount.add_flow(log["timestamp"])
        
            

            
            if os.path.exists(VagueType_path):
                Vague_type = True
                Result["vague"]["datatype_vagueness"]["app"] +=1
                with open(VagueType_path, 'r', encoding='UTF-8')as f:
                    vagueType_dict = json.loads(f.read())
                    for key,value in vagueType_dict.items():
                        Vague_Notice_label.add(key.split("++++++++++")[0])
                        Result["vague"]["datatype_vagueness"]["notice"] +=1
                        for label in value:
                            if label in Result["vague"]["datatype_vagueness"]["detail"].keys():
                                Result["vague"]["datatype_vagueness"]["detail"][label]+=1
                            else: Result["vague"]["datatype_vagueness"]["detail"][label] = 1

        
            if os.path.exists(NERfinal_path):
                Result["existence"]["App_notice"] += 1
                with open(pagefinal_path, 'r', encoding='UTF-8')as json_file:
                    page_dict = json.loads(json_file.read())

                notice_type = []
                original_right = Result["quality"]["Right"]
                original_identity = Result["quality"]["Identity"]
                for key, value in page_dict.items():
                    Result["quality"]["total"]+=1
                    if not process_clickdeny.check_ifgrantpermission(os.path.join(states_dir,"state_"+key+".txt")):
                        key_list = list(value["predict"].keys())
                        key_list.sort()
                        element_num = len(key_list)
                        if element_num == 1 and (key_list[0]=="data" or key_list[0]=="Identity"):
                            continue
                        Result["quality"]["valued"]+=1
                        if element_num == 1:
                            Result["quality"]["one_element"]+=1
                        elif element_num == 2:
                            Result["quality"]["two_elements"]+=1
                        elif element_num == 3:
                            Result["quality"]["three_elements"]+=1
                        elif element_num == 4:
                            Result["quality"]["four_elements"]+=1
                        elif element_num == 5:
                            Result["quality"]["five_elements"]+=1
                        elif element_num == 6:
                            Result["quality"]["six_elements"]+=1
                        elif element_num == 7:
                            Result["quality"]["seven_elements"]+=1
                        if "data" in key_list:
                            lista = ["Purpose","Right","Legal_basis","Receiver","Storage"]
                            flag = 0
                            flag_p = 0
                            for a in lista:
                                if a in key_list :
                                    if a == "Purpose": flag_p = 1
                                    else: flag = 1            
                            if flag == 0 and flag_p == 0:
                                Result["quality"]["onlydata"]+=1
                            elif flag == 0 and flag_p == 1:
                                Result["quality"]["data_purpose"]+=1
                        for label in key_list:
                            Result["quality"][label]+=1
                            if label == "Identity":
                                if(VagueClassifier.classify_Identity(value["predict"][label])):
                                    Vague_identity = True
                                    Vague_Notice_label.add(key)
                            elif label == "Receiver":
                                if(VagueClassifier.classify_Receiver(value["predict"][label])):
                                    Vague_receiver = True
                                    Vague_Notice_label.add(key)
                            elif label == "Purpose":
                                if(VagueClassifier.classify_Purpose(value["predict"][label])):
                                    Vague_purpose = True
                                    Vague_Notice_label.add(key)
                        if "data_type" in value.keys():
                            notice_type.extend(value["data_type"])
                if original_right < Result["quality"]["Right"]:
                    Result["quality"]["Right_app"] += 1
                if original_identity < Result["quality"]["Identity"]:
                    Result["quality"]["Identity_app"] += 1

                notice_type = list(set(notice_type))
                Result["existence"]["notice_type"] += len(notice_type)
                for type in notice_type:
                    CBN = False
                    for t in Collect_Before_Notice:
                        if AnalysisConfig.Ontology.is_ancestor(type,t) or type == t:
                            Result["existence"]["collect_before_notice_type"] += 1
                            CBN = True
                            break
                    if AnalysisConfig.Ontology.is_ancestor("device_information",type) or type == "device_information":
                        Result["existence"]["notice_type_main"]["device_information"] += 1
                        if CBN : Result["existence"]["collect_before_notice_main"]["device_information"] += 1
                    elif AnalysisConfig.Ontology.is_ancestor("personal_information",type) or type == "personal_information":
                        Result["existence"]["notice_type_main"]["personal_information/user_input"] += 1
                        if CBN : Result["existence"]["collect_before_notice_main"]["personal_information/user_input"] += 1
                    elif AnalysisConfig.Ontology.is_ancestor("permission",type) or type == "permission":
                        Result["existence"]["notice_type_main"]["permission"] += 1
                        if CBN : Result["existence"]["collect_before_notice_main"]["permission"] += 1
                            
            if os.path.exists(clickdeny_final_path):
                with open(clickdeny_final_path, 'r', encoding='UTF-8')as f:
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

        if(Vague_identity): Result["vague"]["Identity_vagueness"]["app"] +=1
        if(Vague_receiver): Result["vague"]["Receiver_vagueness"]["app"] +=1
        if(Vague_purpose): Result["vague"]["Purpose_vagueness"]["app"] +=1

        if(Vague_type|Vague_identity|Vague_receiver|Vague_purpose):  Result["vague"]["app_num"] +=1
        Result["vague"]["notice_num"] += len(Vague_Notice_label)


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

        


