"""
Simple script to replace template files with their local counterparts.

Sensetive files in this project are stored localy in two versions:
- template version (e.g. `users.acl`) - all sensitive data is replaced with
    placeholders
- local version (e.g. `users.local.acl`) - file with real sensitive data
    used for local development and testing

This script replaces template files with their local counterparts and removes
local files. It is useful for deployment to production environment.
"""


import argparse
import os
import shutil


LOCAL_TAG = '.local'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Replace Template Files',
        description=('Replace template files with their local counterparts.')
    )
    parser.add_argument('--dir', '-d', type=str, default='.')
    args = parser.parse_args()

    for root, subdirs, files in os.walk(args.dir):
        for file in files:
            if LOCAL_TAG in file:
                template_file = file.replace(LOCAL_TAG, '')
                template_file_path = os.path.join(root, template_file)
                file_path = os.path.join(root, file)
                if os.path.exists(template_file_path):
                    os.remove(template_file_path)
                shutil.copyfile(file_path, template_file_path)
                os.remove(file_path)
