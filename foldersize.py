import os
import re
import unicodedata
from enum import Enum


class FolderSize:
    def __init__(self, path):
        self.__path = path
        self.__dirlist = []  # [((dir,size),[(file,size),(file,size)]),((dir,size),[(file,size)])]
        self.__dirlist_history = []
        self.__dirlist_view = []
        self.__lastprinted = ViewType

    def scan_dir(self):
        dirlist = self.__scan(self.__path)
        self.__dirlist = dirlist[::-1]

    def __scan(self, path):
        # Check
        if not os.path.exists(path):
            raise Exception("The path doesn't exist")

        dirlist = []
        templist = []
        temppath = path

        try:
            for direntry in os.scandir(path):
                dirpath, basename = os.path.split(direntry.path)
                fullpath = direntry.path

                if temppath != dirpath:
                    templist_sorted = sorted(templist, key=lambda x: x[1], reverse=True)
                    dirlist.append(((temppath, self.__calc_size(temppath, isfile=False)), templist_sorted))
                    temppath = dirpath

                if direntry.is_file():
                    templist.append((basename, self.__calc_size(fullpath)))
                elif direntry.is_dir():
                    sublist = self.__scan(fullpath)
                    sublist += dirlist
                    dirlist = sublist
            else:
                templist_sorted = sorted(templist, key=lambda x: x[1], reverse=True)
                dirlist.append(((temppath, self.__calc_size(temppath, isfile=False)), templist_sorted))
        except:
            pass

        return dirlist

    def __calc_size(self, path, isfile=True):
        if isfile:
            return os.path.getsize(path)

        totalsize = 0

        try:
            for direntry in os.scandir(path):
                if direntry.is_file():
                    totalsize += self.__calc_size(direntry.path)
                elif direntry.is_dir():
                    totalsize += self.__calc_size(direntry.path, False)
            return totalsize
        except:
            return 0

    def create_dir_list(self, full=False, number=10):
        self.__check_dirlist()

        dlist = [ditem[0] for ditem in self.__dirlist]
        dlist_sorted = sorted(dlist, key=lambda x: x[1], reverse=True)

        if number > len(dlist_sorted) or full:
            number = len(dlist_sorted)
        elif number <= 0:
            raise Exception('Index overflowed')

        dlist_selected = [dlist_sorted[item] for item in range(0, number)]
        self.__dirlist_view = dlist_selected

    def create_file_list(self, full=False, number=10):
        self.__check_dirlist()

        flist = []
        for ditem in self.__dirlist:
            dirname = ditem[0][0]
            for fitem in ditem[1]:
                filename = fitem[0]
                filesize = fitem[1]
                flist.append((os.path.join(dirname, filename), filesize))
        flist_sorted = sorted(flist, key=lambda x: x[1], reverse=True)

        if number > len(flist_sorted) or full:
            number = len(flist_sorted)
        elif number <= 0:
            raise Exception('Index overflowed')

        flist_selected = [flist_sorted[item] for item in range(0, number)]
        self.__dirlist_view =  flist_selected

    def get_elem(self, index):
        self.__check_dirlist()

        if self.__lastprinted == ViewType.TreeView:
            return self.__get_dir_tree_elem(index)
        elif self.__lastprinted == ViewType.ListView:
            return self.__get_list_elem(index)

    def __get_dir_tree_elem(self, index):
        indexcnt = -1
        rootdir = self.__dirlist[0][0][0]
        rootdepth = calc_depth(rootdir)

        for ditem in self.__dirlist:
            dirpath = ditem[0][0]
            dirdepth = calc_depth(dirpath)
            reldepth = dirdepth - rootdepth
            if reldepth == 1:
                indexcnt += 1
            if index == indexcnt:
                return dirpath

        raise Exception('Index overflowed')

    def __get_list_elem(self, index):
        if index > len(self.__dirlist_view):
            raise Exception('Index overflowed')
        return self.__dirlist_view[index][0]

    def movein_list(self, index):
        self.__check_dirlist()

        newdirlist = []
        indexcnt = -1
        isstarted = False
        rootdir = self.__dirlist[0][0][0]
        rootdepth = calc_depth(rootdir)

        for ditem in self.__dirlist:
            dirpath = ditem[0][0]
            dirdepth = calc_depth(dirpath)
            reldepth = dirdepth - rootdepth

            if reldepth == 1:
                if isstarted:
                    self.__dirlist_history.append(self.__dirlist)
                    self.__dirlist = newdirlist
                else:
                    indexcnt += 1
            if index == indexcnt:
                isstarted = True
                newdirlist.append(ditem)
        # Check
        if not newdirlist:
            raise Exception('Index overflowed')
        else:
            self.__dirlist_history.append(self.__dirlist)
            self.__dirlist = newdirlist

    def back_list(self):
        self.__check_dirlist()
        self.__check_dirlist_history()

        self.__dirlist = self.__dirlist_history.pop()

    def print_treeview(self, collapse=True, level=5):
        self.__check_dirlist()

        dirind = '│   '
        fileind = '    '
        symbol = '├──'
        indexcnt = -1
        collapsecnt = 0
        rootdir = self.__dirlist[0][0][0]
        rootdepth = calc_depth(rootdir)
        if level < 2:
            level = 2

        for i, ditem in enumerate(self.__dirlist):
            dirpath = ditem[0][0]
            dirname = os.path.basename(dirpath)
            dirsize = bytes_convert(ditem[0][1])
            dirdepth = calc_depth(dirpath)
            reldepth = dirdepth - rootdepth

            if i != 0:
                if collapse:
                    if reldepth >= level:
                        collapsecnt += 1
                        continue
                    elif collapsecnt != 0:
                        print(f'{dirind * level}{symbol} ...{collapsecnt} folders collapsed')
                        collapsecnt = 0

                if reldepth == 1:
                    indexcnt += 1
                    dirname = f'{indexcnt}.{dirname}'

                dirname = f'[{len_adjust(dirname)}]'

                print(f'{dirind * reldepth}{symbol} {dirname:<{44 - len_diff(dirname)}}{dirsize:>12}')
            else:  # print rootdir
                dirname = f'[{len_adjust(dirpath)}]'
                print(f'{dirname:<{48 - len_diff(dirname)}}{dirsize:>12}')

            for j, fitem in enumerate(ditem[1]):
                if collapse and i != 0:
                    if reldepth >= 3:
                        print(f'{fileind * (reldepth + 1)}{symbol} ...{len(ditem[1])} files collapsed')
                        break
                    elif j > 2:
                        print(f'{fileind * (reldepth + 1)}{symbol} ...{len(ditem[1]) - 3} files collapsed')
                        break

                filename = len_adjust(fitem[0])
                filesize = bytes_convert(fitem[1])

                print(f'{fileind * (reldepth + 1)}{symbol} {filename:<{40 - len_diff(filename)}}{filesize:>12}')

        if collapse and collapsecnt != 0:
            print(f'{dirind * level}{symbol} ...{collapsecnt} folders collapsed')
        self.__lastprinted = ViewType.TreeView

    def print_listview(self):
        self.__check_dirlist_view()
        [print(f'{i:>3}. {bytes_convert(item[1]):>10}  {item[0]}')
         for i, item in enumerate(self.__dirlist_view)]
        self.__lastprinted = ViewType.ListView

    def __check_dirlist(self):
        if not self.__dirlist:
            raise Exception('Do not have any scan results')

    def __check_dirlist_history(self):
        if not self.__dirlist_history:
            raise Exception('Already at the top of the folder')

    def __check_dirlist_view(self):
        if not self.__dirlist_view:
            raise Exception('Do not have any listview results')


class ViewType(Enum):
    TreeView = 1
    ListView = 2


def calc_depth(path):
    if os.path.sep == '\\':
        sep = r'\\'
    else:
        sep = os.path.sep
    return len(re.findall(sep, path))


def len_adjust(string):
    if len_count(string) > 40:
        return string[0:17 - len_diff(string[0:17])] + '...' + \
               string[-20 + len_diff(string[-20:]):]
    return string


def len_count(string):
    count = 0
    for char in string:
        if unicodedata.east_asian_width(char) in 'FW':
            count += 2
        else:
            count += 1
    return count


def len_diff(string):
    count = 0
    for char in string:
        if unicodedata.east_asian_width(char) in 'FWA':
            count += 1
    return count


def bytes_convert(size):
    kb = 1024
    mb = 1024 ** 2
    gb = 1024 ** 3
    if size < mb:
        return f'{size / kb:>5.2f} KB'
    elif mb <= size < gb:
        return f'{size / mb:>5.2f} MB'
    elif gb <= size:
        return f'{size / gb:>5.2f} GB'
