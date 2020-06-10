# Swarm64 sosreport plugins

## Summary

This is a collection of plugins for _sosreport_ mainly target Swarm64 DA.

## Usage

1. Clone sosreport from https://github.com/sosreport/sos
2. Create a symlink for all plugins you want to `sos/report/plugins`, for instance:

    cd sos/sos/report/plugins
    ln -s ../../../s64-sosreport-plugins/plugins/postgresql_alt.py .

3. Run sosreport with the plugins enabled

