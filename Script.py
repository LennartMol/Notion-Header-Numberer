import time
import os
import requests
import json

def getEnvironmentVariables():
    """ Gets environment variables and sets them in global variables
    """

    global NOTION_API_KEY
    NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
    if NOTION_API_KEY == None:
        print(f"\nMake sure to correctly set your environment variables.\n")
        exit()

def setHeaders():
    """ Sets headers for the API request
    """
    getEnvironmentVariables()

    notion_latest_api_version = "2022-06-28"

    global HEADERS

    HEADERS = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": notion_latest_api_version,
        "Content-Type": "application/json"
    }

def retreivePageIDWithTitle(title):
    """ Retreives the page ID of a page with a given title
    """
    setHeaders()

    # Define the search payload
    data = {
        "query": title
    }

    # Send a POST request to the Notion search endpoint
    response = requests.post('https://api.notion.com/v1/search', headers=HEADERS, data=json.dumps(data))

    # Print the results (for example, to get page IDs)
    if response.status_code == 200:
        search_results = response.json()
        print(json.dumps(search_results, indent=4))  # Print the result in a readable format

        # Get the page ID of the first result
        page_id = search_results["results"][0]["id"]
        print(f"Page ID: {page_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")

retreivePageIDWithTitle("Onderzoekslogboek")