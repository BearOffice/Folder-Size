import sys
import ctypes
import os
import subprocess
import foldersize

# windows runtime

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def cmd_spl(cmd):
    try:
        cmd = cmd.partition(' ')
        return cmd[0], cmd[2]
    except:
        return cmd, ''


helpmsg = 'Enter help(h) to get help message\n' + \
    'Enter scan(s) [path] to scan all folders and files below the path specified\n' + \
    'Enter treeview(t) [optional=level / -full(f)] to print the scan\'s result\n' + \
    '           the folders below the level will be collapsed\n' + \
    '           default value is 5  level should be upper than 1\n' + \
    '           use option -full(f) to print the full scan\'s result\n' + \
    'Enter dirlistview(dl) [optional=number / -full(f)] to print the folders\' paths descending by size\n' + \
    '           number can be specified to decide the number of paths you want to display\n' + \
    '           default value is 10\n' + \
    '           use option -full(f) to print the full result\n' + \
    'Enter filelistview(fl) [optional=number / -full(f)] to print the files\' paths descending by size\n' + \
    '           number can be specified to decide the number of paths you want to display\n' + \
    '           default value is 10\n' + \
    '           use option -full(f) to print the full result\n' + \
    'Enter go(g) [index] to move into the specified folders\n' + \
    'Enter back(b) to move back the parent folders\n' + \
    'Enter open(o) [index] to open the folder or the file specified\n' + \
    'Enter exit(e) to exit'

if is_admin():
    pass
else:
    print('Permission is needed to access the system files\n' + 'Would you like to request the permission(y/n)?')
    inputsrc = input()
    if inputsrc == 'y':
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()
    else:
        pass

print()
print('Enter help(h) to get help message')

dirlist = []
dirlist_view = []
dirlist_history = []
lastdisplayed = ''

while True:
    print()
    print('> Enter command:')
    inputsrc = input()
    cmd, cont = cmd_spl(inputsrc)
    print()

    try:
        if cmd == 'help' or cmd == 'h':
            print(helpmsg)
        elif cmd == 'scan' or cmd == 's':
            print('Scan started...')
            dirlist = []
            dirlist_view = []
            dirlist_history = []
            dirlist = foldersize.scan_dir(cont)
            print('Scan completed...')
        elif cmd == 'treeview' or cmd == 't':
            if dirlist == []:
                raise Exception('Scan first')

            if cont == '-full' or cont == '-f':
                foldersize.print_treeview(dirlist, collapse=False)
            elif cont != '':
                foldersize.print_treeview(dirlist, level=int(cont))
            else:
                foldersize.print_treeview(dirlist)

            lastdisplayed = 't'
        elif cmd == 'dirlistview' or cmd == 'dl':
            if dirlist == []:
                raise Exception('Scan first')

            if cont == '-full' or cont == '-f':
                dirlist_view = foldersize.get_dir_list(dirlist, full=True)
            elif cont != '':
                dirlist_view = foldersize.get_dir_list(dirlist, number=int(cont))
            else:
                dirlist_view = foldersize.get_dir_list(dirlist)

            foldersize.print_listview(dirlist_view)
            lastdisplayed = 'dl'
        elif cmd == 'filelistview' or cmd == 'fl':
            if dirlist == []:
                raise Exception('Scan first')

            if cont == '-full' or cont == '-f':
                dirlist_view = foldersize.get_file_list(dirlist, full=True)
            elif cont != '':
                dirlist_view = foldersize.get_file_list(dirlist, number=int(cont))
            else:
                dirlist_view = foldersize.get_file_list(dirlist)

            foldersize.print_listview(dirlist_view)
            lastdisplayed = 'fl'
        elif cmd == 'go' or cmd == 'g':
            if dirlist == []:
                raise Exception('Scan first')

            newdirlist = foldersize.movein_list(dirlist, int(cont))
            dirlist_history.append(dirlist)
            dirlist = newdirlist
            foldersize.print_treeview(dirlist)
            lastdisplayed = 't'
        elif cmd == 'back' or cmd == 'b':
            if dirlist == []:
                raise Exception('Scan first')
            if dirlist_history == []:
                raise Exception('Already at the top of the folder')

            dirlist = dirlist_history.pop()
            foldersize.print_treeview(dirlist)
            lastdisplayed = 't'
        elif cmd == 'open' or cmd == 'o':
            if dirlist == []:
                raise Exception('Scan first')

            if lastdisplayed == 't':
                path = foldersize.get_dir_tree_elem(dirlist, int(cont))
                subprocess.run(f'explorer /select,{path}')
                print(path + ' opened')
            elif lastdisplayed == 'dl':
                path = foldersize.get_dir_list_elem(dirlist_view, int(cont))
                subprocess.run(f'explorer /select,{path}')
                print(path + ' opened')
            elif lastdisplayed == 'fl':
                path = foldersize.get_file_list_elem(dirlist_view, int(cont))
                subprocess.run(f'explorer /select,{path}')
                print(path + ' opened')
        elif cmd == 'exit' or cmd == 'e':
            break
        else:
            print('Do not have such a command')
    except Exception as ex:
        print('Operation invaild:', ex)

exit()
