# Swarm64 sosreport plugins

## Summary

This is a collection of plugins for _sosreport_ mainly targeting Swarm64 DA.

## Usage

1. Clone sosreport from https://github.com/sosreport/sos, for instance:

    ```
    # Assumes you are in s64-sosreport-plugins
    cd ../
    git clone https://github.com/sosreport/sos
    ```

2. For all plugins you want to load, you will have to create symlinks
   accordingly. For instance to make use of `postgresql_alt.py` do:

    ```
    cd sos/sos/report/plugins
    ln -s ../../../../s64-sosreport-plugins/plugins/postgresql_alt.py .
    ```

    You can check plugins availability by listing them:
    ```
    ./bin/sos report --conf sos.conf -l
    ```

3. Run sosreport with the plugins enabled. For instance to run only with the
   `postgresql_alt` plugin execute. Also, add the `-k` switch to provide
   options for the plugin:

    ```
    # Inside sos directory
    ./bin/sos report --conf sos.conf -o postgresql_alt \
        -k postgresql_alt.dsn=postgresql://postgres@localhost/postgres \
        -k postgresql_alt.container_id=00c4e99
    ```
