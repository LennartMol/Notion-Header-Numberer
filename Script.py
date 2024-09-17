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

    global main_page_id

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
        main_page_id = search_results["results"][0]["id"]
        print(f"Page ID: {main_page_id}")
    else:
        print(f"Error: {response.status_code}, {response.text}")

def getBlocksFromPage(main_page_id):
    """ Gets the blocks from a page
    """

    global all_blocks

    # Send a GET request to the Notion blocks endpoint
    response = requests.get(f'https://api.notion.com/v1/blocks/{main_page_id}/children', headers=HEADERS)

    # Print the results (for example, to get block IDs)
    if response.status_code == 200:
        blocks = response.json()
        print(json.dumps(blocks, indent=4))  # Print the result in a readable format
        all_blocks = blocks
        

        # if blocks contains the 'has_more' key, it means there are more blocks to fetch
        # retreive 'next_cursor' and make another request with the cursor
        if blocks.get("has_more"):
            getNextBlocksFromPage(main_page_id, blocks.get("next_cursor"))
        else:
            print("All blocks have been fetched")

    else:
        print(f"Error: {response.status_code}, {response.text}")

def getNextBlocksFromPage(main_page_id, next_cursor):
    """ Gets the next blocks from a page
    """

    # Send a GET request to the Notion blocks endpoint
    response = requests.get(f'https://api.notion.com/v1/blocks/{main_page_id}/children', headers=HEADERS, params={"start_cursor": next_cursor})

    # Print the results (for example, to get block IDs)
    if response.status_code == 200:
        blocks = response.json()
        print(json.dumps(blocks, indent=4))  # Print the result in a readable format


        all_blocks["results"] += blocks["results"]
        # if blocks contains the 'has_more' key, it means there are more blocks to fetch
        # retreive 'next_cursor' and make another request with the cursor
        if blocks.get("has_more"):
            getNextBlocksFromPage(main_page_id, blocks.get("next_cursor"))
        else:
            print("All blocks have been fetched")

    else:
        print(f"Error: {response.status_code}, {response.text}")

def getHeadingsFromBlocks():
    # Get all blocks that are of type heading_1, heading_2, heading_3
    # Store them in a dictionary with the block id as key and the text as value
    # Return the dictionary
    
    global all_heading_1_blocks
    all_heading_1_blocks = {}
    global all_heading_2_blocks
    all_heading_2_blocks = {}
    global all_heading_3_blocks
    all_heading_3_blocks = {}

    for block in all_blocks["results"]:
        if block["type"] == "heading_1":
            all_heading_1_blocks[block["id"]] = block["heading_1"]["rich_text"][0]["plain_text"]
        elif block["type"] == "heading_2":
            all_heading_2_blocks[block["id"]] = block["heading_2"]["rich_text"][0]["plain_text"]
        elif block["type"] == "heading_3":
            all_heading_3_blocks[block["id"]] = block["heading_3"]["rich_text"][0]["plain_text"]


    print(all_heading_1_blocks)
    print(all_heading_2_blocks)
    print(all_heading_3_blocks)

     

def main():
    getEnvironmentVariables()
    setHeaders()
    retreivePageIDWithTitle("Onderzoekslogboek")
    getBlocksFromPage(main_page_id)
    getHeadingsFromBlocks()

main()