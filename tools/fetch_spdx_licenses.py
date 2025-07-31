# This script is for constructing the SPDX License ID list from a SPDX License List
#   JSON file available at a specific URL.
#   The `licenses_source_url` is to be modified to point to the desired version of the
#   SPDX License List JSON file.

from datetime import datetime
from importlib.resources import as_file, files

from pydantic import AnyUrl, BaseModel, Field
from requests import get

from dandischema.conf import SpdxLicenseIdList, SpdxLicenseListInfo

licenses_source_url = (
    "https://raw.githubusercontent.com/spdx/license-list-data"
    "/refs/tags/v3.27.0/json/licenses.json"
)


class SpdxLicense(BaseModel):
    """
    Represent a license in the SPDX License List, https://spdx.org/licenses/.

    Notes
    ----
        An object of this class is loaded from the JSON version of the list at
        https://github.com/spdx/license-list-data/blob/main/json/licenses.json
        at a specific version, e.g., "3.27.0"
    """

    license_id: str = Field(validation_alias="licenseId")


class SpdxLicenseList(BaseModel):
    """
    Represents the SPDX License List, https://spdx.org/licenses/.

    Notes
    ----
        The resulting object is a representation of the JSON version of the list at
        https://github.com/spdx/license-list-data/blob/main/json/licenses.json
        at a specific version, e.g., "3.27.0"

    """

    license_list_version: str = Field(validation_alias="licenseListVersion")
    licenses: list[SpdxLicense]
    release_date: datetime = Field(validation_alias="releaseDate")


resp = get(licenses_source_url, timeout=30.0)
resp.raise_for_status()
spdx_license_list = SpdxLicenseList.model_validate_json(resp.text)

spdx_license_id_list = SpdxLicenseIdList(
    source=SpdxLicenseListInfo(
        version=spdx_license_list.license_list_version,
        release_date=spdx_license_list.release_date,
        url=AnyUrl(licenses_source_url),
    ),
    license_ids=[license_.license_id for license_ in spdx_license_list.licenses],
)


license_id_file_path = (
    files("dandischema").joinpath("_resources").joinpath("spdx_license_ids.json")
)

with as_file(license_id_file_path) as license_id_file_path_writable:
    license_id_file_path_writable.write_text(
        spdx_license_id_list.model_dump_json(indent=2)
    )
