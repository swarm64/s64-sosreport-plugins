# Swarm64 sosreport plugins

## Summary

This is a collection of plugins for _sosreport_ mainly target Swarm64 DA.

## Usage

1. Clone sosreport from https://github.com/sosreport/sos, for instance:

    # Assumes you are in s64-sosreport-plugins
    cd ../
    git clone https://github.com/sosreport/sos

2. For all plugins you want to load, you will have to create symlinks
   accordingly. For instance to make use of `postgresql_alt.py` do:

    cd sos/sos/report/plugins
    ln -s ../../../../s64-sosreport-plugins/plugins/postgresql_alt.py .

    # Check, that plugin loads by listing all
    ./bin/sos report --conf sos.conf -l

3. Run sosreport with the plugins enabled. For instance to run only with the
   `postgresql_alt` plugin execute:

    # Inside sos directory
    ./bin/sos report --conf sos.conf -o postgresql_alt
