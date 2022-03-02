from __future__ import annotations

import pytest

from dandischema.digests.zarr import (
    ZarrChecksum,
    ZarrChecksumListing,
    ZarrChecksums,
    ZarrJSONChecksumSerializer,
    get_checksum,
)


def test_zarr_checksum_sort_order():
    # The a < b in the path should take precedence over z > y in the md5
    a = ZarrChecksum(name="a", md5="z", size=1)
    b = ZarrChecksum(name="b", md5="y", size=1)
    assert sorted([b, a]) == [a, b]


# ZarrChecksums tests


def test_zarr_checkums_is_empty():
    assert ZarrChecksums(directories=[], files=[]).is_empty
    assert not ZarrChecksums(
        directories=[ZarrChecksum(md5="md5", name="name", size=1)], files=[]
    ).is_empty
    assert not ZarrChecksums(
        directories=[], files=[ZarrChecksum(md5="md5", name="name", size=1)]
    ).is_empty


a = ZarrChecksum(name="a", md5="a", size=1)
b = ZarrChecksum(name="b", md5="b", size=1)
c = ZarrChecksum(name="c", md5="c", size=1)


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
def test_zarr_checkums_add_file_checksums(initial, new_checksums, expected):
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
def test_zarr_checkums_add_directory_checksums(initial, new_checksums, expected):
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
        ([a], [], ["a"], [], []),
        ([], [a], ["a"], [], []),
        ([a], [b], ["a"], [], [b]),
        ([a], [b], ["b"], [a], []),
        ([a, b, c], [], ["b"], [a, c], []),
        ([], [a, b, c], ["b"], [], [a, c]),
    ],
)
def test_zarr_checkums_remove_checksums(
    initial_files,
    initial_directories,
    removed_checksums,
    expected_files,
    expected_directories,
):
    checksums = ZarrChecksums(files=initial_files, directories=initial_directories)
    checksums.remove_checksums(removed_checksums)
    assert checksums.files == expected_files
    assert checksums.directories == expected_directories


# ZarrJSONChecksumSerializer tests


@pytest.mark.parametrize(
    "file_checksums,directory_checksums,checksum",
    [
        ([], [], "481a2f77ab786a0f45aafd5db0971caa"),
        (
            [ZarrChecksum(name="bar", md5="a", size=1)],
            [],
            "677dddd9af150be166c461acdef1b025",
        ),
        (
            [],
            [ZarrChecksum(name="bar", md5="a", size=1)],
            "aa776d184c64cbd6a5956ab0af012830",
        ),
        (
            [
                ZarrChecksum(name="bar", md5="a", size=1),
                ZarrChecksum(name="baz", md5="b", size=1),
            ],
            [],
            "c8a9b1dd53bb43ec6e5d379c29a1f1dd",
        ),
        (
            [],
            [
                ZarrChecksum(name="bar", md5="a", size=1),
                ZarrChecksum(name="baz", md5="b", size=1),
            ],
            "f45aa3833a2129628a38e421f74ff792",
        ),
        (
            [ZarrChecksum(name="baz", md5="a", size=1)],
            [ZarrChecksum(name="bar", md5="b", size=1)],
            "bc0a0e85a0205eb3cb5f163f173774e5",
        ),
    ],
)
def test_zarr_checksum_serializer_aggregate_checksum(
    file_checksums, directory_checksums, checksum
):
    serializer = ZarrJSONChecksumSerializer()
    assert (
        serializer.aggregate_checksum(
            ZarrChecksums(files=file_checksums, directories=directory_checksums)
        )
        == checksum
    )


def test_zarr_checksum_serializer_generate_listing():
    serializer = ZarrJSONChecksumSerializer()
    checksums = ZarrChecksums(
        files=[ZarrChecksum(name="bar", md5="a", size=1)],
        directories=[ZarrChecksum(name="baz", md5="b", size=2)],
    )
    assert serializer.generate_listing(checksums) == ZarrChecksumListing(
        checksums=checksums,
        md5="c20479b1afe558a919eac450028a706e",
        size=3,
    )


def test_zarr_serialize():
    serializer = ZarrJSONChecksumSerializer()
    assert (
        serializer.serialize(
            ZarrChecksumListing(
                checksums=ZarrChecksums(
                    files=[ZarrChecksum(name="bar", md5="a", size=1)],
                    directories=[ZarrChecksum(name="foo", md5="b", size=2)],
                ),
                md5="c",
                size=3,
            )
        )
        == '{"checksums":{"directories":[{"md5":"b","name":"foo","size":2}],"files":[{"md5":"a","name":"bar","size":1}]},"md5":"c","size":3}'  # noqa: E501
    )


def test_zarr_deserialize():
    serializer = ZarrJSONChecksumSerializer()
    assert serializer.deserialize(
        '{"checksums":{"directories":[{"md5":"b","name":"foo","size":2}],"files":[{"md5":"a","name":"bar","size":1}]},"md5":"c","size":3}'  # noqa: E501
    ) == ZarrChecksumListing(
        checksums=ZarrChecksums(
            files=[ZarrChecksum(name="bar", md5="a", size=1)],
            directories=[ZarrChecksum(name="foo", md5="b", size=2)],
        ),
        md5="c",
        size=3,
    )


@pytest.mark.parametrize(
    "files,directories,checksum",
    [
        (
            {"bar": ("a", 1)},
            {},
            "677dddd9af150be166c461acdef1b025",
        ),
        (
            {},
            {"bar": ("a", 1)},
            "aa776d184c64cbd6a5956ab0af012830",
        ),
        (
            {"bar": ("a", 1), "baz": ("b", 2)},
            {},
            "66c03ae00824e6be1283cc370969f6ea",
        ),
        (
            {},
            {"bar": ("a", 1), "baz": ("b", 2)},
            "6969470da4b829f0a8b665ac78350abd",
        ),
        (
            {},
            {"baz": ("b", 1), "bar": ("a", 2)},
            "25f351bbdcfb33f7706f7ef1e80cb010",
        ),
        (
            {"baz": ("a", 1)},
            {"bar": ("b", 2)},
            "a9540738019a48e6392c942217f7526d",
        ),
    ],
)
def test_zarr_get_checksum(files, directories, checksum):
    assert get_checksum(files=files, directories=directories) == checksum


def test_zarr_get_checksum_empty():
    with pytest.raises(ValueError):
        get_checksum(files={}, directories={})
