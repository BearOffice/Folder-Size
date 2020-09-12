import os
import re
import unicodedata


def get_list(path):
    dirlist = scan_dir(path)
    return dirlist[::-1]


def scan_dir(path):
    # Check
    if not os.path.exists(path):
        raise Exception("The path doesn't exist")

    dirlist = []
    templist = []
    temppath = path

    try:
        for direntry in os.scandir(path):
            dirname, basename = os.path.split(direntry.path)
            fullpath = direntry.path
            if temppath != dirname:
                templist_sorted = sorted(templist, key=lambda x: x[1], reverse=True)
                dirlist.append(((temppath, calc_size(temppath, isfile=False)), templist_sorted))
                temppath = dirname

            if direntry.is_file():
                templist.append((basename, calc_size(fullpath)))
            elif direntry.is_dir():
                sublist = scan_dir(fullpath)
                sublist += dirlist
                dirlist = sublist
    except:
        pass

    templist_sorted = sorted(templist, key=lambda x: x[1], reverse=True)
    dirlist.append(((temppath, calc_size(temppath, isfile=False)), templist_sorted))
    # [((dir,size),[(file,size),(file,size)]),((dir,size),[(file,size)])]
    return dirlist


def calc_size(path, isfile=True):
    if isfile:
        return os.path.getsize(path)

    totalsize = 0

    try:
        for direntry in os.scandir(path):
            if direntry.is_file():
                totalsize += calc_size(direntry.path)
            elif direntry.is_dir():
                totalsize += calc_size(direntry.path, False)
        return totalsize
    except:
        return 0


def get_dir_list(dirlist, full=False, number=10):
    dlist = [ditem[0] for ditem in dirlist]
    dlist_sorted = sorted(dlist, key=lambda x: x[1], reverse=True)

    if number > len(dlist_sorted) or full:
        number = len(dlist_sorted)
    elif number <= 0:
        raise Exception('Index overflowed')

    dlist_selected = [dlist_sorted[item] for item in range(0, number)]
    return dlist_selected


def get_dir_list_elem(dirlist, index):
    if index > len(dirlist):
        raise Exception('Index overflowed')
    return dirlist[index][0]


def get_file_list(dirlist, full=False, number=10):
    flist = []
    for ditem in dirlist:
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
    return flist_selected


def get_file_list_elem(filelist, index):
    if index > len(filelist):
        raise Exception('Index overflowed')
    return filelist[index][0]


def calc_depth(path):
    sep = ''
    if os.path.sep == '\\':
        sep = r'\\'
    else:
        sep = os.path.sep
    return len(re.findall(sep, path))


def movein_list(dirlist, index):
    newdirlist = []
    indexcnt = -1
    isstarted = False
    rootdir = dirlist[0][0][0]
    rootdepth = calc_depth(rootdir)

    for ditem in dirlist:
        dirpath = ditem[0][0]
        dirdepth = calc_depth(dirpath)
        reldepth = dirdepth - rootdepth

        if reldepth == 1:
            if isstarted:
                return newdirlist
            else:
                indexcnt += 1
        if index == indexcnt:
            isstarted = True
            newdirlist.append(ditem)
    # Check
    if newdirlist == []:
        raise Exception('Index overflowed')
    else:
        return newdirlist


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
        return f'{size/kb:>5.2f} KB'
    elif mb <= size < gb:
        return f'{size/mb:>5.2f} MB'
    elif gb <= size:
        return f'{size/gb:>5.2f} GB'


def print_treeview(dirlist, collapse=True, level=5):
    dirind = '|   '
    fileind = '    '
    symbol = '├──'
    indexcnt = -1
    collapsecnt = 0
    rootdir = dirlist[0][0][0]
    rootdepth = calc_depth(rootdir)
    if level < 2:
        level = 2

    for i, ditem in enumerate(dirlist):
        dirpath = ditem[0][0]
        dirname = os.path.basename(dirpath)
        dirsize = bytes_convert(ditem[0][1])
        dirdepth = calc_depth(dirpath)
        reldepth = dirdepth - rootdepth

        if i != 0:
            if reldepth == 1:
                indexcnt += 1
                dirname = f'{indexcnt}.{dirname}'

            dirname = f'[{len_adjust(dirname)}]'

            if collapse:
                if reldepth >= level:
                    collapsecnt += 1
                    continue
                elif collapsecnt != 0:
                    print(f'{dirind*level}{symbol} ...{collapsecnt} folders collapsed')
                    collapsecnt = 0

            print(f'{dirind*reldepth}{symbol} {dirname:<{44-len_diff(dirname)}}{dirsize:>12}')
        else:  # print rootdir
            dirname = f'[{len_adjust(dirpath)}]'
            print(f'{dirname:<{48-len_diff(dirname)}}{dirsize:>12}')

        for j, fitem in enumerate(ditem[1]):
            if collapse and i != 0:
                if reldepth >= 3:
                    print(f'{fileind*(reldepth+1)}{symbol} ...{len(ditem[1])} files collapsed')
                    break
                elif j > 2:
                    print(f'{fileind*(reldepth+1)}{symbol} ...{len(ditem[1])-3} files collapsed')
                    break

            filename = len_adjust(fitem[0])
            filesize = bytes_convert(fitem[1])

            print(f'{fileind*(reldepth+1)}{symbol} {filename:<{40-len_diff(filename)}}{filesize:>12}')


def get_dir_tree_elem(dirlist, index):
    indexcnt = -1
    rootdir = dirlist[0][0][0]
    rootdepth = calc_depth(rootdir)

    for ditem in dirlist:
        dirpath = ditem[0][0]
        dirdepth = calc_depth(dirpath)
        reldepth = dirdepth - rootdepth

        if reldepth == 1:
            indexcnt += 1
        if index == indexcnt:
            return dirpath

    raise Exception('Index overflowed')


def print_listview(dirlist):
    [print(f'{i:>3}. {bytes_convert(item[1]):>10}  {item[0]}')
     for i, item in enumerate(dirlist)]
