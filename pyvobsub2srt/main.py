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
import sys
from xml.dom.minidom import parse

parser = argparse.ArgumentParser(description='Convert vobsub subtitles into srt format.')
parser.add_argument('file_name', metavar='file_name', type=str, 
                   help='The file name to process')
parser.add_argument('--lang=', dest='lang', type=str, action="store", default="eng",
                   help='The tesseract language to use')
parser.add_argument('--invert=', dest='invert', type=str, action="store", default="auto",
                   help='Should the images be inverted before OCR. (yes|no|auto)')
parser.add_argument('--background=', dest='background', type=str, action="store", default="white",
                   help='What colour should the background be.')
parser.add_argument('--forcedonly', dest='forcedonly', action='store_true',
                   help='Only convert subtitle entries that are forced')

def main():
    args = parser.parse_args()

    if args.file_name is None:
        parser.print_usage()
        return
    elif args.invert not in ("yes", "no", "auto"):
        print "%s is not an invert mode." % (args.lang, )
        print "Options are: %s" % (", ".join(("yes", "no", "auto")), )
        return 1
    else:
        ocr_tools = pyocr.get_available_tools()
        if args.lang not in ocr_tools[0].get_available_languages():
            print "%s is not an available language." % (args.lang, )
            print "Options are: %s" % (", ".join(ocr_tools[0].get_available_languages()), )
            return 1
        
        process_file(args.file_name, ocr_tools, args.lang, args.forcedonly, args.invert, args.background)

def process_file(file_name, ocr_tools, lang, forcedonly=False, invert="auto", background="white"):
    subprocess.call("subp2png -n " + ("--forced " if forcedonly else "") + file_name + " > /dev/null", shell=True)

    dom = parse(file_name + ".xml")

    count = 1
    for subtitle in dom.getElementsByTagName("subtitle"):
        if not subtitle.attributes.has_key("start") or not subtitle.attributes.has_key("stop"):
            continue # Can't do anything with these, probably a dodgy subtitle."
        
        image = get_xml_text(subtitle.getElementsByTagName("image")[0].childNodes)
        
        if invert == "yes":
            subprocess.call("convert " + image + " -background %s -alpha remove -negate " % background + image, shell=True)
        elif invert == "no":
            subprocess.call("convert " + image + " -background %s -alpha remove " % background + image, shell=True)
        else:
            background, negate = should_invert(image)
            subprocess.call("convert " + image + " -background %s -alpha remove%s " % (background, " -negate" if negate else "") + image, shell=True)
        print count
        print "%s --> %s" % (subtitle.attributes["start"].value.replace(".", ","), subtitle.attributes["stop"].value.replace(".", ","))
        print get_subtitle_text(image, ocr_tools, lang).encode("utf8")
        print

        count += 1

def get_subtitle_text(image, ocr_tools, lang):
    return ocr_tools[0].image_to_string(Image.open(image), lang=lang,
                           builder=pyocr.builders.TextBuilder())

# Most DVD subtitles are outlined text, with doesn't ocr well. We need to make sure that the outline is the same colour as the
# background, which sometimes requires us to invert the image.
def should_invert(image):
    img = Image.open(image)
    pixels = img.load()
    
    bg = pixels[(0, 0)]
    outer, inner = None, None
    
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            if pixels[(x, y)] == bg:
                pass
            elif outer is None:
                outer = pixels[(x, y)]
            elif pixels[(x, y)] == outer:
                pass
            else:
                inner = pixels[(x, y)]
                break

    if inner is None:
        return "white" if outer[:3] == (0, 0, 0) else "black", False

    if outer[:3] != (0, 0, 0) and outer[:3] != (255, 255, 255) and \
        inner[:3] != (0, 0, 0) and inner[:3] != (255, 255, 255):
            print "Invalid colours found.", outer, inner
            sys.exit(1)
    return "black" if outer[:3] == (0, 0, 0) else "white", outer[:3] == (0, 0, 0)
    
def get_xml_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
