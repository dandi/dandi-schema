from __future__ import annotations

import hashlib
from typing import List, Optional

import pydantic


"""Passed to the json() method of pydantic models for serialization."""
ENCODING_KWARGS = {"separators": (",", ":")}


class ZarrChecksum(pydantic.BaseModel):
    """
    A checksum for a single file/directory in a zarr file.

    Every file and directory in a zarr archive has a path and a MD5 hash.
    """

    md5: str
    path: str

    # To make ZarrChecksums sortable
    def __lt__(self, other: ZarrChecksum):
        return self.path < other.path


class ZarrChecksums(pydantic.BaseModel):
    """
    A set of file and directory checksums.

    This is the data hashed to calculate the checksum of a directory.
    """

    directories: List[ZarrChecksum] = pydantic.Field(default_factory=list)
    files: List[ZarrChecksum] = pydantic.Field(default_factory=list)

    @property
    def is_empty(self):
        return self.files == [] and self.directories == []

    def _index(self, checksums: List[ZarrChecksum], checksum: ZarrChecksum):
        # O(n) performance, consider an ordered dict for optimization
        for i in range(0, len(checksums)):
            if checksums[i].path == checksum.path:
                return i
        raise ValueError("Not found")

    def add_file_checksums(self, checksums: List[ZarrChecksum]):
        for new_checksum in checksums:
            try:
                self.files[self._index(self.files, new_checksum)] = new_checksum
            except ValueError:
                self.files.append(new_checksum)
        self.files = sorted(self.files)

    def add_directory_checksums(self, checksums: List[ZarrChecksum]):
        """Add a list of directory checksums to the listing."""
        for new_checksum in checksums:
            try:
                self.directories[
                    self._index(self.directories, new_checksum)
                ] = new_checksum
            except ValueError:
                self.directories.append(new_checksum)
        self.directories = sorted(self.directories)

    def remove_checksums(self, paths: List[str]):
        """Remove a list of paths from the listing."""
        self.files = sorted(
            filter(lambda checksum: checksum.path not in paths, self.files)
        )
        self.directories = sorted(
            filter(lambda checksum: checksum.path not in paths, self.directories)
        )


class ZarrChecksumListing(pydantic.BaseModel):
    """
    A listing of checksums for all sub-files/directories in a zarr directory.

    This is the data serialized in the checksum file.
    """

    checksums: ZarrChecksums
    md5: str


class ZarrJSONChecksumSerializer:
    def aggregate_checksum(self, checksums: ZarrChecksums) -> str:
        """Generate an aggregated checksum for a list of ZarrChecksums."""
        # Use the most compact separators possible
        # content = json.dumps([asdict(zarr_md5) for zarr_md5 in checksums], separators=(',', ':'))0
        content = checksums.json(**ENCODING_KWARGS)
        h = hashlib.md5()
        h.update(content.encode("utf-8"))
        return h.hexdigest()

    def serialize(self, zarr_checksum_listing: ZarrChecksumListing) -> str:
        """Serialize a ZarrChecksumListing into a string."""
        # return json.dumps(asdict(zarr_checksum_listing))
        return zarr_checksum_listing.json(**ENCODING_KWARGS)

    def deserialize(self, json_str: str) -> ZarrChecksumListing:
        """Deserialize a string into a ZarrChecksumListing."""
        # listing = ZarrChecksumListing(**json.loads(json_str))
        # listing.checksums = [ZarrChecksum(**checksum) for checksum in listing.checksums]
        # return listing
        return ZarrChecksumListing.parse_raw(json_str)

    def generate_listing(
        self,
        checksums: Optional[ZarrChecksums] = None,
        files: Optional[List[ZarrChecksum]] = None,
        directories: Optional[List[ZarrChecksum]] = None,
    ) -> ZarrChecksumListing:
        """
        Generate a new ZarrChecksumListing from the given checksums.

        This method wraps aggregate_checksum and should not be overridden.
        """
        if checksums is None:
            checksums = ZarrChecksums(
                files=files if files is not None else [],
                directories=directories if directories is not None else [],
            )
        return ZarrChecksumListing(
            checksums=checksums,
            md5=self.aggregate_checksum(checksums),
        )


# We do not store a checksum file for empty directories since an empty directory doesn't exist in
# S3. However, an empty zarr file still needs to have a checksum, even if it has no checksum file.
# For convenience, we define this constant as the "null" checksum.
EMPTY_CHECKSUM = ZarrJSONChecksumSerializer().generate_listing(ZarrChecksums()).md5
