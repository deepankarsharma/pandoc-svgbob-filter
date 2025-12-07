#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import subprocess as sp
import panflute as pf
from shutil import which


class SvgbobInline(object):
    """
    Converts CodeBlock or Link with svgbob class to Image
    requires `svgbob` in PATH
    option can be provided as attributes or can set default values in yaml metadata block

    option          | metadata              | default
    ----------------|-----------------------|----------
    font-family     | svgbob.font-family    | "Arial"
    font-size       | svgbob.font-size      | 14
    scale           | svgbob.scale          | 1
    stroke_width    | svgbob.stroke-width   | 2

    """

    def __init__(self):
        self.dir_to = "svg"
        # Support both svgbob_cli (newer) and svgbob (older) binary names
        if which("svgbob_cli"):
            self.svgbob_cmd = "svgbob_cli"
        elif which("svgbob"):
            self.svgbob_cmd = "svgbob"
        else:
            raise AssertionError("svgbob or svgbob_cli is not in path")

    def get_options(self, attributes, doc):
        """Extract svgbob options from attributes and metadata."""
        meta_font_family = doc.get_metadata("svgbob.font-family", "Arial")
        meta_font_size = doc.get_metadata("svgbob.font-size", 14)
        meta_scale = doc.get_metadata("svgbob.scale", 1)
        meta_stroke_width = doc.get_metadata("svgbob.stroke-width", 2)

        font_family = attributes.get("font-family", meta_font_family)
        font_size = attributes.get("font-size", meta_font_size)
        scale = attributes.get("scale", meta_scale)
        stroke_width = attributes.get("stroke-width", meta_stroke_width)

        svgbob_option = " ".join([
            '--font-family "{}"'.format(font_family) if font_family is not None else "",
            "--font-size {}".format(font_size) if font_size is not None else "",
            "--scale {}".format(scale) if scale is not None else "",
            "--stroke-width {}".format(stroke_width) if stroke_width is not None else "",
            '--background "#fdf6e3"',
        ])
        return svgbob_option

    def process_codeblock(self, elem, doc):
        """Process a CodeBlock with svgbob class."""
        if not os.path.exists(self.dir_to):
            os.mkdir(self.dir_to)

        data = elem.text
        counter = hashlib.sha1(data.encode("utf-8")).hexdigest()[:8]
        self.basename = "/".join([self.dir_to, str(counter)])

        _format = "svg"
        linkto = os.path.abspath(".".join([self.basename, _format])).replace("\\", "/")

        svgbob_option = self.get_options(elem.attributes, doc)

        command = "{} {} -o {}".format(self.svgbob_cmd, svgbob_option, linkto)
        pf.debug(command)

        proc = sp.Popen(command, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        proc.communicate(input=data.encode("utf-8"))

        pf.debug("[codeblock] generate svgbob to {}".format(linkto))

        elem.classes.remove("svgbob")
        return pf.Para(pf.Image(url=linkto, classes=elem.classes,
                                identifier=elem.identifier, attributes=elem.attributes))

    def action(self, elem, doc):
        if isinstance(elem, pf.CodeBlock) and "svgbob" in elem.classes:
            return self.process_codeblock(elem, doc)
        elif isinstance(elem, pf.Link) and "svgbob" in elem.classes:
            fn = elem.url
            caption = elem.content

            if not os.path.exists(self.dir_to):
                os.mkdir(self.dir_to)

            data = open(fn, "r", encoding="utf-8").read()
            counter = hashlib.sha1(data.encode("utf-8")).hexdigest()[:8]
            self.basename = "/".join([self.dir_to, str(counter)])

            _format = "svg"
            fn = os.path.abspath(fn)
            linkto = os.path.abspath(".".join([self.basename, _format])).replace("\\", "/")

            svgbob_option = self.get_options(elem.attributes, doc)
            command = "{} {} {} -o {}".format(self.svgbob_cmd, fn, svgbob_option, linkto)
            pf.debug(command)
            sp.Popen(command, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

            pf.debug("[inline] generate svgbob from {} to {}".format(fn, linkto))
            elem.classes.remove("svgbob")
            return pf.Image(*caption, classes=elem.classes, url=linkto,
                            identifier=elem.identifier, title="fig:", attributes=elem.attributes)


def main(doc=None):
    si = SvgbobInline()
    pf.run_filters([si.action], doc=doc)
    return doc


if __name__ == "__main__":
    main()
