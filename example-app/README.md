# JetEZ GO Example

### Cross Compile App for JunOS

```
cd src
env GOOS=freebsd GOARCH=386 go build -o ../hello
```

### Build Package

```
$ jetez --source example-app --key certs/<key>.pem --cert certs/<cert>.pem --version 0.1
INFO: load project file example-app/jet.yaml
INFO: create temporary build directory .build
INFO: copy file hello to .build/contents/contents/var/db/scripts/jet/hello
INFO: create manifest file .build/contents/contents/pkg/manifest
INFO: create symlink file .build/contents/contents.symlinks
INFO: sign manifest file .build/contents/contents/pkg/manifest
INFO: create contents.iso
Total translation table size: 0
Total rockridge attributes bytes: 1805
Total directory bytes: 10240
Path table size(bytes): 72
Max brk space used 0
1027 extents written (2 MB)
INFO: create package.xml
INFO: create manifest file .build/manifest
INFO: sign manifest file .build/manifest
INFO: create example-x86-32-0.1.tgz
INFO: package successfully created
```

### Install and Test Package

The used certificate must be configured under system extensions providers
to be able to install the package.

```
system {
    extensions {
        providers {
            <provider-id> {
                license-type <license> deployment-scope <deployment>;
            }
        }
    }
}
```

Install package:
```
> request system software add example-x86-32-0.1.tgz
Verified example-x86-32-0.1 signed by <cert> method RSA2048+SHA1
```

Enable JET application:
```
system {
    extensions {
        extension-service {
            application {
                file hello;
            }
        }
    }
}
```

Test application:
```
> request extension-service start hello
Extension-service application 'hello' started with pid: 12968
Hello GO
```
