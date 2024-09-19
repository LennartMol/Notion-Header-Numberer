import os
import requests
import aiohttp
import asyncio
import json
import re
import logging
logger = logging.getLogger(__name__)

global all_synced_blocks 
all_synced_blocks = []
global all_old_synced_block_headers2
all_old_synced_block_headers2 = []
global all_old_synced_block_headers3
all_old_synced_block_headers3 = []
global all_new_synced_block_headers2
all_new_synced_block_headers2 = []
global all_new_synced_block_headers3
all_new_synced_block_headers3 = []

MAX_RETRIES = 5  # Maximum number of retries
RETRY_DELAY = 2  # Initial delay between retries in seconds

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

def getBlocksFromPage(main_page_id, cursor=None):
    """ Gets the blocks from a page
    """
    global all_blocks

    # Send a GET request to the Notion blocks endpoint
    response = requests.get(f'https://api.notion.com/v1/blocks/{main_page_id}/children', headers=HEADERS, params={"start_cursor": cursor})

    # Print the results (for example, to get block IDs)
    if response.status_code == 200:
        response_data = response.json()
        
        if (cursor == None):
            all_blocks = response_data
        else:
            all_blocks["results"] += response_data["results"]
        
        # if blocks contains the 'has_more' key, it means there are more blocks to fetch
        # retreive 'next_cursor' and make another request with the cursor
        if response_data.get("has_more"):
            getBlocksFromPage(main_page_id, response_data.get("next_cursor"))
            logger.debug(f"There are more blocks to fetch")
            logger.debug(f"Next cursor: {response_data.get('next_cursor')}")
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


def renumberHeading1Blocks():
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

async def sendRequestToUpdateHeadingBlock(block_key, newHeadingValue, oldHeadingValue, headingNumber, indexSyncedBlock=None):
    """ Updates a block with a new value and retries if a conflict error (409) occurs """

    # Retrieve block data from all_blocks with block_key
    if headingNumber == 1:
        block = all_blocks["results"][block_key]
    else:
        block = all_synced_blocks[indexSyncedBlock]["results"][block_key]

    heading_number = f"heading_{headingNumber}"  # heading_1, heading_2, heading_3, etc.

    data = {
        heading_number: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": newHeadingValue,
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
                    "plain_text": newHeadingValue,
                    "href": None
                }
            ],
            "is_toggleable": False,
            "color": "default"
        }
    }

    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Send PATCH request using aiohttp for async requests
            async with aiohttp.ClientSession() as session:
                async with session.patch(f'https://api.notion.com/v1/blocks/{block["id"]}', headers=HEADERS, data=json.dumps(data)) as response:
                    if response.status == 200:
                        logger.info(f"Heading {headingNumber}: '{oldHeadingValue}' has been changed to '{newHeadingValue}'")
                        return
                    elif response.status == 409:
                        # Conflict error, retry with backoff
                        logger.warning(f"Conflict error: {response.status}. Retrying {retries + 1}/{MAX_RETRIES}...")
                        retries += 1
                        await asyncio.sleep(RETRY_DELAY * retries)  # Exponential backoff
                    else:
                        # Log other errors and break the loop
                        error_message = await response.text()
                        logger.error(f"Error: {response.status}, {error_message}")
                        break
        except aiohttp.ClientError as e:
            # Catch any client-related errors (network issues, etc.)
            logger.error(f"Request failed due to client error: {e}")
            retries += 1
            await asyncio.sleep(RETRY_DELAY * retries)  # Retry after backoff

    logger.error(f"Failed to update block '{block['id']}' after {MAX_RETRIES} retries.")

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
            all_synced_blocks.append(synced_block_data)
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

    all_old_synced_block_headers2.append(synced_block_headers2)
    all_old_synced_block_headers3.append(synced_block_headers3)

    logger.debug(f"\nAll heading 2 blocks: \n{json.dumps(synced_block_headers2, indent=4)}")
    logger.debug(f"\nAll heading 3 blocks: \n{json.dumps(synced_block_headers3, indent=4)}")
    
    renumberHeading2And3Blocks(key)

def renumberHeading2And3Blocks(important_key):
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

    all_new_synced_block_headers2.append(new_synched_block_headers2)
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

    all_new_synced_block_headers3.append(new_synched_block_headers3)
    logger.debug(f"\nRenumbered heading 3 blocks: \n{json.dumps(new_synched_block_headers3, indent=4)}")

async def updateAllHeaders():
    """ Update the headers asynchronously if they have changed """
    
    async def check_and_update_blocks(blocks, new_blocks, old_blocks, heading_number, index_synced_block=None):
        """ Helper function to check if a block's heading value has changed and update if necessary """
        tasks = []
        for key in new_blocks:
            # check if the new value is different from the old value
            if new_blocks[key] != old_blocks[key]:
                # add the task to update the block with the new value
                tasks.append(sendRequestToUpdateHeadingBlock(
                    block_key=key,
                    newHeadingValue=new_blocks[key],
                    oldHeadingValue=old_blocks[key],
                    headingNumber=heading_number,
                    indexSyncedBlock=index_synced_block
                ))
            else: 
                logger.info(f"Heading {heading_number}: '{old_blocks[key]}' has not been changed.")
        if tasks:
            await asyncio.gather(*tasks)  # Run all tasks concurrently

    # Update heading 1 blocks
    await check_and_update_blocks(
        all_heading_1_blocks, 
        new_all_heading_1_blocks, 
        all_heading_1_blocks, 
        heading_number=1
    )
    
    # Update heading 2 blocks
    for index in range(len(all_new_synced_block_headers2)):
        await check_and_update_blocks(
            all_old_synced_block_headers2[index], 
            all_new_synced_block_headers2[index], 
            all_old_synced_block_headers2[index], 
            heading_number=2, 
            index_synced_block=index
        )

    # Update heading 3 blocks
    for index in range(len(all_new_synced_block_headers3)):
        await check_and_update_blocks(
            all_old_synced_block_headers3[index], 
            all_new_synced_block_headers3[index], 
            all_old_synced_block_headers3[index], 
            heading_number=3, 
            index_synced_block=index
        )


def main():
    logging.basicConfig(level=logging.INFO)
    
    getEnvironmentVariables()
    setHeaders()
    retreivePageIDWithTitle("Onderzoekslogboek")
    getBlocksFromPage(main_page_id)
    getHeadingsFromBlocks()
    renumberHeading1Blocks()

    getSyncedBlockPageID()
    getAllSyncedBlockContent()

    asyncio.run(updateAllHeaders())

main()