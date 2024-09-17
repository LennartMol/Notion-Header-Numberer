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
    # Get all blocks that are of type heading_1
    # Store the position of the block in the all_heading_1_blocks dictionary with the key being the position of the block and the value being the text of the block heading
    
    global all_heading_1_blocks
    all_heading_1_blocks = {}

    for block in all_blocks["results"]:
        if block["type"] == "heading_1":
            all_heading_1_blocks[all_blocks["results"].index(block)] = block["heading_1"]["rich_text"][0]["plain_text"]
    
    print(all_heading_1_blocks)

    #TODO implement a way to get the blocks that are under the heading_1 blocks (search for 1st occurence of a synced block)


def renumberAndUpdateHeading1Blocks():
    """ Renumber the heading_1 blocks and update the blocks with the new values
    """


    # Change the value of all_heading_1_blocks by removing the numbers in front of the heading
    for key in all_heading_1_blocks:
        all_heading_1_blocks[key] = all_heading_1_blocks[key].split(" ", 1)[1]

    print(all_heading_1_blocks)

    # Renumber the text values of all_heading_1_blocks 
    # for example {85: 'Inleiding'} becomes {85: '1 Inleiding'}, adding '1 ' in front of the text
    chapter = 1
    for key in all_heading_1_blocks:
        all_heading_1_blocks[key] = f"{chapter} {all_heading_1_blocks[key]}"  
        chapter = chapter + 1  
    
    print(all_heading_1_blocks)

    for key in all_heading_1_blocks:
        # update the blocks with the new values
        updateHeading1Block(key, all_heading_1_blocks[key])

def updateHeading1Block(block_key, newHeading1Value):
    """ Updates a block with a new value
    """

    # retreive block data from all_blocks with block_key
    block = all_blocks["results"][block_key]
    print(block)
    # use block data to send a PATCH request to the Notion blocks endpoint, only updating the 'plain_text' value to newHeadingValue
    # example from block[85]: {'object': 'block', 'id': '8994839b-782b-4f8d-afa8-3118539119e1', 'parent': {'type': 'page_id', 'page_id': '673e1892-3d00-467d-a4f8-010301092f9d'}, 'created_time': '2024-09-09T13:03:00.000Z', 'last_edited_time': '2024-09-17T11:42:00.000Z', 'created_by': {'object': 'user', 'id': '45f88c9c-b81b-453f-8ccb-5209de4bedd0'}, 'last_edited_by': {'object': 'user', 'id': '45f88c9c-b81b-453f-8ccb-5209de4bedd0'}, 'has_children': False, 'archived': False, 'in_trash': False, 'type': 'heading_1', 'heading_1': {'rich_text': [{'type': 'text', 'text': {'content': '2 Inleiding', 'link': None}, 'annotations': {'bold': False, 'italic': False, 'strikethrough': False, 'underline': False, 'code': False, 'color': 'default'}, 'plain_text': '2 Inleiding', 'href': None}], 'is_toggleable': False, 'color': 'default'}}

    data = {
        "heading_1": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": newHeading1Value,
                        "link": None
                    },
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default"
                    },
                    "plain_text": newHeading1Value,
                    "href": None
                }
            ],
            "is_toggleable": False,
            "color": "default"
        }
    }

    response = requests.patch(f'https://api.notion.com/v1/blocks/{block["id"]}', headers=HEADERS, data=json.dumps(data))
    if response.status_code == 200:
        print(f"Block {block_key} updated")
    else:
        print(f"Error: {response.status_code}, {response.text}")

def main():
    getEnvironmentVariables()
    setHeaders()
    retreivePageIDWithTitle("Onderzoekslogboek")
    getBlocksFromPage(main_page_id)
    getHeadingsFromBlocks()
    renumberAndUpdateHeading1Blocks()

main()