#!/usr/bin/env python

"""
This program will add an transfrom based on send2url.


"""

# Builtin modules
import os
import os.path
import sys
import zipfile
import tempfile
import shutil
import platform
import glob
from string import Template

# 3rd party modules.
from lxml import etree
from termcolor import colored


disclaimer = "This program is tested on  Maltego carbon and Maltego Chlorine."

template1 = """
<TransformSettings enabled="true" disclaimerAccepted="true" showHelp="false">
    <Properties>
        <Property name="url" type="string" popup="false">$link</Property>
        <Property name="maltego.transform.java-class-name" type="string" popup="false">
            com.paterva.maltego.webtx.WebTxTransform
        </Property>
    </Properties>
</TransformSettings>
"""

template2 = """
<MaltegoTransform name="maltego.transform.$name" displayName="$name" abstract="false" template="false"
                  visibility="public" description="$desc" author="$author" requireDisplayInfo="false">
    <TransformAdapter>
        com.paterva.maltego.transform.runner.test.JavaTransformAdapter
    </TransformAdapter>
    <Properties>
        <Fields>
            <Property name="url" type="string" nullable="false" hidden="false" readonly="false"
                      popup="false" abstract="false" visibility="public" displayName="URL">
                <SampleValue></SampleValue>
            </Property>
            <Property name="maltego.transform.java-class-name" type="string" nullable="false"
                      hidden="false" readonly="true" popup="false" abstract="false"
                      visibility="hidden" displayName="Class">
                <SampleValue></SampleValue>
            </Property>
        </Fields>
    </Properties>
    <InputConstraints>
        <Entity min="1" max="0"/>
    </InputConstraints>
    <OutputEntities/>
    <defaultSets/>
    <StealthLevel>0</StealthLevel>
</MaltegoTransform>
"""

localtas = """
<MaltegoServer name="Local" enabled="true" description="Local transforms hosted on this machine"
               url="http://localhost">
    <LastSync>2015-01-01 00:00:00.000 CEST</LastSync>
    <Protocol version="0.0"/>
    <Authentication type="none"/>
    <Transforms>
    </Transforms>
</MaltegoServer>
"""

def writetransforms(name,link,desc,author,filename):
    """ Lets write the templates """
    out = Template(template1).safe_substitute({'name':name, 'link':link})
    with open(filename + "maltego.transform." + name + ".transformsettings","wb") as f:
        f.write(out)

    out = Template(template2).safe_substitute({'name':name, 'link':link, 'desc':desc, 'author':author})
    with open(filename + "maltego.transform." + name + ".transform","wb") as f:
        f.write(out)


# unzip a file
def unzip(path, directory):
    """
        unzip all files
    """
    zfile = zipfile.ZipFile(path)
    name = ""
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)

        # directory
        if not os.path.exists(directory + "/" + dirname):
            #print "mkdir: " + directory + "/" + dirname
            os.makedirs(directory + "/" + dirname)

        if filename != '':
            with open(directory + "/" + name, 'w') as filehd:
                filehd.write(zfile.read(name))

    zfile.close()



def insert_transform(e, name):
    """
        use this if actions is defined
    """
    #e = etree.SubElement(e, "Transforms")
    name = "maltego.transform." + name
    d = {"name":name}
    e1 = etree.SubElement(e, "Transform", d)
    return e




def doxml(path, name, link):
    """
        write the new stuff to the xml file
    """
    dom = etree.parse(path)
    actions = dom.findall("./Transforms")
    insert_transform(actions[0], name)
    res = etree.tostring(dom)
    with open(path, "wb") as fil:
        fil.write(res)


def zipit(directory):
    """
        Zip all the file into one mtz file
        @todo rewrite to python
    """
    cmd = "cd %s; zip -r test.mtz * 1>/dev/null" % directory
    os.system(cmd)
    print colored("File is done " + directory + "/test.mtz", "blue")


def copyfile(fil):
    """
        Copy the file to a save location
    """
    shutil.copy(fil, "/tmp/" + fil.split("/")[-1])
    return "/tmp/" + fil.split("/")[-1]




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print colored("Usage: send2urlnamed [file.mtz]","red")
        exit()
    print colored(disclaimer,"red")
    infile = sys.argv[1]
    #nfile = copyfile("test.mtz")
    directory = tempfile.mkdtemp()
    unzip(infile, directory)
    #print_entities(directory)
    author  = raw_input("Author        : ")
    name = raw_input("Name          : ")
    link = raw_input("Link          : ")
    desc = raw_input("Description   : ")
    if not os.path.exists(directory + "/TransformRepositories/Local/"):
        os.mkdir(directory + "/TransformRepositories/Local/")
    writetransforms(name,link,desc,author,directory + "/TransformRepositories/Local/")
    #lets check if the local seed file exists.

    if not os.path.exists(directory + "/Servers/Local.tas"):
        with open(directory + "/Servers/Local.tas","wb") as f:
            f.write(localtas)
    doxml(directory + "/Servers/Local.tas", name, link)
    zipit(directory)
