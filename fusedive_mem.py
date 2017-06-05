import os
import sys
import llfuse
import errno
import stat
from time import time
import sqlite3
import logging
from collections import defaultdict
from llfuse import FUSEError
from argparse import ArgumentParser
import dropbox
import subprocess
import requests

from tmpfs import Operations as TmpOperations
from tmpfs import init_logging

from os import fsencode, fsdecode

from crypto import get_fernet

DEFAULT_DIR_MODE = stat.S_IFDIR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | \
                   stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
DEFAULT_FILE_MODE = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | \
                    stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

fernet = ''

class Ctx(object):
    def __init__(self, uid, gid):
        self.uid = uid
        self.gid = gid


class Field(object):
    def __init__(self):
        self.update_size = False
        self.update_mode = False
        self.update_uid = False
        self.update_gid = False
        self.update_atime = False
        self.update_mtime = False


class Attr(object):
    pass


class DropboxOperations(TmpOperations):
    def __init__(self, dbx, tmpdir):
        super().__init__()
        self.dbx = dbx
        self.tmpdir = tmpdir
        self._path2inode = {}
        self._inode2path = {}
        self._mark = {}
        self._set_inode_path(llfuse.ROOT_INODE, '/')
        # self._inode2path = {llfuse.ROOT_INODE: '/'}
        # self._path2inode = {'/': llfuse.ROOT_INODE}
        # self._init_dropbox()

    def _set_inode_path(self, inode, name, mark = 0):
        self._inode2path[inode] = name
        self._path2inode[name] = inode
        self._mark[inode] = mark
        print("> " + str(self._path2inode[name]) + ", " + self._inode2path[inode])

    def _init_dropbox(self):
        y = self.dbx.files_list_folder('', recursive=True)
        while 1:
            for metadata in y.entries:
                path_lower = metadata.path_lower.split('/')
                assert path_lower[0] == ''
                path_lower = list(map(fsencode, path_lower))
                tinode = llfuse.ROOT_INODE
                name = None
                size = None
                if isinstance(metadata, dropbox.files.FolderMetadata):
                    pass
                else:
                    assert isinstance(metadata, dropbox.files.FileMetadata)
                    name = fsencode(metadata.name)
                    size = metadata.size
                    path_lower = path_lower[:-1]

                if len(path_lower) > 1:
                    for foldern in path_lower[1:]:
                        try:
                            tinode = self.lookup(tinode, foldern).st_ino
                        except FUSEError:
                            tinode = self._virtual_mkdir(tinode, foldern, DEFAULT_DIR_MODE, Ctx(os.getuid(), os.getgid())).st_ino

                if isinstance(metadata, dropbox.files.FileMetadata):
                    ino, _ = self._virtual_create(tinode, name, DEFAULT_FILE_MODE, flags=None, ctx=Ctx(os.getuid(), os.getgid()))
                    field = Field()
                    field.update_size = True
                    attr = Attr()
                    attr.st_size = size
                    self.setattr(ino, attr, field, None, None)
                else:
                    assert isinstance(metadata, dropbox.files.FolderMetadata)
                    pass
            if y.has_more:
                y = self.dbx.files_list_folder_continue(y.cursor)
            else:
                break

    def _virtual_create(self, inode_parent, name, mode, flags, ctx):
        tpath = self._inode2path[inode_parent] + fsdecode(name)
        ret = super().create(inode_parent, name, mode, flags, ctx)
        self._set_inode_path(ret[0], tpath)
        # self._inode2path[ret[0]] = tpath
        # self._path2inode[tpath] = ret[0]
        # self._mark[ret[0]] = True
        return ret

    def _virtual_mkdir(self, inode_p, name, mode, ctx):
        tpath = self._inode2path[inode_p] + fsdecode(name) + '/'
        ret = super().mkdir(inode_p, name, mode, ctx)
        self._set_inode_path(ret.st_ino, tpath)
        # self._inode2path[ret.st_ino] = tpath
        # self._path2inode[tpath] = ret.st_ino
        # self._mark[ret.st_ino] = True
        return ret


    def opendir(self, inode, ctx):
        path = self._inode2path[inode]
        y = self.dbx.files_list_folder(path[1:], recursive=False)
        while 1:
            for metadata in y.entries:
                path_lower = metadata.path_lower.split('/')
                assert path_lower[0] == ''
                path_lower = list(map(fsencode, path_lower))
                tinode = llfuse.ROOT_INODE
                exist = False
                name = None
                size = None
                if isinstance(metadata, dropbox.files.FolderMetadata):
                    pass
                else:
                    assert isinstance(metadata, dropbox.files.FileMetadata)
                    # print ("< " + metadata.path_lower)
                    for tno in self._inode2path:
                        # print("> " + self._inode2path[tno])
                        if (metadata.path_lower == self._inode2path[tno]):
                            self._mark[tno] = 1
                            exist = True
                            break
                    name = fsencode(metadata.name)
                    size = metadata.size
                    path_lower = path_lower[:-1]

                if len(path_lower) > 1:
                    for foldern in path_lower[1:]:
                        try:
                            tinode = self.lookup(tinode, foldern).st_ino
                            self._mark[tinode] = 1
                        except FUSEError:
                            tinode = self._virtual_mkdir(tinode, foldern, DEFAULT_DIR_MODE, Ctx(os.getuid(), os.getgid())).st_ino
                            self._mark[tinode] = 1

                if isinstance(metadata, dropbox.files.FileMetadata) and not exist:
                    # name is fsencode
                    # print ("fsencode" + name)
                    ino, _ = self._virtual_create(tinode, name, DEFAULT_FILE_MODE, flags=None, ctx=Ctx(os.getuid(), os.getgid()))
                    field = Field()
                    field.update_size = True
                    attr = Attr()
                    attr.st_size = size
                    self.setattr(ino, attr, field, None, None)
                    self._mark[ino] = 1
                else:
                    pass
            if y.has_more:
                y = self.dbx.files_list_folder_continue(y.cursor)
            else:
                break


        entrys = self.listdir(inode, 0)
        for entry in entrys:
            ine = entry[0]
            by_name = entry[1]
            name = fsdecode(by_name)
            if (name == '.' or name == '..'):
                continue
            if (self._mark[ine] == 0):
                print (name + " : " + str(ine))
                mode = self.getattr(ine).st_mode
                # ctx=Ctx(os.getuid(), os.getgid())
                entry = super().lookup(inode, by_name)
                super()._remove(inode, by_name, entry)
                if (mode == DEFAULT_DIR_MODE):
                    print ("Default dir mode")
                    # self.rmdir(ine, by_name, ctx)
                    # super().rmdir(ine, by_name, ctx)
                    # super()._remove(ine, by_name, ctx)
                elif (mode == DEFAULT_FILE_MODE):
                    print ("Defualt file mode")
                    # self.unlink(ine, by_name, ctx)
                    # super._remove(ine, by_name, ctx)
                    # super().unlink(ine, by_name, ctx)

        for ine in self._inode2path:
            self._mark[ine] = 0

        return super().opendir(inode, ctx)


    def create(self, inode_parent, name, mode, flags, ctx):
        ret = self._virtual_create(inode_parent, name, mode, flags, ctx)
        ino = ret[0]
        self.dbx.files_upload(b'', self._inode2path[ino], mode=dropbox.files.WriteMode.overwrite)
        return ret

    def mkdir(self, inode_p, name, mode, ctx):
        ret = self._virtual_mkdir(inode_p, name, mode, ctx)
        ino = ret.st_ino
        self.dbx.files_create_folder(self._inode2path[ino][:-1])
        return ret

    def rename(self, inode_p_old, name_old, inode_p_new, name_new, ctx):
        #assert inode_p_old==inode_p_new
        super().rename(inode_p_old, name_old, inode_p_new, name_new, ctx)
        name_old = name_old.decode('utf-8')
        name_new= name_new.decode('utf-8')
        self.dbx.files_move(self._inode2path[inode_p_old]+name_old,self._inode2path[inode_p_new]+name_new)
        path_old = self._inode2path[inode_p_old] + name_old
        path_new = self._inode2path[inode_p_new] + name_new
        # print(path_old)
        if not (path_old in self._path2inode): # it is a directory(it has a '/')
            path_old += '/'
            path_new += '/'
        node = self._path2inode[path_old]
        self._path2inode.pop(path_old)
        self._set_inode_path(node, path_new)
        # self._inode2path[node] = path_new
        # self._path2inode[path_new] = node
        # self._mark[node] = True
        # print(self._inode2path)
        # print(self._path2inode)

        print("RENAME!!!!!")

    def read(self, fh, offset, length):
        tmppath = os.path.join(self.tmpdir, self._inode2path[fh].replace('/', '-'))
        if not os.path.exists(tmppath):
            self.dbx.files_download_to_file(tmppath, self._inode2path[fh])
            with open(tmppath, 'rb') as f:
                content = f.read()
            with open(tmppath, 'wb') as f:
                f.write(fernet.decrypt(content))
        with open(tmppath, 'rb') as f:
            f.read(offset)
            return f.read(length)

    def write(self, fh, offset, buf):
        tmppath = os.path.join(self.tmpdir, self._inode2path[fh].replace('/', '-'))
        with open(tmppath, 'wb+') as f:
            f.seek(0)
            f.seek(offset)
            res = f.write(buf)
            # print(offset, buf)
        with open(tmppath, 'rb') as f:
            f_crypted = fernet.encrypt(f.read())
            self.dbx.files_upload(f_crypted, self._inode2path[fh], mode=dropbox.files.WriteMode.overwrite)
        # return res
        return super().write(fh, offset, buf)

    def rmdir(self, inode_p, name, entry):
        ino = self.lookup(inode_p, name).st_ino
        tpath = self._inode2path[ino]
        super().rmdir(inode_p, name, entry)
        self.dbx.files_delete(tpath[:-1])

    def unlink(self, inode_p, name, ctx):
        ino = self.lookup(inode_p, name).st_ino
        tpath = self._inode2path[ino]
        super().unlink(inode_p, name, ctx)
        self.dbx.files_delete(tpath)


def main():
    global fernet
    parser = ArgumentParser()
    parser.add_argument('mountpoint', type=str,
                        help='Where to mount the file system')
    parser.add_argument('token', type=str,
                        help='Token of dropbox app')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debugging output')
    parser.add_argument('--debug-fuse', action='store_true', default=False,
                        help='Enable FUSE debugging output')
    parser.add_argument('--tmpdir', type=str, default='/tmp/fusedive',
                        help='Temporary local path')
    options = parser.parse_args()

    subprocess.Popen(('mkdir -p %s' % (options.tmpdir)).split())

    init_logging(options.debug)
    dbx = dropbox.Dropbox(options.token)
    fernet = get_fernet(options.token)
    operations = DropboxOperations(dbx, options.tmpdir)

    pros = {
            'http':     "socks5://127.0.0.1:1080",
            'https':    "socks5://127.0.0.1:1080"
            }
    sess = dropbox.create_session(max_connections=3, proxies=pros)
    dbx = dropbox.Dropbox(options.token, session=sess)
    operations = DropboxOperations(dbx, options.tmpdir)

    fuse_options = set(llfuse.default_options)
    fuse_options.add('fsname=dropboxfs')
    fuse_options.discard('default_permissions')
    if options.debug_fuse:
        fuse_options.add('debug')
    llfuse.init(operations, options.mountpoint, fuse_options)

    # sqlite3 does not support multithreading
    try:
        llfuse.main(workers=1)
    except:
        subprocess.Popen(('rm -rf %s' % (options.tmpdir)).split())
        llfuse.close()
        raise

    subprocess.Popen(('rm -rf %s' % (options.tmpdir)).split())
    llfuse.close()


if __name__ == '__main__':
    main()
