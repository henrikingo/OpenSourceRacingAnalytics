import sys
import os
import platform
import threading



def getDocumentDir(out_data_dir='Open Source Racing Analytics'):
    import platform
    outputDirectory = None
    print(platform.system())

    if platform.system() == "Windows":
        outputDirectory = getWin32DocumentDir(out_data_dir=out_data_dir)
        assert outputDirectory is not None
        outputDirectory = os.path.join(outputDirectory, out_data_dir)
    else:
        outputDirectory = os.path.join(os.path.expanduser("~"),"Documents",out_data_dir)

    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    return outputDirectory

def getSourceDir(source_data_dir="IncomingAlfano6"):
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "ALFANO SOFTWARE");
    else:
        return os.path.join(os.path.expanduser("~"),"Documents",source_data_dir)

def getWin32DocumentDir():
    import ctypes
    from ctypes.wintypes import MAX_PATH
    dll = ctypes.windll.shell32
    documentsFolderBuffer = ctypes.create_unicode_buffer(MAX_PATH + 1)
    if dll.SHGetSpecialFolderPathW(None, documentsFolderBuffer, 0x0005, False):
        return os.path.join(documentsFolderBuffer.value)
    elif os.getenv('USERPROFILE'):
        return os.path.join(os.getenv('USERPROFILE'),'Documents')
    else:
        return None

    return outputDirectory


if __name__=="__main__":
    reader = AlfanoReader()
    reader.translate_sessions()
    reader.write_sessions()
