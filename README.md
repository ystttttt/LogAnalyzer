# LogAnalyzer
## About
LogAnalyzer is a tool that can analyze the compliance of the app runtime privacy notices according to the screenshots, Api logs and network traffic records generated by [AppAutoRuner](https://github.com/ystttttt/AppAutoRunner)

### Reference

## Requirement
1. `Python3`
2. `Pytorch`
3. `Transformers`
4. `numpy`
5. `pytorch-crf 0.7.2`
6. `pygtrans`
7. `langid`
8. `easyocr`
9. `treelib`

## How to use
`LogAnalyze.py` is the main file and `AnalysisConfig.py` is the main configuration file.
- When you use this tool, please modify LogPaths, Outputpath and ErrorLogpath in `AnalysisConfig.py` to the corresponding path in your environment.
  Note that LogPaths can be multiple and LogPaths should be consistent with the Outputpath in [AppAutoRuner](https://github.com/ystttttt/AppAutoRunner)
- Our final models are not included in the repository. Please download models from [Final model]() and place them in the `Model/final_model` directory. 
