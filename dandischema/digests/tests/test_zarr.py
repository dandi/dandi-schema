from __future__ import annotations

import pytest

from dandischema.digests.zarr import (
    ZarrChecksum,
    ZarrChecksumListing,
    ZarrChecksums,
    ZarrJSONChecksumSerializer,
    get_checksum,
)


def test_zarr_checksum_sort_order() -> None:
    # The a < b in the path should take precedence over z > y in the checksum
    a = ZarrChecksum(name="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", digest="z", size=1)
    b = ZarrChecksum(name="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", digest="y", size=1)
    assert sorted([b, a]) == [a, b]


# ZarrChecksums tests


def test_zarr_checkums_is_empty() -> None:
    assert ZarrChecksums(directories=[], files=[]).is_empty
    assert not ZarrChecksums(
        directories=[ZarrChecksum(digest="checksum", name="name", size=1)], files=[]
    ).is_empty
    assert not ZarrChecksums(
        directories=[], files=[ZarrChecksum(digest="checksum", name="name", size=1)]
    ).is_empty


a = ZarrChecksum(
    name="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    size=1,
)
b = ZarrChecksum(
    name="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    size=1,
)
c = ZarrChecksum(name="c", digest="c", size=1)


@pytest.mark.parametrize(
    ("initial", "new_checksums", "expected"),
    [
        ([], [], []),
        ([a], [], [a]),
        ([], [a], [a]),
        ([a], [a], [a]),
        ([b], [a], [a, b]),
        ([a, c], [b], [a, b, c]),
        ([b], [c, a], [a, b, c]),
    ],
)
def test_zarr_checkums_add_file_checksums(
    initial: list[ZarrChecksum],
    new_checksums: list[ZarrChecksum],
    expected: list[ZarrChecksum],
) -> None:
    checksums = ZarrChecksums(directories=[], files=initial)
    checksums.add_file_checksums(new_checksums)
    assert checksums.files == expected
    assert checksums.directories == []


@pytest.mark.parametrize(
    ("initial", "new_checksums", "expected"),
    [
        ([], [], []),
        ([a], [], [a]),
        ([], [a], [a]),
        ([a], [a], [a]),
        ([b], [a], [a, b]),
        ([a, c], [b], [a, b, c]),
        ([b], [c, a], [a, b, c]),
    ],
)
def test_zarr_checkums_add_directory_checksums(
    initial: list[ZarrChecksum],
    new_checksums: list[ZarrChecksum],
    expected: list[ZarrChecksum],
) -> None:
    checksums = ZarrChecksums(directories=initial, files=[])
    checksums.add_directory_checksums(new_checksums)
    assert checksums.directories == expected
    assert checksums.files == []


@pytest.mark.parametrize(
    (
        "initial_files",
        "initial_directories",
        "removed_checksums",
        "expected_files",
        "expected_directories",
    ),
    [
        ([], [], [], [], []),
        ([a], [], ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"], [], []),
        ([], [a], ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"], [], []),
        ([a], [b], ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"], [], [b]),
        ([a], [b], ["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"], [a], []),
        ([a, b, c], [], ["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"], [a, c], []),
        ([], [a, b, c], ["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"], [], [a, c]),
    ],
)
def test_zarr_checkums_remove_checksums(
    initial_files: list[ZarrChecksum],
    initial_directories: list[ZarrChecksum],
    removed_checksums: list[str],
    expected_files: list[ZarrChecksum],
    expected_directories: list[ZarrChecksum],
) -> None:
    checksums = ZarrChecksums(files=initial_files, directories=initial_directories)
    checksums.remove_checksums(removed_checksums)
    assert checksums.files == expected_files
    assert checksums.directories == expected_directories


# ZarrJSONChecksumSerializer tests


@pytest.mark.parametrize(
    "file_checksums,directory_checksums,digest",
    [
        ([], [], "481a2f77ab786a0f45aafd5db0971caa-0--0"),
        (
            [
                ZarrChecksum(
                    name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size=1
                )
            ],
            [],
            "f21b9b4bf53d7ce1167bcfae76371e59-1--1",
        ),
        (
            [],
            [
                ZarrChecksum(
                    name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1--1", size=1
                )
            ],
            "ea8b8290b69b96422a3ed1cca0390f21-1--1",
        ),
        (
            [
                ZarrChecksum(
                    name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size=1
                ),
                ZarrChecksum(
                    name="baz", digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", size=1
                ),
            ],
            [],
            "8e50add2b46d3a6389e2d9d0924227fb-2--2",
        ),
        (
            [],
            [
                ZarrChecksum(
                    name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1--1", size=1
                ),
                ZarrChecksum(
                    name="baz", digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--1", size=1
                ),
            ],
            "4c21a113688f925240549b14136d61ff-2--2",
        ),
        (
            [
                ZarrChecksum(
                    name="baz", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size=1
                )
            ],
            [
                ZarrChecksum(
                    name="bar", digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--1", size=1
                )
            ],
            "d5e4eb5dc8efdb54ff089db1eef34119-2--2",
        ),
    ],
)
def test_zarr_checksum_serializer_aggregate_digest(
    file_checksums: list[ZarrChecksum],
    directory_checksums: list[ZarrChecksum],
    digest: str,
) -> None:
    serializer = ZarrJSONChecksumSerializer()
    assert (
        serializer.aggregate_digest(
            ZarrChecksums(files=file_checksums, directories=directory_checksums)
        )
        == digest
    )


def test_zarr_checksum_serializer_generate_listing() -> None:
    serializer = ZarrJSONChecksumSerializer()
    checksums = ZarrChecksums(
        files=[
            ZarrChecksum(name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size=1)
        ],
        directories=[
            ZarrChecksum(
                name="baz", digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2", size=2
            )
        ],
    )
    assert serializer.generate_listing(checksums) == ZarrChecksumListing(
        checksums=checksums,
        digest="baf791d7bac84947c14739b1684ec5ab-2--3",
        size=3,
    )


def test_zarr_serialize() -> None:
    serializer = ZarrJSONChecksumSerializer()
    assert (
        serializer.serialize(
            ZarrChecksumListing(
                checksums=ZarrChecksums(
                    files=[
                        ZarrChecksum(
                            name="bar",
                            digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                            size=1,
                        )
                    ],
                    directories=[
                        ZarrChecksum(
                            name="foo",
                            digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2",
                            size=2,
                        )
                    ],
                ),
                digest="cccccccccccccccccccccccccccccccc-2--3",
                size=3,
            )
        )
        == '{"checksums":{"directories":[{"digest":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2","name":"foo","size":2}],"files":[{"digest":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","name":"bar","size":1}]},"digest":"cccccccccccccccccccccccccccccccc-2--3","size":3}'  # noqa: E501
    )


def test_zarr_deserialize() -> None:
    serializer = ZarrJSONChecksumSerializer()
    assert serializer.deserialize(
        '{"checksums":{"directories":[{"digest":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2","name":"foo","size":2}],"files":[{"digest":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","name":"bar","size":1}]},"digest":"cccccccccccccccccccccccccccccccc-2--3","size":3}'  # noqa: E501
    ) == ZarrChecksumListing(
        checksums=ZarrChecksums(
            files=[
                ZarrChecksum(
                    name="bar", digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size=1
                )
            ],
            directories=[
                ZarrChecksum(
                    name="foo", digest="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2", size=2
                )
            ],
        ),
        digest="cccccccccccccccccccccccccccccccc-2--3",
        size=3,
    )


@pytest.mark.parametrize(
    "files,directories,checksum",
    [
        (
            {"bar": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1)},
            {},
            "f21b9b4bf53d7ce1167bcfae76371e59-1--1",
        ),
        (
            {},
            {"bar": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1--1", 1)},
            "ea8b8290b69b96422a3ed1cca0390f21-1--1",
        ),
        (
            {
                "bar": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1),
                "baz": ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", 2),
            },
            {},
            "4e67de4393d14c1e9c472438f0f1f8b1-2--3",
        ),
        (
            {},
            {
                "bar": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1--1", 1),
                "baz": ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2", 2),
            },
            "859ca1926affe9c7d0424030f26fbd89-2--3",
        ),
        (
            {},
            {
                "baz": ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--1", 1),
                "bar": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-1--2", 2),
            },
            "8f8361a286c9a7c3fbfd464e33989037-2--3",
        ),
        (
            {"baz": ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1)},
            {"bar": ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-1--2", 2)},
            "3cb139f47d3a3580388f41956c15f55e-2--3",
        ),
    ],
)
def test_zarr_get_checksum(
    files: dict[str, tuple[str, int]],
    directories: dict[str, tuple[str, int]],
    checksum: str,
) -> None:
    assert get_checksum(files=files, directories=directories) == checksum


def test_zarr_get_checksum_empty() -> None:
    with pytest.raises(ValueError):
        get_checksum(files={}, directories={})
