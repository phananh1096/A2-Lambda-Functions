import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import datetime
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    #TODO: IMPLEMENT
    print("Going to process query:")
    print("API Event is: ", event)
    logger.debug(event)
    query = event["queryStringParameters"]['q']
    parsed_query = ""
    #test
    # query = "I want to see photos of dogs"

    # Lex disambiguation source: https://stackoverflow.com/questions/52358345/aws-lex-select-query-from-user-question
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='OrderFlowers',
        botAlias='SearchPhotos',
        userId='pa_test',
        inputText=query
    )
    print("Lex Response is: ", response)
    for key_term in response["slots"]:
        val = response["slots"][key_term]
        if val:
            parsed_query += f"+{val}"
    parsed_query = parsed_query[1:]
    print("Extracted Lex query is: ", parsed_query)

    # # Pass parsed query into Search elasticsearch:
    # es_url = "https://search-photos-cvl5kpkrddtvprdzlgtoxrpa7a.us-east-1.es.amazonaws.com/_search?q="
    # print("About to call ES!")
    # search_results = requests.get(es_url+parsed_query, auth=('phananh1096', 'Columbia311096!')).text
    # print("About to convert to json")
    # search_results = json.loads(search_results)
    # print("ES Search results: ", search_results)
    # search_results = search_results['hits']['hits']
    # print("ES Search results are: ", search_results)

    # Updated es search: 
    # Set up ES labels
    host = 'search-photos-cvl5kpkrddtvprdzlgtoxrpa7a.us-east-1.es.amazonaws.com' # For example, my-test-domain.us-east-1.es.amazonaws.com
    try:
        host = os.environ['ESPhotosEndpoint']
    except:
        pass
    
    region = 'us-east-1' 

    print("Setting up credentials..")
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    print("Attempting to start es instance/auth")
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    print("Got some results back from es...")
    search_results = es.search(q=parsed_query)
    print(search_results)

    search_results = search_results['hits']['hits']
    # photo_links = ["https://coms6998-sp21-photobucket.s3.amazonaws.com/img001.jpg"]
    photo_links = set()
    # Iterate over results to get s3? 
    print("Iterate to get links from es results")
    for photo in search_results:
        try:
            source1 = photo["_source"]["bucket"]
            source2 = photo["_source"]["objectKey"]
            link= f"https://{source1}.s3.amazonaws.com/{source2}"
            photo_links.add(link)
        except:
            print("Couldn't append results, skipping")
            continue
    print(json.dumps({"message":"Found some photos!",
                            "Links": list(photo_links)}))
                            
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"message":"Found some photos!",
                            "Links": list(photo_links)}),
    }

# def get_photo_link(photo):
#     s3 = boto3.client('s3')
#     metadata = s3.get_object(
#         Bucket=photo["bucket"],
#         Key=photo["objectKey"],
#     )
#     #Then return link
#     link = ""
#     return link