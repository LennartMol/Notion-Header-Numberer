import time
import os


def getEnvironmentVariables():
    """ Gets environment variables and sets them in global variables
    """

    global NOTION_API_KEY
    NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
    if NOTION_API_KEY == None:
        print(f"\nMake sure to correctly set your environment variables.\n")
        exit()

getEnvironmentVariables() 