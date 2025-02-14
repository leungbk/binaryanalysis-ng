import os

from UnpackParserException import UnpackParserException
from UnpackResults import UnpackResults
from FileResult import FileResult

import os
import pathlib

class OffsetInputFile:
    def __init__(self, infile, offset):
        self.infile = infile
        self.offset = offset

    def __getattr__(self, name):
        return self.infile.__getattribute__(name)

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            return self.infile.seek(offset + self.offset, whence)
        return self.infile.seek(offset, whence)

    def tell(self):
        return self.infile.tell() - self.offset



class UnpackParser:
    """The UnpackParser class can parse input according to a certain format,
    and unpack any content from it if necessary.

    You can make an UnpackParser by deriving a class from UnpackParser and
    defining:

    extensions:
        a list of file extensions. These are strings with which the file
        needs to end. Default is empty.

    signatures:
        a list of tuples of the form (offset, bytestring), e.g.
        (0x54, b'\\x00AB\\x0a'). Default is empty.

    scan_if_featureless:
        a boolean that indicates that files for this UnpackParser do not
        always have an extension or a signature. Text-based formats often
        need this. Default is False.

    pretty_name:
        a name of the file type, used in the unpack directory name and in
        logs. There is no default.

    Override any methods if necessary.
    """
    extensions = []

    signatures = []
    scan_if_featureless = False

    def __init__(self, fileresult, scan_environment, rel_unpack_dir, offset):
        """Constructor. All constructor arguments are available as object
        fields of the same name.
        """
        self.unpacked_size = 0
        self.unpack_results = UnpackResults()
        self.fileresult = fileresult
        self.scan_environment = scan_environment
        self.rel_unpack_dir = rel_unpack_dir
        self.offset = offset
    def parse(self):
        """Override this method to implement parsing the file data. If there is
        a (non-fatal) error during the parsing, you should raise an
        UnpackParserException.
        """
        raise UnpackParserException("%s: undefined parse method" % self.__class__.__name__)
    def parse_from_offset(self):
        """Parses the data from a file pointed to by fileresult, starting from
        offset. Normally you do not need to override this.
        """
        self.infile.seek(0)
        self.parse()
        self.calculate_unpacked_size()
        check_condition(self.unpacked_size > 0, 'Parser resulted in zero length file')
    def open(self):
        filename_full = self.scan_environment.get_unpack_path_for_fileresult(
                    self.fileresult)
        f = filename_full.open('rb')
        self.infile = OffsetInputFile(f, self.offset)
    def close(self):
        self.infile.close()
    def calculate_unpacked_size(self):
        """Override this to calculate the length of the file data that is
        extracted. Needed if you call the UnpackParser to extract (carve)
        data that is contained in another file or if the parse method does
        not read the entire content and you need a custom length calculation.
        You must assign the length to self.unpacked_size.
        """
        self.unpacked_size = self.infile.tell()
    def parse_and_unpack(self):
        """Parses the file and unpacks any contents into other files. Files are
        stored in the filesandlabels field of the self.unpack_results
        dictionary.
        You normally do not need to override this method. Any
        UnpackParserExceptions that are raised are assumed to be non-fatal,
        i.e. the program can continue. Other exceptions are not assumed to be
        handled and may cause the program to abort.
        """

        self.parse_from_offset()
        self.unpack_results.set_length(self.unpacked_size)
        self.set_metadata_and_labels()
        unpacked_files = self.unpack()
        self.unpack_results.set_unpacked_files(unpacked_files)
        return self.unpack_results

    @classmethod
    def get_carved_filename(cls):
        """Override this to change the name of the unpacked file if it is
        carved. Default is unpacked.<pretty_name>.
        """
        return "unpacked.%s" % cls.pretty_name

    def carve(self):
        """If the UnpackParser recognizes data but there is still data left in
        the file, this method saves the parsed part of the file, leaving the
        rest to be  analyzed. The part is saved to the unpack data directory,
        under the name given by get_carved_filename.
        """
        rel_output_path = self.rel_unpack_dir / self.get_carved_filename()
        abs_output_path = self.scan_environment.unpack_path(rel_output_path)
        os.makedirs(abs_output_path.parent, exist_ok=True)
        outfile = open(abs_output_path, 'wb')
        # Although self.infile is an OffsetInputFile, fileno() will give the file
        # descriptor of the backing file. Therefore, we need to specify self.offset here
        os.sendfile(outfile.fileno(), self.infile.fileno(), self.offset, self.unpacked_size)
        outfile.close()
        self.unpack_results.add_label('unpacked')
        out_labels = self.unpack_results.get_labels() + ['unpacked']
        fr = FileResult(self.fileresult, rel_output_path, set(out_labels))
        self.unpack_results.add_unpacked_file( fr )
    def set_metadata_and_labels(self):
        """Override this method to set metadata and labels."""
        self.unpack_results.set_labels([])
        self.unpack_results.set_metadata({})
    def unpack(self):
        """Override this method to unpack any data into subfiles.
        The filenames are relative to the unpack directory root that the
        scan_environment points to (usually this is a file under unpack_dir).
        Must return a list of FileResult objects.
        For (non-fatal) errors, you should raise a UnpackParserException.
        """
        return []
    @classmethod
    def is_valid_extension(cls, ext):
        return ext in cls.extensions
    def extract_to_file(self, filename, start, length):
        """Extracts data from the input stream, starting at start, of length
        length, to the file pointed to by filename.
        filename is a path, relative to the unpack root directory.,
        start is relative to the beginning of the input stream. If the file
        data is assumed to start at an offset in the input stream, you will
        need to add this offset when calling this method.
        """
        outfile_full = self.scan_environment.unpack_path(filename)
        os.makedirs(outfile_full.parent, exist_ok=True)
        outfile = open(outfile_full, 'wb')
        os.sendfile(outfile.fileno(), self.infile.fileno(), self.infile.offset + start, length)
        outfile.close()

class WrappedUnpackParser(UnpackParser):
    """Wrapper class for unpack functions.
    To wrap an unpack function, derive a class from WrappedUnpackParser and
    override the method unpack_function.
    """
    def unpack_function(self, fileresult, scan_environment, offset, unpack_dir):
        """Override this method to call the unpack function and return the
        result, e.g.:
            return unpack_foobar(fileresult, scan_environment, offset,
                    unpack_dir)
        Unpack results that have the status field set to False are converted
        to an UnpackParserException automatically by parse_and_unpack.
        """
        raise UnpackParserException("%s: must call unpack function" % self.__class__.__name__)
    def parse_and_unpack(self):
        r = self.unpack_function(self.fileresult, self.scan_environment,
                self.offset, self.rel_unpack_dir)
        if r['status'] is False:
            raise UnpackParserException(r.get('error'))
        return self.get_unpack_results_from_dictionary(r)
    def open(self):
        pass
    def close(self):
        pass
    def carve(self):
        pass
    def get_unpack_results_from_dictionary(self,r):
        unpack_results = UnpackResults()
        unpack_results.set_length(r['length'])
        frs = [ FileResult(self.fileresult, pathlib.Path(x[0]), set(x[1]))
                for x in r['filesandlabels'] ]
        unpack_results.set_unpacked_files(frs)
        unpack_results.set_offset(r.get('offset'))
        unpack_results.set_labels(r.get('labels', []))
        unpack_results.set_metadata(r.get('metadata', {}))
        return unpack_results


def check_condition(condition, message):
    """semantic check function to see if condition is True.
    Raises an UnpackParserException with message if not.
    """
    if not condition:
        raise UnpackParserException(message)
