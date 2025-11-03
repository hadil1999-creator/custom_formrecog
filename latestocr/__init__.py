"""import logging
import json
import os
import logging
from json import JSONEncoder
import os
import azure.functions as func
import base64
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = json.dumps(req.get_json())
        logging.info("body: " + body)
        if body:
            result = compose_response(body)
            logging.info("Result to return to custom skill: " + result)
            return func.HttpResponse(result, mimetype="application/json")
        else:
            return func.HttpResponse(
                "Invalid body",
                status_code=400
            )
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def compose_response(json_data):
    values = json.loads(json_data)['values']
    # Prepare the Output before the loop
    results = {}
    results["values"] = []
    endpoint = os.environ["FR_ENDPOINT"]
    key = os.environ["FR_ENDPOINT_KEY"]
    for value in values:
        output_record = read(endpoint=endpoint, key=key, recordId=value["recordId"], data=value["data"])
        results["values"].append(output_record)
    return json.dumps(results, ensure_ascii=False)

def read(endpoint, key, recordId, data):
    try:
        #base64 padding can be tricky when coming from Java. check if length is divisible by 4, add to make it multiple of 4
        #logging.info("b64 docUrl: " + data["Url"])
        if len(data["Url"]) % 4 == 0:
            docUrl = base64.b64decode(data["Url"]).decode('utf-8')[:-1] + data["SasToken"]
        elif len(data["Url"]) % 4 == 1:
            docUrl = base64.b64decode(data["Url"][:-1]).decode('utf-8') + data["SasToken"]
        elif len(data["Url"]) % 4 == 2:
            docUrl = base64.b64decode(data["Url"]+"=").decode('utf-8') + data["SasToken"]
        elif len(data["Url"]) % 4 == 3:
            docUrl = base64.b64decode(data["Url"]+"==").decode('utf-8')[:-1]+ data["SasToken"]
        document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-read", docUrl)
        result = poller.result()
        output_record = {
            "recordId": recordId,
            "data": {"text": result.content}
        }

    except Exception as error:
        output_record = {
            "recordId": recordId,
            "errors": [ { "message": "Error: " + str(error) }   ] 
        }
    #logging.info("Output record: " + json.dumps(output_record, ensure_ascii=False))
    return output_record

    """

import logging
import json
import os
import azure.functions as func
import base64
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azureml.core import Workspace
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.pipelines import Pipeline
from azureml.core import Workspace
ws = Workspace.from_config()
pipeline = Pipeline(workspace=ws, steps=[])


# Define step for processing data in batches
step = PythonScriptStep(
    name="read",
    script_name="read.py",  # assumes a file named 'read.py' containing the read function
    inputs=[azureml.input.DatasetFile("input_data")],  # input dataset
    outputs=[azureml.output.DatasetFile("output_data")],  # output dataset
)

step.run_min_instances = 1  # Set the minimum number of instances to run in parallel

# Add the step to the pipeline
pipeline.append(step)

# Define a function to process data in batches using the pipeline
def compose_response(json_data):
    values = json.loads(json_data)['values']
    results = {}
    results["values"] = []
    endpoint = os.environ["FR_ENDPOINT"]
    key = os.environ["FR_ENDPOINT_KEY"]
    
    # Create an instance of the pipeline and run it on the input data
    pipeline_run = pipeline.run(min_instances=1, inputs=[azureml.input.DatasetFile("input_data")])
    output_dataset = pipeline_run.get_output_dataset("output_data")
    
    for value in values:
        output_record = read(endpoint=endpoint, key=key, recordId=value["recordId"], data=value["data"])
        results["values"].append(output_record)
    
    return json.dumps(results, ensure_ascii=False)

def read(endpoint, key, recordId, data):
    try:
        if len(data["Url"]) % 4 == 0:
            docUrl = base64.b64decode(data["Url"]).decode('utf-8')[:-1] + data["SasToken"]
        elif len(data["Url"]) % 4 == 1:
            docUrl = base64.b64decode(data["Url"][:-1]).decode('utf-8') + data["SasToken"]
        elif len(data["Url"]) % 4 == 2:
            docUrl = base64.b64decode(data["Url"]+"=").decode('utf-8') + data["SasToken"]
        elif len(data["Url"]) % 4 == 3:
            docUrl = base64.b64decode(data["Url"]+"==").decode('utf-8')[:-1]+ data["SasToken"]
        document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-read", docUrl)
        result = poller.result()
        output_record = {
            "recordId": recordId,
            "data": {"text": result.content}
        }
    except Exception as error:
        output_record = {
            "recordId": recordId,
            "errors": [ { "message": "Error: " + str(error) }   ] 
        }
    return output_record
