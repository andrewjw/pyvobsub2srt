#    This file is part of pyvobsub2srt.
#
#    pyvobsub2srt is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyvobsub2srt is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pyvobsub2srt.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import glob
from PIL import Image
import pyocr
import subprocess
from xml.dom.minidom import parse

parser = argparse.ArgumentParser(description='Convert vobsub subtitles into srt format.')
parser.add_argument('file_name', metavar='file_name', type=str, 
                   help='The file name to process')
parser.add_argument('--lang=', dest='lang', type=str, action="store", default="eng",
                   help='The tesseract language to use')
parser.add_argument('--forcedonly', dest='forcedonly', action='store_true',
                   help='Only convert subtitle entries that are forced')

def main():
    args = parser.parse_args()

    if args.file_name is None:
        parser.print_usage()
        return
    else:
        ocr_tools = pyocr.get_available_tools()
        if args.lang not in ocr_tools[0].get_available_languages():
            print "%s is not an available language." % (args.lang, )
            print "Options are: %s" % (", ".join(ocr_tools[0].get_available_languages()), )
            return 1
        
        process_file(args.file_name, ocr_tools, args.lang, args.forcedonly)

def process_file(file_name, ocr_tools, lang, forcedonly=False):
    subprocess.call("subp2png -n " + ("--forced " if forcedonly else "") + file_name + " > /dev/null", shell=True)

    dom = parse(file_name + ".xml")

    count = 1
    for subtitle in dom.getElementsByTagName("subtitle"):
        print count
        print "%s --> %s" % (subtitle.attributes["start"].value.replace(".", ","), subtitle.attributes["stop"].value.replace(".", ","))
        print get_subtitle_text(get_xml_text(subtitle.getElementsByTagName("image")[0].childNodes), ocr_tools, lang).encode("utf8")
        print

        count += 1

def get_subtitle_text(image, ocr_tools, lang):
    return ocr_tools[0].image_to_string(Image.open(image), lang=lang,
                           builder=pyocr.builders.TextBuilder())

def get_xml_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
