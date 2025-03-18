import os, sys
import json
import shutil
import re

BEGIN_FRAG = '<script class="tiddlywiki-tiddler-store" type="application/json">'
END_FRAG = '</script><div id="storeArea" style="display:none;"></div>'
FILE_LINK = '../cafe.html'

ROOT_FOLDER = 'data'

IMGS_URL = "https://daidalvi.github.io/coffee/"

CODE_LANGS = ["sql", "python", "php", "Node.js", "html", "git", "eclipse", "c++", "batch", "bat"]

class ZGen():

    def getRootDir(self):
        
        try:
            return os.path.dirname(os.path.abspath(__file__))       
        except Exception:
            return os.path.dirname(sys.executable)   
        
    def cleanFileName(self, f):
        #for symbol in ["?", "!", ","]:
        #    f = f.replace(symbol, "-")
        #return f
        return re.sub('[^А-Яа-яЁё☕⚜✡ॐA-Za-z0-9\.]+', '-', f)
    
    def clean_tags(self, text):
        res = re.findall(r'(?<=\[\[)(.*?)(?=\]\])', text)
        #res = re.findall(r'(?<=\[\[)(.*?)\|(.*?)(?=\]\])', text)
        for r in res:
            if "|" in r:
                rs = r.split("|")
                text = text.replace("[[%s]]"%r, "[[%s|%s]]"%(self.cleanFileName(rs[1]), rs[0]))
            elif " " in r:
                text = text.replace("[[%s]]"%r, "[[%s]]"% self.cleanFileName(r))

        return text
    
    def cleanhtml(self, raw_html):
        raw_html = raw_html.replace("<br />", "\n").replace("<br>", "\n").replace("<br >", "\n")
        raw_html = raw_html.replace("<hr />", "\n---\n")

        CLEANR = re.compile('<.*?>') 
        cleantext = re.sub(CLEANR, '', raw_html)
        return cleantext

    def modify_content(self, dt):

        text = dt["text"]

        text = self.cleanhtml(text)

        if "{{!!image}}" in text and "image" in dt.keys():
            text = text.replace("{{!!image}}", IMGS_URL+dt["image"])

        text = text.replace("{{", "![[").replace("}}", "]]")

        text = self.clean_tags(text)
     
        return text

    
    def run(self):

        subfolders= [f.path for f in os.scandir(os.path.join(self.getRootDir(), ROOT_FOLDER)) if f.is_dir()]
        for dirname in list(subfolders):
            if not dirname.endswith(".obsidian"):
                print("REMOVE :"+dirname)
                shutil.rmtree(dirname, ignore_errors=True)

        flink = os.path.join(self.getRootDir(), FILE_LINK)
        f = open(flink, 'r', encoding="utf-8")
        raw_data = f.read()
        f.close()

        raw_data = raw_data.split(BEGIN_FRAG)[1].split(END_FRAG)[0]

        #print(raw_data.encode(sys.stdout.encoding, errors='replace'))
        data = json.loads(raw_data)
        for dt in data:

            if dt["title"][:3] == "$:/" or "text" not in dt:
                continue

            title  = self.cleanFileName(dt["title"])

            if title in ["Images"]:
                continue

            mtype = ""

            tags = []

            mpath = "other"
            if "tags" not in dt.keys():
                mpath = "untagged"
            else:
                tags = dt["tags"].split(" ")
                if "санскрит" in tags:
                    mtype = "санскрит"
                    mpath= "санскрит"
                    for t in ["деванагари", "грамматика", "мантра", "шлока"]:
                        if t in tags:
                            mpath +="/"+t
                            break
                    if "/" not in mpath:
                        mpath += "/Другое"
                else:
                    found = False

                    for t in CODE_LANGS:
                        if t in tags:
                            mpath ="code/"+t
                            mtype = "code"
                            found = True
                            break

                    if not found:
                        for t in ["linux", "windows", "virtualbox", "meri"]:
                            if t in tags:
                                mpath ="admin/"+t
                                mtype = "admin"
                                found = True
                                break

                    if not found:
                        for t in ["LHD", "Пак Звезда", "МУКЭП", "АРМ"]:
                            if t in tags:
                                mpath ="project/"+t
                                mtype = "project"
                                found = True
                                break


                    if not found:
                        for t in ["zest", "wiki"]:
                            if t in tags:
                                mpath ="zest/"+t
                                mtype = "zest"
                                found = True
                                break

                    
                    if not found:
                        for t in ["разное"]:
                            if t in tags:
                                mpath ="x/"+t
                                found = True
                                break

            fields = ""
            fields_adds = ""
            for key, value in dt.items():
                if key not in ["title", "text", "saved-text", "creator", "modifier", "description"]:

                    if not value.strip():
                        continue

                    #comment
                    value = self.clean_tags(value)

                    if key == "tags":

                        value = value.replace("[[", "").replace("]]", "")

                        #fields_adds += "taglinks: [[" +value.replace(" ", "]] [[")+ "]]\n"
                        fields_adds += 'taglinks:\n  - "[[' +value.replace(" ", ']]"\n  - "[[')+ ']]"\n'


                        value = "\n  - "+value.replace(" ", "\n  - ")

                    elif key == "list" and "role" in dt.keys() and dt["role"] == "comment":

                        val = value.split(" ")
                        new_vs = list()
                        for v in val:
                            if "[" not in v:
                                v = "[[%s]]" % v
                            new_vs.append(v)
                        value = " ".join(new_vs)
                        value = value.replace("[[", '"[[').replace("]]", ']]"')
                        

                    fields += key+": "+value+"\n"


            content = "---\n"+"\n"+fields+fields_adds+"---\n"

            if "description" in dt.keys():
                content +=  "> [!NOTE] description\n>" + self.clean_tags(dt['description']).replace("\n", "\n>")+"\n\n"

            content += self.modify_content(dt)


            #if mtype == "code":
            #    content +=   "\n\n````query\n[list: ("+title+")]\n```\n"
            #elif mtype != "mtype" :
            #    content +=   "\n\n````query\n[tag: "+title+"]\n```\n"
            #if mtype == "code":
            #    for t in CODE_LANGS:
            #        if t in tags:
            #            content +=   "\n\n````query\n[tag: ("+t+")]\n```\n"

            fdir = os.path.join(self.getRootDir(), ROOT_FOLDER, mpath)
            os.makedirs(fdir, exist_ok=True)
            #print(os.path.join(fdir, title))
            f = open(os.path.join(fdir, title+".md"), 'w', encoding="utf-8")  # open file in append mode
            f.write(content)
            f.close()

"""
---
date: 12.04.2024
link: "[[хва]]"
tags:
  - дваСлова
  - тег3
---
34234234

![[Pasted image 11.png]]
"""            



ZGen().run()