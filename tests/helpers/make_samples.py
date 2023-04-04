from hashlib import sha256
from io import BytesIO
from pathlib import Path
from shutil import copyfile
from sys import exit
from typing import Optional
import zstandard as zstd
from blk import DictSection
import blk.binary
import vromfs.vromfs
import vromfs.bin

here = Path(__file__).absolute().parent


class SamplesBuilder:
    def __init__(self, samples_dir: Path) -> None:
        self.samples_dir = samples_dir
        self.inv_names: Optional[blk.binary.InvNames] = None
        self.no_dict_compressor: Optional[zstd.ZstdCompressor] = None
        self.dict_name: str = ...

        with open(samples_dir / 'section_txt.blk') as istream:
            list_section = blk.text.compose(istream)
            self.section = DictSection.of(list_section)

    def build_slim_zst_dict(self) -> None:
        if self.inv_names is None:
            self.inv_names = blk.binary.InvNames.of(self.section, include_strings=True)

        partial_slim_stream = BytesIO()
        blk.binary.serialize_partial_slim(self.section, self.inv_names, partial_slim_stream)
        ss = [partial_slim_stream.getvalue()]
        dict_ = zstd.train_dictionary(2**8, ss*7)
        dict_digest = sha256(dict_.as_bytes()).digest()
        self.dict_name = f'{dict_digest.hex()}.dict'
        (self.samples_dir / self.dict_name).write_bytes(dict_.as_bytes())
        dict_compressor = zstd.ZstdCompressor(dict_data=dict_)

        if self.no_dict_compressor is None:
            self.no_dict_compressor = zstd.ZstdCompressor()

        with open(self.samples_dir / 'nm', 'wb') as ostream:
            blk.binary.serialize_names(self.inv_names, dict_digest, self.no_dict_compressor, ostream)

        with open(self.samples_dir / 'section_slim_zst_dict.blk', 'wb') as ostream:
            blk.binary.serialize_slim_zst_dict(self.section, self.inv_names, dict_compressor, ostream)

    def build_dir(self) -> None:
        dir_ = self.samples_dir / 'directory'
        dir_.mkdir(exist_ok=True)
        config_dir = dir_ / 'config'
        config_dir.mkdir(exist_ok=True)
        Path(dir_ / 'version').write_text('1.2.3.4\n')
        copyfile(self.samples_dir / 'section_slim_zst_dict.blk', config_dir / 'section_slim_zst_dict.blk')
        copyfile(self.samples_dir / self.dict_name, dir_ / self.dict_name)
        copyfile(self.samples_dir / 'nm', dir_ / 'nm')

    def build_unchecked_vromfs(self) -> None:
        with open(self.samples_dir / 'unchecked.vromfs', 'wb') as ostream:
            vromfs.vromfs.VromfsFile.pack_into(self.samples_dir / 'directory', ostream, extended=False, checked=False)

    def build_checked_vromfs(self) -> None:
        with open(self.samples_dir / 'checked.vromfs', 'wb') as ostream:
            vromfs.vromfs.VromfsFile.pack_into(self.samples_dir / 'directory', ostream, extended=True, checked=True)

    def build_checked_vromfs_simple_uncompressed_checked_bin(self) -> None:
        vromfs_stream = BytesIO((self.samples_dir / 'checked.vromfs').read_bytes())
        with open(self.samples_dir / 'checked_simple_uncompressed_checked.vromfs.bin', 'wb') as ostream:
            vromfs.bin.BinFile.pack_into(vromfs_stream, ostream, platform=vromfs.bin.PlatformType.PC,
                                         version=None, compressed=False, checked=True,
                                         size=len(vromfs_stream.getvalue()))

    def build_unchecked_vromfs_extended_compressed_checked_bin(self) -> None:
        vromfs_stream = BytesIO((self.samples_dir / 'unchecked.vromfs').read_bytes())
        with open(self.samples_dir / 'unchecked_extended_compressed_checked.vromfs.bin', 'wb') as ostream:
            vromfs.bin.BinFile.pack_into(vromfs_stream, ostream, platform=vromfs.bin.PlatformType.PC,
                                         version=(1, 2, 3, 4), compressed=True, checked=True,
                                         size=len(vromfs_stream.getvalue()))


def main() -> int:
    samples_dir = here.parent / 'samples'
    builder = SamplesBuilder(samples_dir)
    builder.build_slim_zst_dict()
    builder.build_dir()
    builder.build_unchecked_vromfs()
    builder.build_checked_vromfs()
    builder.build_checked_vromfs_simple_uncompressed_checked_bin()
    builder.build_unchecked_vromfs_extended_compressed_checked_bin()

    return 0


if __name__ == '__main__':
    exit(main())
