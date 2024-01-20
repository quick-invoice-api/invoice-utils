# invoice-utils

## Building

We use [Docker](https://www.docker.com) containers to package the invoicing app.
The Docker image has two target stages:

 * `test` - is used for building and running our automated test suite
 * `runtime` - is used for building and running our app

To build the `test` image, run:

```shell
$ docker build --target test --tag <your-tag-here> .
```

To build the `runtime` image, run:
```shell
$ docker build --target runtime --tag <your-tag-here> .
```

To run the app, you need to build the `runtime` image and then run that via
`docker run`.
To run the app's automated test suite you need to build the `test` image and
run that using `docker run`.
