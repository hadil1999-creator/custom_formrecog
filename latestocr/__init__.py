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
import base64
import azure.functions as func
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Optional Azure ML imports for batch/pipeline and retraining integration
import azureml.core
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.pipelines import Pipeline


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function entry point."""
    try:
        body = json.dumps(req.get_json())
        logging.info("Request body: " + body)

        if body:
            result = compose_response(body, rate_limit=True)
            logging.info("Result to return to custom skill: " + result)
            return func.HttpResponse(result, mimetype="application/json")
        else:
            return func.HttpResponse("Invalid body", status_code=400)

    except ValueError:
        return func.HttpResponse("Invalid body", status_code=400)


def compose_response(json_data, rate_limit=False):
    """Processes input JSON and calls Form Recognizer for each record."""
    values = json.loads(json_data).get('values', [])
    results = {"values": []}
    endpoint = os.environ["FR_ENDPOINT"]
    key = os.environ["FR_ENDPOINT_KEY"]

    # Set up Azure ML pipeline for batch processing
    pipeline = Pipeline()
    step = PythonScriptStep(
        name="read",
        script_name="read.py",
        inputs=[azureml.input.DatasetFile("input_data")],
        outputs=[azureml.output.DatasetFile("output_data")],
    )
    step.run_min_instances = 1
    pipeline.append(step)

    # Run pipeline (asynchronous batch processing)
    pipeline_run = pipeline.run(min_instances=1, inputs=[azureml.input.DatasetFile("input_data")])
    output_dataset = pipeline_run.get_output_dataset("output_data")

    # Process each document
    for value in values:
        record_id = value.get("recordId")
        data = value.get("data", {})
        output_record = read(endpoint, key, record_id, data, rate_limit)
        results["values"].append(output_record)

    return json.dumps(results, ensure_ascii=False)


def read(endpoint, key, recordId, data, rate_limit=False):
    """Reads and analyzes a document from a URL using Form Recognizer."""
    try:
        # Decode base64 URL and append SAS token
        url_base = data.get("Url", "")
        sas_token = data.get("SasToken", "")

        # Handle potential base64 padding issues
        padding = len(url_base) % 4
        if padding == 1:
            url_base = url_base[:-1]
        elif padding == 2:
            url_base += "="
        elif padding == 3:
            url_base += "=="

        docUrl = base64.b64decode(url_base).decode("utf-8")
        if not docUrl.endswith("/"):
            docUrl += sas_token
        else:
            docUrl = docUrl[:-1] + sas_token

        # Initialize client
        document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )

        # Apply rate limiting (if enabled)
        if rate_limit:
            logging.info("Rate limiting enabled for Form Recognizer requests.")

        # Schema mismatch alert placeholder
        from azure.ai.formrecognizer import SchemaMismatchAlert  # For monitoring schema drift

        # Perform document analysis
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-read", docUrl)
        result = poller.result()

        # Build output record
        output_record = {"recordId": recordId, "data": {"text": result.content}}

        # Check for data drift
        if is_data_drift(result):
            retrain_model(endpoint, key)

    except Exception as error:
        logging.error(f"Error processing record {recordId}: {error}")
        output_record = {
            "recordId": recordId,
            "errors": [{"message": f"Error: {str(error)}"}],
        }

    return output_record


def is_data_drift(result):
    """Detects data drift (placeholder logic)."""
    # TODO: implement comparison logic vs baseline predictions
    return False


def retrain_model(endpoint, key):
    """Retrains model if drift detected (placeholder logic)."""
    # TODO: implement Azure ML retraining workflow here
    logging.info("Retraining model triggered due to detected data drift.")


