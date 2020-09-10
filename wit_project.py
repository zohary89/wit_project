from datetime import datetime
import filecmp
import logging
import os
import random
import shutil
import string
import sys
from time import strftime

from matplotlib import pyplot as plt
import networkx as nx

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

WIT = ".wit"
STAGING_AREA = os.path.join(".wit", "staging_area")
IMAGES = os.path.join(".wit", "images")
REFERENCES = os.path.join(".wit", "references.txt")


def log_and_print(message):
    logging.error(message)
    print(message)


def update_activated_file(path, branch):
    with open(os.path.join(path, "activated.txt"), "w") as f:
        f.write(branch)


def make_folders_in_wit(path):
    folders = ["images", "staging_area"]
    for folder in folders:
        os.mkdir(os.path.join(path, folder))
        print(f"Directory {folder} was created")


def init():
    directory = WIT
    parent_dir = os.getcwd()
    path = os.path.join(parent_dir, directory) 
    try:
        os.mkdir(path)
        print(f"Directory {path} was created") 
    except FileExistsError:
        log_and_print(f"The directory '.wit' already exists in the current folder, {path}")
    else:
        make_folders_in_wit(path)
        update_activated_file(path, "master")
        print("activated file was created")


def find_wit_folder(path):
    previous_path = None
    if os.path.isdir(path):
        current_path = path
    else:
        current_path = os.path.dirname(path)
    while current_path != previous_path:
        if WIT in os.listdir(current_path):
            return current_path
        previous_path = current_path
        current_path = os.path.dirname(previous_path)
    return None


def get_dst_with_rel_folders(path, wit_dst):
    relative_folders = os.path.relpath(path, wit_dst)
    return os.path.join(wit_dst, STAGING_AREA, relative_folders)


def copy_file(path, wit_dst):
    folder_path = os.path.dirname(path)
    if os.path.samefile(folder_path, wit_dst):
        shutil.copy2(path, (os.path.join(wit_dst, STAGING_AREA)))
    else:
        dst = get_dst_with_rel_folders(path, wit_dst)
        try:
            os.makedirs(os.path.dirname(dst))
        except FileExistsError:
            pass
        finally:
            shutil.copy2(path, dst)


def copy_directory(path, wit_dst):
    dst = get_dst_with_rel_folders(path, wit_dst)
    try:
        shutil.copytree(path, dst)
    except FileExistsError:
        shutil.rmtree(dst)
        shutil.copytree(path, dst)
    

def add(path):
    if os.path.isabs(path):
        abs_path = path
    else:
        abs_path = os.path.join(os.getcwd(), path)
    wit_dst = find_wit_folder(abs_path)
    if wit_dst is not None:
        if os.path.isfile(abs_path):
            copy_file(abs_path, wit_dst)
        else:
            copy_directory(abs_path, wit_dst)
        print(f"{abs_path} - add to the staging area")
    else:
        log_and_print("There is no '.wit' folder in the directory")


def get_references_items(wit_dst):
    with open(os.path.join(wit_dst, REFERENCES), "r") as f:
        lines = f.readlines()
    references_dict = {}
    for line in lines:
        item = line.strip().split("=")
        references_dict[item[0]] = item[1]
    return references_dict


def create_references_file(wit_dst, commits_dict): 
    path = os.path.join(wit_dst, REFERENCES)
    text = ""
    for key, value in commits_dict.items():
        text += f"{key}={value}\n"
    with open(path, "w") as references_file:
        references_file.write(text)


def create_commit_id_file(wit_dst, path, message, merged_commit_id=None):
    tz = strftime("%z")
    time = datetime.now().strftime(f"%a %b %d %H:%M:%S %Y {tz}")
    if len(os.listdir(os.path.dirname(path))) < 2:   # check images folder for next commit
        txt_to_write = f"parent=None\n{time}\n{message}\n"
    else:
        parent_commit_id = get_references_items(wit_dst)["HEAD"]
        if merged_commit_id is not None:
            parent_commit_id += f", {merged_commit_id}"
        txt_to_write = f"parent={parent_commit_id}\n{time}\n{message}\n"
    with open(path + ".txt", "w") as f:
        f.write(txt_to_write)


def create_commit_id_folder(wit_dst, message, merged_commit_id=None):
    commit_id = ''.join(random.choice(string.ascii_lowercase[:6] + string.digits) for _ in range(40))
    commit_id_folder = (os.path.join(wit_dst, IMAGES, commit_id))
    os.mkdir(commit_id_folder)
    create_commit_id_file(wit_dst, commit_id_folder, message, merged_commit_id)
    return commit_id_folder


# Derived from https://stackoverflow.com/questions/3397752
# By dustin michels https://stackoverflow.com/users/7576819/dustin-michels
def recursive_copy(src, dst):
    for item in os.listdir(src):
        file_path = os.path.join(src, item)
        if os.path.isfile(file_path):
            shutil.copy2(file_path, dst)
        elif os.path.isdir(file_path):
            new_dst = os.path.join(dst, item)
            try:
                os.mkdir(new_dst)
            except FileExistsError:
                pass
            recursive_copy(file_path, new_dst)


def save_staging_area(wit_dst, commit_id_path):
    staging_area = os.path.join(wit_dst, STAGING_AREA)
    recursive_copy(staging_area, commit_id_path)


def check_activated_branch(wit_dst):
    with open(os.path.join(wit_dst, ".wit/activated.txt"), "r") as f:
        return f.read()


def commit(wit_dst, message, merged_commit_id=None):
    commit_id_path = create_commit_id_folder(wit_dst, message, merged_commit_id)
    save_staging_area(wit_dst, commit_id_path)
    commit_id = os.path.basename(commit_id_path)
    try:
        references_items = get_references_items(wit_dst)
    except FileNotFoundError:
        references_items = {'HEAD': commit_id, "master": commit_id}
        create_references_file(wit_dst, references_items)
    else:
        activated_branch = check_activated_branch(wit_dst)
        if activated_branch is None:
            references_items["HEAD"] = commit_id 
            create_references_file(wit_dst, references_items)
        else:
            if references_items[activated_branch] == references_items['HEAD']:
                references_items["HEAD"] = commit_id
                references_items[activated_branch] = commit_id 
                create_references_file(wit_dst, references_items)
            else:
                references_items["HEAD"] = commit_id
                create_references_file(wit_dst, references_items)
    print(f"Commit {commit_id} created")


def get_current_commit_id(wit_dst):
    try:
        commit_id = get_references_items(wit_dst)["HEAD"]
    except FileNotFoundError:
        return None
    return os.path.join(wit_dst, IMAGES, commit_id)


def get_children_relative_to_path(path, root, item):
    full_path = os.path.join(root, item)
    return os.path.relpath(full_path, path)


def get_all_children_relative_to_path(path):
    dirs_set = set()
    files_set = set()
    for root, dirs, files in os.walk(path):
        for directory in dirs:
            rel_path = get_children_relative_to_path(path, root, directory)
            dirs_set.add(rel_path)
        for f in files:
            rel_path = get_children_relative_to_path(path, root, f)
            files_set.add(rel_path)
    return dirs_set, files_set


def check_changed_common_files(files, staging_area, cur_commit_id):
    for f in files:
        if not filecmp.cmp(os.path.join(staging_area, f), os.path.join(cur_commit_id, f)):
            yield f


def get_changes_to_be_committed(staging_area, cur_commit_id, staging_area_items, commit_id_items):
    dirs_commit_id, files_commit_id = commit_id_items
    dirs_staging_area, files_staging_area = staging_area_items
    new_files_staging_area = list(files_staging_area - files_commit_id)
    new_dirs_staging_area = list(dirs_staging_area - dirs_commit_id)
    common_files = files_staging_area & files_commit_id
    changed_common_files = list(check_changed_common_files(common_files, staging_area, cur_commit_id))
    return new_files_staging_area + new_dirs_staging_area + changed_common_files


def get_changes_not_staged_for_commit(wit_dst, staging_area, files_staging_area):
    for f in files_staging_area:
        full_path = os.path.join(wit_dst, f)
        if os.path.exists(full_path):
            if not filecmp.cmp(full_path, os.path.join(staging_area, f)):
                yield f


def get_untracked_files(wit_dst, staging_area, staging_area_items):
    real_dirs, real_files = get_all_children_relative_to_path(wit_dst)
    real_dirs_filter_wit = {directory for directory in real_dirs if WIT not in directory}
    real_files_filter_wit = {f for f in real_files if WIT not in f}
    dirs_staging_area, files_staging_area = staging_area_items
    difference_dirs = list(real_dirs_filter_wit - dirs_staging_area)
    difference_files = list(real_files_filter_wit - files_staging_area)
    return difference_dirs + difference_files


def get_status_info(wit_dst):
    cur_commit_id = get_current_commit_id(wit_dst)
    staging_area = os.path.join(wit_dst, STAGING_AREA)
    staging_area_items = get_all_children_relative_to_path(staging_area)
    if cur_commit_id is not None:
        commit_id_items = get_all_children_relative_to_path(cur_commit_id)
        changes_to_be_committed = get_changes_to_be_committed(staging_area, cur_commit_id, staging_area_items, commit_id_items)
    else:
        changes_to_be_committed = None
    files_staging_area = staging_area_items[1]
    changes_not_staged_for_commit = list(get_changes_not_staged_for_commit(wit_dst, staging_area, files_staging_area))
    untracked_files = get_untracked_files(wit_dst, staging_area, staging_area_items)
    return changes_to_be_committed, changes_not_staged_for_commit, untracked_files


def status(wit_dst):
    changes_to_be_committed, changes_not_staged_for_commit, untracked_files = get_status_info(wit_dst)
    print("Changes to be committed:")
    if changes_to_be_committed is None:
        print("There is no commit id yet.")
    else:
        for f in changes_to_be_committed:
            print(f)
    print("\nChanges not staged for commit:")
    for f in changes_not_staged_for_commit:
        print(f)
    print("\nUntracked files:")
    for f in untracked_files:
        print(f)


def check_status(changes_to_be_committed, changes_not_staged_for_commit):
    return len(changes_to_be_committed) == 0 and len(changes_not_staged_for_commit) == 0


def update_head(wit_dst, commit_id, references_dict):
    references_dict['HEAD'] = commit_id
    create_references_file(wit_dst, references_dict)


def update_staging_area(staging_area, commit_id_path):
    shutil.rmtree(staging_area)
    shutil.copytree(commit_id_path, staging_area)


def check_if_commit_is_exist(wit_dst, commit_id):
    images = os.path.join(wit_dst, IMAGES)
    return commit_id in os.listdir(images)


def checkout(wit_dst):
    commit_id = sys.argv[2]
    branch = ""
    references = get_references_items(wit_dst)
    if commit_id in references.keys():
        branch = commit_id
        commit_id = references[branch]
    elif not check_if_commit_is_exist(wit_dst, commit_id):
        log_and_print("Invalid commit id/ branch")
        return
    changes_to_be_committed, changes_not_staged_for_commit, _ = get_status_info(wit_dst)
    if check_status(changes_to_be_committed, changes_not_staged_for_commit):
        commit_id_path = os.path.join(wit_dst, IMAGES, commit_id)
        staging_area = os.path.join(wit_dst, STAGING_AREA)
        recursive_copy(commit_id_path, wit_dst)
        update_head(wit_dst, commit_id, references)
        update_staging_area(staging_area, commit_id_path)
        print(f"Checkout was done to commit id: {commit_id}")
        update_activated_file(os.path.join(wit_dst, WIT), branch)
    else:
        log_and_print("Unable to checkout. Check changes_to_be_committed or changes_not_staged_for_commit")


def get_parent_commit(wit_dst, commit_id):
    with open(os.path.join(wit_dst, IMAGES, F"{commit_id}.txt")) as info:
        info_details = info.readlines()
    parent_line = info_details[0]
    parent_list = parent_line.strip().split("=")
    parent = parent_list[1]
    if "," in parent:
        parents = parent.split(", ")
        return parents
    return [parent]


def get_splited_commit_id(commit_id):
    part1 = commit_id[:20]
    part2 = commit_id[20:]
    return part1 + "\n" + part2


def recursive_parent_commit(wit_dst, start_commit_id, commits_list):
    parent_id = get_parent_commit(wit_dst, start_commit_id)
    commit = get_splited_commit_id(start_commit_id)
    if parent_id[0] == 'None':
        if len(commits_list) == 0:
            commits_list = [(commit, "None")]
    else:
        for parent in parent_id:
            splited_parent = get_splited_commit_id(parent)
            commits_list.append((commit, splited_parent))
            recursive_parent_commit(wit_dst, parent, commits_list)
    return commits_list


def get_commits_list_from_head(wit_dst):
    head = get_references_items(wit_dst)["HEAD"]
    commits_list = []
    return recursive_parent_commit(wit_dst, head, commits_list)


def create_graph(all_commits):
    commits_g = nx.DiGraph()
    commits_g.add_edges_from(all_commits)
    nx.draw_networkx(commits_g, arrows=True, node_size=6000, node_color='lightblue', font_size=7)
    plt.savefig("commits_g.png", format="PNG")
    plt.show()


def graph(wit_dst):
    try:
        all_commits = get_commits_list_from_head(wit_dst)
    except FileNotFoundError:
        create_graph([])
        log_and_print("There is no wit images yet.")
    else:
        create_graph(all_commits)


def add_branch_to_references(wit_dst, branch_name):
    references_items = get_references_items(wit_dst)
    if branch_name in references_items.keys():
        log_and_print(f"Branch {branch_name} name already exist")
    else:
        head = references_items["HEAD"]
        path = os.path.join(wit_dst, REFERENCES)
        with open(path, "a") as references_file:
            references_file.write(f"{branch_name}={head}\n")
        print(f"branch {branch_name}- add to references")


def branch(wit_dst):
    branch_name = sys.argv[2]
    try:
        add_branch_to_references(wit_dst, branch_name)
    except FileNotFoundError:
        print("Can't add branch. There is no references yet.")


def check_if_changed_files(files, commit_id, staging_area):
    for f in files:
        if not filecmp.cmp(os.path.join(staging_area, f), os.path.join(commit_id, f)):
            return True
    return False


def check_equality_between_head_and_staging_area(wit_dst, head, staging_area):
    head_dirs_set, head_files_set = get_all_children_relative_to_path(head)
    staging_dirs_set, staging_files_set = get_all_children_relative_to_path(staging_area)
    uncommon_files = staging_files_set ^ head_files_set
    uncommon_dirs = head_dirs_set ^ staging_dirs_set
    if len(uncommon_files) > 0 or len(uncommon_dirs) > 0:
        return False
    common_files = staging_files_set & head_files_set
    if check_if_changed_files(common_files, head, staging_area):
        return False
    return True


def merge(wit_dst):
    merged_commit_id = sys.argv[2]
    message = f"Merge branch/commit id: {merged_commit_id}"
    references = get_references_items(wit_dst)
    if merged_commit_id in references.keys():
        merged_commit_id = references[merged_commit_id]
    elif not check_if_commit_is_exist(wit_dst, merged_commit_id):
        log_and_print("Invalid commit id/ branch")
        return
    head_path = os.path.join(wit_dst, IMAGES, references['HEAD'])
    staging_area = os.path.join(wit_dst, STAGING_AREA)
    if check_equality_between_head_and_staging_area(wit_dst, head_path, staging_area):
        merged_commit_id_path = os.path.join(wit_dst, IMAGES, merged_commit_id)
        recursive_copy(merged_commit_id_path, staging_area)
        commit(wit_dst, message, merged_commit_id)
    else:
        log_and_print("Can't merge, Staging area and HEAD are different")


def main():
    try:
        function = sys.argv[1]
    except IndexError:
        log_and_print("Usage: python <filename> <function>")
        return 
    
    if function == "init":
        init()
 
    elif function == "add":
        try:
            path = sys.argv[2]
            add(path)
        except IndexError:
            log_and_print("Usage: python <filename> <add> <path>")
        except FileNotFoundError:
            log_and_print("Invalid path, use valid absolute or relative path.")

    elif function in ["commit", "status", "checkout", "graph", "branch", "merge"]:
        wit_dst = find_wit_folder(os.getcwd())
        if wit_dst is None:
            log_and_print("There is no '.wit' directory in the cwd")
            return

        if function == "commit":
            try:
                message = sys.argv[2]
                commit(wit_dst, message) 
            except IndexError:
                log_and_print("Usage: python <filename> <commit> <message>")
        elif function == "status":
            status(wit_dst)
        elif function == "checkout":
            try:
                checkout(wit_dst)
            except IndexError:
                log_and_print("Usage: python <filename> <checkout> <commit id/branch>")
        elif function == "graph":
            graph(wit_dst)
        elif function == "branch":
            try:
                branch(wit_dst)
            except IndexError:
                log_and_print("Usage: python <filename> <branch> <branch name>")
        elif function == "merge":
            try:
                merge(wit_dst)
            except IndexError:
                log_and_print("Usage: python <filename> <merge> <branch name/commit id>")
    else:
        log_and_print("Unknown command was given.")
    

if __name__ == "__main__":
    main()