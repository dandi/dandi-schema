def test_get_instance_config() -> None:
    from dandischema.conf import _instance_config, get_instance_config

    obtained_config = get_instance_config()

    assert obtained_config == _instance_config
    assert (
        obtained_config is not _instance_config
    ), "`get_instance_config` should return a copy of the instance config"
