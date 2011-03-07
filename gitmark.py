#!/usr/bin/env python
# encoding: utf-8
"""
gitmark.py

Created by Hilary Mason on 2010-09-24.
Copyright (c) 2010 Hilary Mason. All rights reserved.
"""

import sys, os
import urllib
import re
import hashlib
import subprocess
import imp
from optparse import OptionParser

# XDG Defaults
if 'XDG_CONFIG_HOME' not in os.environ:
    os.environ['XDG_CONFIG_HOME'] = os.path.expandvars('$HOME/.config')
if 'XDG_DATA_HOME' not in os.environ:
    os.environ['XDG_DATA_HOME'] = os.path.expandvars('$HOME/.local/share')
if 'XDG_CACHE_HOME' not in os.environ:
    os.environ['XDG_CACHE_HOME'] = os.path.expandvars('$HOME/.cache')

# Settings from environment or defaults
BASE_PATH = os.environ.get('GITMARK_BASE', os.path.expandvars('$XDG_DATA_HOME/gitmark'))
os.environ['GIT_DIR'] = os.path.join(BASE_PATH, '.git')
os.environ['GIT_WORK_TREE'] = BASE_PATH

TAG_PATH = os.environ.get('GITMARK_TAGS', os.path.join(BASE_PATH, 'tags'))
CONTENT_PATH = os.environ.get('GITMARK_CONTENT', os.path.join(BASE_PATH, 'content'))

# Arguments are passed directly to git, not through the shell, to avoid the
# need for shell escaping. On Windows, however, commands need to go through the
# shell for git to be found on the PATH, but escaping is automatic there. So
# send git commands through the shell on Windows, and directly everywhere else.
USE_SHELL = os.name == 'nt'

class gitMark(object):
    
    def __init__(self, options, args):
        modified = [] # track files we need to add - a hack, because it will add files that are already tracked by git
        
        try:
            url = args[0].strip('/')
        except IndexError, e:
            print >>sys.stderr, ("Error: No url found")
            return

        title = options['title']
        content = None

        if title is None:
            content = self.getContent(url)
            title = self.parseTitle(content)
        content_filename = self.generateHash(url)
        
        tags = ['all']
        tags.extend(options['tags'].split(','))
        for tag in tags:
            t = tag.strip()
            if not t:
                continue
            if '/' in t:
                t = ''.join(t.split('/'))
            modified.append(self.saveTagData(t, url, title, content_filename))

        if content is None:
            content = self.getContent(url)
        modified.append(self.saveContent(content_filename, content))
        self.gitAdd(modified)
        
        commit_msg = options['msg']
        if not commit_msg:
            commit_msg = 'adding %s' % url
        
        self.gitCommit(commit_msg)
        
        if options['push']:
            self.gitPush()

    def gitAdd(self, files):
        subprocess.call(['git', 'add'] + files, shell=USE_SHELL)
        
    def gitCommit(self, msg):
        subprocess.call(['git', 'commit', '-m', msg], shell=USE_SHELL)
        
    def gitPush(self):
        pipe = subprocess.Popen("git push origin master", shell=True)
        pipe.wait()

    def gitInit(self):
        pipe = subprocess.Popen("git init", shell=True)
        pipe.wait()

    def createDirectory(self, path):
        head, tail = os.path.split(path.rstrip('/'))
        if not os.path.exists(head):
            self.createDirectory(head)
        os.mkdir(path, 0755)
        if path == BASE_PATH:
            self.gitInit()

    def saveContent(self, filename, content):
        path = os.path.join(CONTENT_PATH, filename)
        try:
            f = open(path, 'w')
        except IOError, e: #likely the dir doesn't exist
            self.createDirectory(CONTENT_PATH)
            f = open(path, 'w')
            
        f.write(content)
        f.close()
        return path
        
    def saveTagData(self, tag, url, title, content_filename):
        path = os.path.join(TAG_PATH, tag)
        try:
            tag_file = open(path, 'a')
        except IOError, e:
            self.createDirectory(TAG_PATH)
            tag_file = open(path, 'a')
        print >> tag_file, '\t'.join([url, title, content_filename])
        tag_file.close()
        return path

    def parseTitle(self, content):
        re_htmltitle = re.compile(".*<title>(.*)</title>.*")
        t = re_htmltitle.search(content)
        try:
            title = t.group(1)
        except AttributeError:
            title = '[No Title]'
        
        return re.sub('[\t\n]+', ' ', title)
        
    def generateHash(self, text):
        m = hashlib.md5()
        m.update(text)
        return m.hexdigest()
        
    def getContent(self, url):
        try:
            h = urllib.urlopen(url)
            content = h.read()
            h.close()
        except IOError, e:
            print >>sys.stderr, ("Error: could not retrieve the content of a"
                " URL. The bookmark will be saved, but its content won't be"
                " searchable. URL: <%s>. Error: %s" % (url, e))
            content = ''
        return content
        


if __name__ == '__main__':
    parser = OptionParser("usage: %prog [options] <url>")
    parser.add_option("-p", "--push", dest="push", action="store_false", default=True, help="don't push to origin.")
    parser.add_option("-t", "--tags", dest="tags", action="store", default='notag', help="comma seperated list of tags")
    parser.add_option("-m", "--message", dest="msg", action="store", default=None, help="specify a commit message (default is 'adding [url]')")
    parser.add_option("-T", "--title", dest="title", action="store", default=None, help="title of the bookmark (default is the title of the document if html, or else 'No Title')")
    (options, args) = parser.parse_args()
    
    opts = {'push': options.push, 'tags': options.tags, 'msg': options.msg, 'title': options.title}
    
    g = gitMark(opts, args)
