# wit_project
Wit is a command line program for handling version control of your files.\
In order to start tracking files with wit, you first need to navigate to the relevant folder using the command line and afterwards use the "init" command, as explained in the next section.\
Later you can use the various commands to manipulate your project files.

Init:\
Usage: python <WIT_FILE_PATH> init\
Initialize 'wit' directory in the current working directory, with that folders inside: 'images', 'staging_area', and the file: 'activated.txt'

Add:\
Usage: python <WIT_FILE_PATH> add <FILE_PATH>\
Add files from the working directory to the staging area folder. FILE_PATH is the file/ directory path you would like to add.

Commit:\
Usage: python <WIT_FILE_PATH> commit <MESSAGE>\
Create new folder in 'images' and save all the files from the staging area, create new commit id file with the same name as the folder.\
MESSAGE- The message you would like to add to the commit.

Status:\
Usage: python <WIT_FILE_PATH> status\
Get the status of your wit repository: Changes to be commited, Changes not staged for commit and Untracked files.
  
Checkout:\
Usage: python <WIT_FILE_PATH> checkout <BRANCH_NAME/ COMMIT_ID>\
Copy all of the files from a chosen BRANCH_NAME/ COMMIT_ID to the working directory. HEAD will point to that commit id after that command.
  
Graph:\
Usage: python <WIT_FILE_PATH> graph\
Create and show a graph of all the commits id-\
starting from 'HEAD' and continue with arrow towards the commit id that marked as his parent, from it to the parent above and so on.

Branch:\
Usage: python <WIT_FILE_PATH> branch <BRANCH_NAME>\
Create a new branch, that will point to the last commit id we work on.\
As long as the HEAD is on this branch and this branch is activated (by 'checkout'), the commit id of that branch will change in every commit.

Merge:\
Usage: python <WIT_FILE_PATH> merge <BRANCH_NAME/ COMMIT_ID>\
Create a new commit, which will merge the files between the current commit and the BRANCH_NAME/ COMMIT_ID passed.
