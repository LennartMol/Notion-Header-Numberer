# Notion Header Numberer
A python script that will automatically number headings within a Notion page.

**For example:**

Chapter (heading 1)  
&nbsp;&nbsp;&nbsp;&nbsp;Subchapter(heading 2)  
Chapter (heading 1)  
&nbsp;&nbsp;&nbsp;&nbsp;Subchapter (heading 2)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Subsubchapter (heading 3)  
        
**Will automatically change into:**

1 Chapter (heading 1)  
&nbsp;&nbsp;&nbsp;&nbsp;1.1 Subchapter(heading 2)  
2 Chapter (heading 1)  
&nbsp;&nbsp;&nbsp;&nbsp;2.1 Subchapter (heading 2 to)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.1 Subsubchapter (heading 3) 
<br>
<br>

### To use this script follow these steps: 

1. Create a Notion integration (internal) to get a notion API key
2. To use this script, on all pages under 'Connections' add your created integration, thus granting it edit rights.
3. Set the notion API key as an environmental variable on your computer with the same 'NOTION_API_KEY'
4. Change the global variable 'main_page_id' to the page you want to use this script on.
5. Enjoy!

**NOTE:** This script is highly specificly written to be used for one of my own documents. This its implementation is dependant on so called 'Synced blocks' within Notion and will NOT work without these blocks.  
It can be used to only update Heading1 chapters by commenting out the following functions:  

        getSyncedBlockPageID()
        getAllSyncedBlockContent()

### TODO: Improvments

- To enhance performance and reduce unnecessary data usage, check if the chapter or heading content has changed before sending a PATCH request. If no changes are detected, the update request is skipped, resulting in faster execution and more efficient use of resources. ✔️
- To enhance performance, do all header requests of Heading 1 async ✔️
- To enhance performance, do all header requests of Heading 2 async within chapter ✔️
- To enhance performance, do all header requests of Heading 3 async within chapter ✔️
- Optimally do all requets simultaneously async after all headers are renumbered. This requires redesign of code structure. ✔️
- Make using synced blocks optional and use headings of the page instead. Right now only heading 1 is used from the main page, heading 2 and heading 3 are retreived from synced blocks from other pages.
