import os


def get_parent_folder_name_and_basename(the_path):
    the_path = os.path.abspath(the_path)
    return os.path.basename(os.path.dirname(the_path)), os.path.basename(the_path)