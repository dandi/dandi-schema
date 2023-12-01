from __future__ import annotations

from functools import total_ordering
import hashlib
import re
from typing import Dict, List, Optional, Tuple

import pydantic

"""Passed to the json() method of pydantic models for serialization."""
ENCODING_KWARGS = {"separators": (",", ":")}
ZARR_CHECKSUM_PATTERN = "([0-9a-f]{32})-([0-9]+)--([0-9]+)"


def generate_directory_digest(md5: str, file_count: int, size: int) -> str:
    """Generate a directory digest from its constituent parts"""
    return f"{md5}-{file_count}--{size}"


def parse_directory_digest(digest: str) -> tuple[str, int, int]:
    """Parse a directory digest into its constituent parts"""
    match = re.match(ZARR_CHECKSUM_PATTERN, digest)
    if match is None:
        raise ValueError(f"Cannot parse directory digest {digest}")
    return match.group(1), int(match.group(2)), int(match.group(3))


@total_ordering
class ZarrChecksum(pydantic.BaseModel):
    """
    A checksum for a single file/directory in a zarr file.

    Every file and directory in a zarr archive has a name, digest, and size.
    """

    digest: str
    name: str
    size: int

    # To make ZarrChecksums sortable
    def __lt__(self, other: ZarrChecksum) -> bool:
        return self.name < other.name


class ZarrChecksums(pydantic.BaseModel):
    """
    A set of file and directory checksums.

    This is the data hashed to calculate the checksum of a directory.
    """

    directories: List[ZarrChecksum] = pydantic.Field(default_factory=list)
    files: List[ZarrChecksum] = pydantic.Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.files == [] and self.directories == []

    def _index(self, checksums: List[ZarrChecksum], checksum: ZarrChecksum) -> int:
        # O(n) performance, consider using the bisect module or an ordered dict for optimization
        for i in range(0, len(checksums)):
            if checksums[i].name == checksum.name:
                return i
        raise ValueError("Not found")

    def add_file_checksums(self, checksums: List[ZarrChecksum]) -> None:
        for new_checksum in checksums:
            try:
                self.files[self._index(self.files, new_checksum)] = new_checksum
            except ValueError:
                self.files.append(new_checksum)
        self.files = sorted(self.files)

    def add_directory_checksums(self, checksums: List[ZarrChecksum]) -> None:
        """Add a list of directory checksums to the listing."""
        for new_checksum in checksums:
            try:
                self.directories[
                    self._index(self.directories, new_checksum)
                ] = new_checksum
            except ValueError:
                self.directories.append(new_checksum)
        self.directories = sorted(self.directories)

    def remove_checksums(self, names: List[str]) -> None:
        """Remove a list of names from the listing."""
        self.files = sorted(
            filter(lambda checksum: checksum.name not in names, self.files)
        )
        self.directories = sorted(
            filter(lambda checksum: checksum.name not in names, self.directories)
        )


class ZarrChecksumListing(pydantic.BaseModel):
    """
    A listing of checksums for all sub-files/directories in a zarr directory.

    This is the data serialized in the checksum file.
    """

    checksums: ZarrChecksums
    digest: str
    size: int


class ZarrJSONChecksumSerializer:
    def aggregate_digest(self, checksums: ZarrChecksums) -> str:
        """Generate an aggregated digest for a list of ZarrChecksums."""
        # Use the most compact separators possible
        # content = json.dumps([asdict(zarr_md5) for zarr_md5 in checksums], separators=(',', ':'))0
        content = checksums.model_dump_json()
        h = hashlib.md5()
        h.update(content.encode("utf-8"))
        md5 = h.hexdigest()
        file_count = sum(
            parse_directory_digest(checksum.digest)[1]
            for checksum in checksums.directories
        ) + len(checksums.files)
        size = sum(file.size for file in checksums.files) + sum(
            directory.size for directory in checksums.directories
        )
        return generate_directory_digest(md5, file_count, size)

    def serialize(self, zarr_checksum_listing: ZarrChecksumListing) -> str:
        """Serialize a ZarrChecksumListing into a string."""
        # return json.dumps(asdict(zarr_checksum_listing))
        return zarr_checksum_listing.model_dump_json()

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
                files=sorted(files) if files is not None else [],
                directories=sorted(directories) if directories is not None else [],
            )
        digest = self.aggregate_digest(checksums)
        return ZarrChecksumListing(
            checksums=checksums,
            digest=digest,
            size=parse_directory_digest(digest)[2],
        )


# We do not store a checksum file for empty directories since an empty directory doesn't exist in
# S3. However, an empty zarr file still needs to have a checksum, even if it has no checksum file.
# For convenience, we define this constant as the "null" checksum.
EMPTY_CHECKSUM = ZarrJSONChecksumSerializer().generate_listing(ZarrChecksums()).digest


def get_checksum(
    files: Dict[str, Tuple[str, int]], directories: Dict[str, Tuple[str, int]]
) -> str:
    """Calculate the checksum of a directory."""
    if not files and not directories:
        raise ValueError("Cannot compute a Zarr checksum for an empty directory")
    checksum_listing = ZarrJSONChecksumSerializer().generate_listing(
        files=[
            ZarrChecksum(digest=digest, name=name, size=size)
            for name, (digest, size) in files.items()
        ],
        directories=[
            ZarrChecksum(digest=digest, name=name, size=size)
            for name, (digest, size) in directories.items()
        ],
    )
    return checksum_listing.digest
