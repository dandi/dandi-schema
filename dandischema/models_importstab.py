from .models_linkml import *  # noqa: F401,F403
from .models_orig import (  # noqa: F401
    DANDI_INSTANCE_URL_PATTERN,
    DANDI_NSKEY,
    get_schema_version,
)

# TODO: temporary imports of consts etc which might need to be 'redone'
# so we do not duplicate them

# Deprecated aliases mirroring the ones `models_orig.py` keeps for backward
# compatibility, `PublishedDandiset` and `PublishedAsset` having been consolidated
# into `Dandiset` and `Asset` respectively. `metadata.SCHEMA_MAP` still names them,
# so `publish_model_schemata` needs them to resolve. Temporary: remove these after the
# follow-up to dandi/dandi-schema#419 that drops the aliases from `models_orig.py`.
PublishedDandiset = Dandiset  # noqa: F405
PublishedAsset = Asset  # noqa: F405


# TODO: do the extra tune ups like linking extra validations etc,
# potentially copied from models_orig.py
