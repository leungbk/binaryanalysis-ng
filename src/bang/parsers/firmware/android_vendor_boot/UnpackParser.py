# Binary Analysis Next Generation (BANG!)
#
# This file is part of BANG.
#
# BANG is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation.
#
# BANG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License, version 3, along with BANG.  If not, see
# <http://www.gnu.org/licenses/>
#
# Copyright Armijn Hemel
# Licensed under the terms of the GNU Affero General Public License
# version 3
# SPDX-License-Identifier: AGPL-3.0-only

import os
import pathlib

from bang.UnpackParser import UnpackParser, check_condition
from bang.UnpackParserException import UnpackParserException
from kaitaistruct import ValidationNotEqualError
from . import android_vendor_boot


class AndroidVendorBootUnpackParser(UnpackParser):
    extensions = []
    signatures = [
        (0, b'VNDRBOOT')
    ]
    pretty_name = 'android_vendor_boot'

    def parse(self):
        try:
            self.data = android_vendor_boot.AndroidVendorBoot.from_io(self.infile)
        except (Exception, ValidationNotEqualError) as e:
            raise UnpackParserException(e.args)

    def unpack(self, meta_directory):
        file_path = pathlib.Path('vendor_ramdisk')
        with meta_directory.unpack_regular_file(file_path) as (unpacked_md, outfile):
            outfile.write(self.data.vendor_ramdisk)
            yield unpacked_md

        file_path = pathlib.Path('dtb')
        with meta_directory.unpack_regular_file(file_path) as (unpacked_md, outfile):
            outfile.write(self.data.dtb)
            yield unpacked_md

    labels = ['android vendor boot', 'android']

    @property
    def metadata(self):
        metadata = {
            'commandline': self.data.header.commandline
        }
        return metadata
