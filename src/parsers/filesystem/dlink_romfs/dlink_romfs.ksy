meta:
  id: dlink_romfs
  title: D-Link ROMFS format
  license: MIT
  endian: le
  encoding: ASCII
doc: |
  File system used by D-Link in certain routers, such as DIR-600. This is
  apparently a modified version of the romfs file system used in eCos.
doc-ref:
  - https://raw.githubusercontent.com/ReFirmLabs/binwalk/ec47069/src/binwalk/plugins/dlromfsextract.py
  - http://web.archive.org/web/20201208093903/https://github.com/syschmod/dlink_patch_utils/wiki/D-Link-GO-RT-N150---vulnerabilities-and-firmware-modification
  - https://github.com/antmicro/ecos-openrisc/blob/0891c1c/packages/fs/rom/current/src/romfs.c
seq:
  - id: super_block
    type: super_block
    size: 32
  - id: first_entry
    type: entry
  - id: entries
    type: entry
    repeat: until
    repeat-until: _io.pos == first_entry.ofs_entry
types:
  super_block:
    seq:
      - id: magic
        contents: "\x2emoR"
      - id: unknown1
        type: u4
      - id: unknown2
        type: u4
      - id: unknown3
        type: u4
      - id: signature
        type: signature
        size: 16
    doc-ref: https://github.com/antmicro/ecos-openrisc/blob/0891c1c/packages/fs/rom/current/src/romfs.c#L302
  signature:
    seq:
      - id: romfs_name
        contents: "ROMFS v"
      - id: version
        type: version
        size: 3
  version:
    seq:
      - id: major_version
        size: 1
        type: str
      - id: separator
        contents: "."
      - id: minor_version
        size: 1
        type: str
    instances:
      major:
        value: major_version.to_i
      minor:
        value: minor_version.to_i
  entry:
    seq:
      - id: entry_type
        type: u4
      - id: num_links
        type: u4
      - id: owner
        type: u2
      - id: group
        type: u2
      - id: len_entry
        type: u4
      - id: ctime
        type: u4
      - id: ofs_entry
        type: u4
      - id: len_decompressed
        type: u4 
      - id: entry_uid
        size: 4
        type: str
    doc-ref: https://github.com/antmicro/ecos-openrisc/blob/0891c1c/packages/fs/rom/current/src/romfs.c#L273
    instances:
     is_compressed:
       value: entry_type & 0x5b0000 == 0x5b0000
     is_directory:
       value: entry_type & 0x1 == 0x1
     is_data:
       value: entry_type & 0x8 == 0x8
     uid:
       value: entry_uid.to_i
     data:
       pos: ofs_entry
       size: len_entry