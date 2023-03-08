
# [PEP 517](https://peps.python.org/pep-0517/#build-backend-interface)
from poetry.core.masonry import api

# TODO: build pygwalker-app with npm

def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    return api.build_wheel(wheel_directory, config_settings, metadata_directory)

def build_sdist(sdist_directory, config_settings=None):
    return api.build_sdist(sdist_directory, config_settings)

def get_requires_for_build_wheel(config_settings=None):
    return api.get_requires_for_build_wheel(config_settings)

def get_requires_for_build_wheel(config_settings):
    return api.get_requires_for_build_wheel(config_settings)

def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    return api.prepare_metadata_for_build_wheel(metadata_directory, config_settings)

def get_requires_for_build_sdist(config_settings=None):
    return api.get_requires_for_build_sdist(config_settings)