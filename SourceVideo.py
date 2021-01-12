import os
import sys
import shutil

class SourceVideo:
    def __init__(self, filename, folder, separator):
        self.Folder = folder
        self.Filename = filename
        split_filename = os.path.splitext(self.Filename)[0].split(separator)
        self.Name = split_filename[0]
        self.Channel = split_filename[2]
        self.ID = split_filename[1]
        self.Extension = os.path.splitext(self.Filename)[1]

    def __eq__(self, other):
        return self.ID == other.ID

    def MoveToFolder(self, folder):
        filepath = os.path.join(self.Folder, self.Filename)
        newFilepath = os.path.join(folder, self.Filename)
        try:
            shutil.move(filepath, newFilepath)
        except FileNotFoundError:
            print("\t{}: file not found, skipping...\n\t{}".format(self.Name, sys.exc_info()))
        self.Folder = folder