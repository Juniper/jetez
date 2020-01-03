# JET YAML - Project Description

The JET package content is described in the project description YAML file
described here. The default path is `<source-dir>/jet.yaml` which can be
changed using the argument `-j/--jet`.

The example shows the minimum version of this file.

```yaml
---
basename: "go-rpc"
files:
    - source: go-rpc
      destination: /var/db/scripts/jet/go-rpc
```

The table below describes all fields supported in the project description file.

| Field           | Mandatory | Default                                  | Description |
| --------------- | --------- | ---------------------------------------- | ----------- |
| basename        | YES       |                                          | name without spaces used for package filename and comment |
| comment         | NO        | JET app `basename`                       | description for `show version` |
| arch            | NO        | x86                                      | cpu architecture (x86 or ppc) |
| abi             | NO        | 32                                       | cpu bit (32 or 64) |
| copyright       | NO        | Copyright `year`, Juniper Networks, Inc. | copyright text |
| package_id      | NO        | 31                                       | should not be changed |
| role            | NO        | Provider_Daemon                          | should not be changed |
| schema          | NO        | False                                    | reload schema (mgd restart) |
| config-validate | NO        | False                                    | trigger config validation |
| veriexec-ext    | NO        | False                                    | enables veriexec extension |
| files           | YES       |                                          | list of files in the package (see file table) |

Following all fields supported per file.

| Field       | Mandatory | Default | Description |
| ----------- | --------- | ------- | ----------- |
| source      | YES       |         | relative (from source directory) path to file |
| destination | YES       |         | target path on JunOS (e.g. /var/db/scripts/jet/...) |
| uid         | NO        | 0       | unix user identifier |
| gid         | NO        | 0       | unix group identifier |
| mode        | NO        | 555     | unix file permissions |
| program_id  | NO        | 1       | should not be changed |
| symlink     | NO        | True    | create symlink |


The field `schema` means that mgd needs it. It will cause mgd to be restarted when
the package is added, but unlike `config-validate` will not trigger config
validation. The field `veriexec-ext` means that extensions are needed, without `schema`
this has the same effect as `mountlate`. The fields `schema` and `veriexec-ext` should
be `True` if the package content is required for initial commit (e.g. event-script referenced).
