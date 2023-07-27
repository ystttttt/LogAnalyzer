class NERConfig():
    def __init__(self):
        self.output_dir = './Model/model_output_NER'                                                            
        self.bert_path = './Model/configuration/NER'                                     
        self.vocab_file = './Model/configuration/NER/vocab.txt'                                                                                                    
        self.max_seq_length = 256
        self.devpath =  './Model/dataset/'                                                           
        self.trainpath = './Model/dataset/'                                                      
        self.testpath = './Model/dataset/'  
        self.testoutputpath = './Model/dataset/'                                                     
        self.per_gpu_train_batch_size = 64 
        self.n_gpu = 1
        self.local_rank = -1
        self.eval_batch_size  = 64
        self.gradient_accumulation_steps = 1
        self.num_train_epochs = 10
        self.warm_up_ratio = 0.05
        # lr = [5e-5,3e-5,2e-5]
        self.learning_rate = 5e-5
        self.no_cuda = True
        self.logging_steps = 64
        self.save_steps = 64
        self.max_grad_norm = 1
        # dtype = ["train"","test","dev"]
        self.dtype = 'NERtest'
        self.checkpoint = ''
        self.do_lower_case = True
        self.test_batch_size = 64
        
        self.labels = ['O','B-Purpose', 'I-Purpose','B-Right', 'I-Right', 'B-Identity', 'I-Identity','B-Receiver', 'I-Receiver','B-Legal_basis', 'I-Legal_basis','B-Storage','I-Storage','B-data','I-data']
        self.pos = ['CC','CD','DT','EX','FW','IN','JJ','JJR','JJS','LS','MD','NN','NNS','NNP','NNPS','PDT','POS','PRP','PRP$','RB','RBR','RBS','RP','SYM','TO','UH','VB','VBD','VBG','VBN','VBP','VBZ','WDT','WP','WP$','WRB','$',':','']

        self.label2id = {
            "O": 0,
            "B-Purpose": 1,
            "I-Purpose": 2,
            "B-Right": 3,
            'I-Right': 4,
            'B-Identity': 5,
            'I-Identity': 6,
            'B-Receiver': 7,
            'I-Receiver': 8,
            'B-Legal_basis': 9,
            'I-Legal_basis': 10,
            "B-Storage": 11,
            "I-Storage": 12,
            "B-data": 13,
            "I-data": 14
        }


        self.id2label = {_id: _label for _label, _id in list(self.label2id.items())}
        self.num_classes = len(self.label2id)                                                                               
 
