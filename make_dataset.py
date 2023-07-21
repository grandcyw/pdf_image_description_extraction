"""
Extract the images of a document into the output folder
-------------------------------------------------------------------------------
License: GNU GPL V3
(c) 2018 Jorj X. McKie

Notes
-----
The output.pdf file generated in examples/insert-images is renamed as input.pdf
to be used as the input file in this example.

Usage
-----
python extract-from-pages.py input.pdf

Description
-----------
For a given entry in a page's get_images() list, function "recoverpix"
returns a dictionary like the one produced by "Document.extract_image".

It preprocesses the following special cases:
* The PDF image has an /SMask (soft mask) entry. We use Pillow for recovering
  the original image with an alpha channel in RGBA format.
* The PDF image has a /ColorSpace definition. We then convert the image to
  an RGB colorspace.

The main script part implements the following features:
* Prevent multiple extractions of same image
* Prevent extraction of "unimportant" images, like "too small", "unicolor",
  etc. This can be controlled by parameters.

Apart from above special cases, the script aims to extract images with
their original file extensions. The produced filename is "img<xref>.<ext>",
with xref being the PDF cross reference number of the image.

Dependencies
------------
PyMuPDF v1.18.18
PySimpleGUI, tkinter

Changes
-------
* 2021-09-17: remove PIL and use extended pixmap features instead
* 2020-10-04: for images with an /SMask, we use Pillow to recover original
* 2020-11-21: convert cases with special /ColorSpace definitions to RGB PNG
"""

import io
import os
import sys
import time
import re
import uuid
from queue import *
import fitz

print(fitz.__doc__)



if not tuple(map(int, fitz.version[0].split("."))) >= (1, 18, 18):
    raise SystemExit("require PyMuPDF v1.18.18+")

dimlimit = 0  # 100  # each image side must be greater than this
relsize = 0  # 0.05  # image : image size ratio must be larger than this (5%)
abssize = 2048  # 2048  # absolute image size limit 2 KB: ignore if smaller

pdfdir="C:\imgtest"#把pdfdir下所有pdf的图片和图片描述按页提取到imgpath文件夹下，过滤了前10页和小于2K的图片
imgpath="C:\output"
doclist=[]

for root,dir,files in os.walk(pdfdir):
    for file in files:
        if file.endswith('.pdf'):
            doclist.append(os.path.join(pdfdir,file))

#filename=uuid.uuid4()
filename="dataset"

for fname in doclist:
    print(f'{fname}\t')
    imgdir =os.path.join(imgpath,f'{filename}')   # found images are stored in this subfolder
    txtpath=os.path.join(imgdir,"imgname_des_kvpair.txt")
    if not os.path.exists(imgdir):  # make subfolder if necessary
        os.mkdir(imgdir)


    def recoverpix(doc, item):
        xref = item[0]  # xref of PDF image
        smask = item[1]  # xref of its /SMask

        # special case: /SMask or /Mask exists
        if smask > 0:
            pix0 = fitz.Pixmap(doc.extract_image(xref)["image"])
            if pix0.alpha:  # catch irregular situation
                pix0 = fitz.Pixmap(pix0, 0)  # remove alpha channel
            mask = fitz.Pixmap(doc.extract_image(smask)["image"])

            try:
                pix = fitz.Pixmap(pix0, mask)
            except:  # fallback to original base image in case of problems
                pix = fitz.Pixmap(doc.extract_image(xref)["image"])

            if pix0.n > 3:
                ext = "pam"
            else:
                ext = "png"

            '''return {  # create dictionary expected by caller
                "ext": ext,
                "colorspace": pix.colorspace.n,
                "image": pix.tobytes(ext),
            }'''

        # special case: /ColorSpace definition exists
        # to be sure, we convert these cases to RGB PNG images
        if "/ColorSpace" in doc.xref_object(xref, compressed=True):
            pix = fitz.Pixmap(doc, xref)
            pix = fitz.Pixmap(fitz.csRGB, pix)
            return {  # create dictionary expected by caller
                "ext": "png",
                "colorspace": 3,
                "image": pix.tobytes("png"),
            }
        return doc.extract_image(xref)



    t0 = time.time()
    doc = fitz.open(fname)

    page_count = doc.page_count  # number of pages

    xreflist = []
    imglist = []

    p=0
    with open(txtpath, 'a',encoding='utf-8') as f:
        #f.write(f'----------{fname} figure description extraction begins----------\n')
        f.write("")
    f.close()
    for pno in range(page_count):    
        imgno=0
        queue_img_name=Queue()
        if pno<10:
            continue

        page=doc[pno]
        #print(f'\npage {pno}\n')

        il = doc.get_page_images(pno)
        imglist.extend([x[0] for x in il])
        for img in il:
            xref = img[0]
            if xref in xreflist:
                continue
            width = img[2]
            height = img[3]
            if min(width, height) <= dimlimit:
                continue
            image = recoverpix(doc, img)

            n = image["colorspace"]
            imgdata = image["image"]
        
            if len(imgdata) <= abssize:
                continue
            if len(imgdata) / (width * height * n) <= relsize:
                continue
            img_name=uuid.uuid4()
            imgfile = os.path.join(imgdir, f'{img_name}.{image["ext"]}')
            queue_img_name.put(img_name)
            p=p+1
            fout = open(imgfile, "wb")
            fout.write(imgdata)
            fout.close()
            xreflist.append(xref)

        textlist = page.get_text('blocks')
        #print(textlist)
        check_FigDesc = r"Fig.*"
        check_imgno=r"<image.*"
        imgno=0
        with open(txtpath, 'a',encoding='utf-8') as f:
            #f.write(f'page{pno+1}\n')
            for text in textlist:
                if len(text[4])>=7 and re.match(check_imgno,str(text[4])):
                    imgno=imgno+1
                if len(text[4])>=3 and re.match(check_FigDesc, str(text[4])):
                    while imgno>0 and not queue_img_name.empty():                        
                        f.write(f'<key>{queue_img_name.get()}\n<value>{text[4]}')
                        imgno=imgno-1
        f.close()

    t1 = time.time()
    print(len(xreflist), "images extracted")
    print("total time %g sec" % (t1 - t0))
