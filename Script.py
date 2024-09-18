import os
import requests
import json
import re
import logging
logger = logging.getLogger(__name__)

def getEnvironmentVariables():
    """ Gets environment variables and sets them in global variables
    """

    global NOTION_API_KEY
    NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
    if NOTION_API_KEY == None:
        logger.error(f"Make sure to correctly set your environment variables.")
        exit()
    logger.debug(f"Retreived NOTION_API_KEY: {NOTION_API_KEY}")

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

        # Get the page ID of the first result
        main_page_id = search_results["results"][0]["id"]
        logger.debug(f"Page ID: {main_page_id}")
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def getBlocksFromPage(main_page_id):
    """ Gets the blocks from a page
    """

    global all_blocks

    # Send a GET request to the Notion blocks endpoint
    response = requests.get(f'https://api.notion.com/v1/blocks/{main_page_id}/children', headers=HEADERS)

    # Print the results (for example, to get block IDs)
    if response.status_code == 200:
        blocks = response.json()
        all_blocks = blocks
        

        # if blocks contains the 'has_more' key, it means there are more blocks to fetch
        # retreive 'next_cursor' and make another request with the cursor
        if blocks.get("has_more"):
            getNextBlocksFromPage(main_page_id, blocks.get("next_cursor"))
            logger.debug(f"There are more blocks to fetch")
            logger.debug(f"Next cursor: {blocks.get('next_cursor')}")
        else:
            logger.debug(f"All blocks have been fetched")

    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def getNextBlocksFromPage(main_page_id, next_cursor):
    """ Gets the next blocks from a page
    """

    # Send a GET request to the Notion blocks endpoint
    response = requests.get(f'https://api.notion.com/v1/blocks/{main_page_id}/children', headers=HEADERS, params={"start_cursor": next_cursor})

    # Print the results (for example, to get block IDs)
    if response.status_code == 200:
        blocks = response.json()


        all_blocks["results"] += blocks["results"]
        # if blocks contains the 'has_more' key, it means there are more blocks to fetch
        # retreive 'next_cursor' and make another request with the cursor
        if blocks.get("has_more"):
            getNextBlocksFromPage(main_page_id, blocks.get("next_cursor"))
            logger.debug(f"There are more blocks to fetch")
            logger.debug(f"Next cursor: {blocks.get('next_cursor')}")
        else:
            logger.debug(f"All blocks have been fetched")

    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def getHeadingsFromBlocks():
    # Get all blocks that are of type heading_1
    # Store the position of the block in the all_heading_1_blocks dictionary with the key being the position of the block and the value being the text of the block heading
    
    global all_heading_1_blocks
    all_heading_1_blocks = {}

    for block in all_blocks["results"]:
        if block["type"] == "heading_1":
            all_heading_1_blocks[all_blocks["results"].index(block)] = block["heading_1"]["rich_text"][0]["plain_text"]

    logger.debug(f"\nAll heading 1 blocks: \n{json.dumps(all_heading_1_blocks, indent=4)}")


def renumberAndUpdateHeading1Blocks():
    """ Renumber the heading_1 blocks and update the blocks with the new values
    """
    global new_all_heading_1_blocks
    new_all_heading_1_blocks = {}

    # Change the value of all_heading_1_blocks by removing the numbers in front of the heading
    for key in all_heading_1_blocks:
        new_all_heading_1_blocks[key] = all_heading_1_blocks[key].split(" ", 1)[1]

    logger.debug(f"\nStripped heading 1 blocks: \n{json.dumps(new_all_heading_1_blocks, indent=4)}")
    
    # Renumber the text values of all_heading_1_blocks 
    # for example {85: 'Inleiding'} becomes {85: '1 Inleiding'}, adding '1 ' in front of the text
    chapter = 1
    for key in new_all_heading_1_blocks:
        new_all_heading_1_blocks[key] = f"{chapter} {new_all_heading_1_blocks[key]}"  
        chapter = chapter + 1  

    logger.debug(f"\nRenumbered heading 1 blocks: \n{json.dumps(new_all_heading_1_blocks, indent=4)}")

    for key in new_all_heading_1_blocks:
        # check if the new value is different from the old value
        if new_all_heading_1_blocks[key] != all_heading_1_blocks[key]:
            # if the new value is different from the old value, update the block with the new value
            updateHeading1Block(key, new_all_heading_1_blocks[key])
        else: 
            logger.info(f"Heading 1: '{all_heading_1_blocks[key]}' has not been changed.")

def updateHeading1Block(block_key, newHeading1Value):
    """ Updates a block with a new value
    """

    # retreive block data from all_blocks with block_key
    block = all_blocks["results"][block_key]
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
        logger.info(f"Heading 1: '{all_heading_1_blocks[block_key]}' has been changed to '{newHeading1Value}'")
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def getSyncedBlockPageID():
    """ Get the page ID of the synced block
    """
    # use all_heading_1_blocks to get the position of the synced block
    # search for the first occurence of a synced block under the heading_1 block key in all_blocks
    # return the page ID of the synced block

    # create dictionary to link the synced block page ID to the heading_1 block key

    global synced_block_page_id
    synced_block_page_id = {}


    for key in new_all_heading_1_blocks:
        for block in all_blocks["results"]:
            if block["type"] == "synced_block" and all_blocks["results"].index(block) > key:
                # print index of synced block
                logger.debug(f"Synced block index: {all_blocks['results'].index(block)}")
                synced_block_page_id[key] = block["synced_block"]["synced_from"]["block_id"]
                break

def getAllSyncedBlockContent():
    """ Get the content of all synced blocks
    """

    for key in synced_block_page_id:
        getSyncedBlockContent(key)

                
def getSyncedBlockContent(key, next_cursor=None):
    """ Get the content of the synced block
    """

    global synced_block_data

    # use synced_block_page_id to get the content of the synced block
    # send a GET request to the Notion blocks endpoint with the synced block page ID
    # print the content of the synced block

    response = requests.get(f'https://api.notion.com/v1/blocks/{synced_block_page_id[key]}/children', headers=HEADERS, params={"start_cursor": next_cursor})
    if response.status_code == 200:
        
        response_data = response.json()

        if (next_cursor == None):
            synced_block_data = response_data
        else:
            synced_block_data["results"] += response_data["results"]

        if response_data.get("has_more"):
            getSyncedBlockContent(key, response_data.get("next_cursor"))
            logger.debug(f"There are more blocks to fetch")
            logger.debug(f"Next cursor: {response_data.get('next_cursor')}")
        else:
            logger.debug(f"All blocks have been fetched")
            getSyncedBlockHeaders(key)
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def getSyncedBlockHeaders(key):
    """ Get the headers of the synced block
    """

    global synced_block_headers2
    synced_block_headers2 = {}
    global synced_block_headers3
    synced_block_headers3 = {}
    
    for block in synced_block_data["results"]:
        if block["type"] == "heading_2":
            synced_block_headers2[synced_block_data["results"].index(block)] = block["heading_2"]["rich_text"][0]["plain_text"]
        if block["type"] == "heading_3":
            synced_block_headers3[synced_block_data["results"].index(block)] = block["heading_3"]["rich_text"][0]["plain_text"]

    logger.debug(f"\nAll heading 2 blocks: \n{json.dumps(synced_block_headers2, indent=4)}")
    logger.debug(f"\nAll heading 3 blocks: \n{json.dumps(synced_block_headers3, indent=4)}")
    
    renumberAndUpdateHeading2And3Blocks(key)

def renumberAndUpdateHeading2And3Blocks(important_key):
    """ 
    Renumber the heading_2 blocks and heading_3 blocks and update the blocks with the new values
    """
    global remove_chapter_number_pattern
    remove_chapter_number_pattern = r'^\d+(\.\d+)*\s*'

    global new_synched_block_headers2
    new_synched_block_headers2 = {}
    global new_synched_block_headers3
    new_synched_block_headers3 = {}

    # Remove old chapter numbers from both synced_block_headers2 (Heading 2) and synced_block_headers3 (Heading 3)
    for key in synced_block_headers2:
        new_synched_block_headers2[key] = re.sub(remove_chapter_number_pattern, '', synced_block_headers2[key])

    for key in synced_block_headers3:
        new_synched_block_headers3[key] = re.sub(remove_chapter_number_pattern, '', synced_block_headers3[key])

    logger.debug(f"\nStripped heading 2 blocks: \n{json.dumps(new_synched_block_headers2, indent=4)}")
    logger.debug(f"\nStripped heading 3 blocks: \n{json.dumps(new_synched_block_headers3, indent=4)}")

    # Retrieve the chapter number from the heading_1 block
    chapter = int(new_all_heading_1_blocks[important_key].split(" ", 1)[0])

    # Renumber the Heading 2 blocks
    subchapter = 1
    for key in sorted(new_synched_block_headers2.keys()):  # Sort by block keys for consistency
        new_synched_block_headers2[key] = f"{chapter}.{subchapter} {new_synched_block_headers2[key]}"  
        subchapter = subchapter + 1

    logger.debug(f"\nRenumbered heading 2 blocks: \n{json.dumps(new_synched_block_headers2, indent=4)}")

    # Renumber the Heading 3 blocks based on the closest Heading 2 block
    sorted_heading2_keys = sorted(synced_block_headers2.keys())
    subsubchapter_count = {key: 1 for key in sorted_heading2_keys}  # To track subsubchapters under each Heading 2 block

    for key in sorted(new_synched_block_headers3.keys()):  # Sort Heading 3 blocks by their block IDs
        # Find the closest Heading 2 block key that is <= the current Heading 3 block key
        closest_heading2_key = max([k for k in sorted_heading2_keys if k <= key], default=None)

        if closest_heading2_key is not None:
            # Build the new number using the corresponding Heading 2's chapter number
            heading2_number = new_synched_block_headers2[closest_heading2_key].split(" ", 1)[0]
            subsubchapter = subsubchapter_count[closest_heading2_key]  # Get current subsubchapter count for this Heading 2
            new_synched_block_headers3[key] = f"{heading2_number}.{subsubchapter} {new_synched_block_headers3[key]}"

            # Increment the subsubchapter count for this Heading 2 block
            subsubchapter_count[closest_heading2_key] += 1 

    logger.debug(f"\nRenumbered heading 3 blocks: \n{json.dumps(new_synched_block_headers3, indent=4)}")

    updateSyncedBlockHeaders()

def updateSyncedBlockHeaders():
    """ Update the synced block headers
    """

    for key in new_synched_block_headers2:
        # check if the new value is different from the old value
        if new_synched_block_headers2[key] != synced_block_headers2[key]:
            # if the new value is different from the old value, update the block with the new value
            updateSyncedBlockHeading2(key, new_synched_block_headers2[key])
        else: 
            logger.info(f"Heading 2: '{synced_block_headers2[key]}' has not been changed.")

    for key in new_synched_block_headers3:
        # check if the new value is different from the old value
        if new_synched_block_headers3[key] != synced_block_headers3[key]:
            # if the new value is different from the old value, update the block with the new value
            updateSyncedBlockHeading3(key, new_synched_block_headers3[key])
        else: 
            logger.info(f"Heading 3: '{synced_block_headers3[key]}' has not been changed.")

def updateSyncedBlockHeading2(block_key, newHeading2Value):
    """ Update the synced block heading 2
    """
    
    # Retrieve the block data from synced_block_data with block_key
    block = synced_block_data["results"][block_key]

    # Use the block data to send a PATCH request to the Notion blocks endpoint, only updating the 'plain_text' value to newHeadingValue
    data = {
        "heading_2": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": newHeading2Value,
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
                    "plain_text": newHeading2Value,
                    "href": None
                }
            ],
            "is_toggleable": False,
            "color": "default"
        }
    }

    response = requests.patch(f'https://api.notion.com/v1/blocks/{block["id"]}', headers=HEADERS, data=json.dumps(data))
    if response.status_code == 200:
        logger.info(f"Heading 2: '{synced_block_headers2[block_key]}' has been changed to '{newHeading2Value}'")
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def updateSyncedBlockHeading3(block_key, newHeading3Value):
    """ Update the synced block heading 3
    """

    # Retrieve the block data from synced_block_data with block_key
    block = synced_block_data["results"][block_key]

    # Use the block data to send a PATCH request to the Notion blocks endpoint, only updating the 'plain_text' value to newHeadingValue
    data = {
        "heading_3": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": newHeading3Value,
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
                    "plain_text": newHeading3Value,
                    "href": None
                }
            ],
            "is_toggleable": False,
            "color": "default"
        }
    }

    response = requests.patch(f'https://api.notion.com/v1/blocks/{block["id"]}', headers=HEADERS, data=json.dumps(data))
    if response.status_code == 200:
        logger.info(f"Heading 3: '{synced_block_headers3[block_key]}' has been changed to '{newHeading3Value}'")
    else:
        logger.error(f"Error: {response.status_code}, {response.text}")

def main():
    logging.basicConfig(level=logging.DEBUG)
    
    getEnvironmentVariables()
    setHeaders()
    retreivePageIDWithTitle("Onderzoekslogboek")
    getBlocksFromPage(main_page_id)
    getHeadingsFromBlocks()
    renumberAndUpdateHeading1Blocks()
    getSyncedBlockPageID()
    getAllSyncedBlockContent()

main()