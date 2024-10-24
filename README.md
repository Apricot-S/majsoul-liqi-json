# majsoul-liqi-json

## Usage

### Using Docker

#### Build the image

```sh
majsoul-liqi-json$ docker build -t cryolite/majsoul-liqi-json .
```

#### Run the container

```sh
majsoul-liqi-json$ cat PATH/TO/liqi.json | docker run --rm -i cryolite/majsoul-liqi-json > PATH/TO/your-favorite-name.proto
```

### Using uv

```sh
majsoul-liqi-json$ cat PATH/TO/liqi.json | uv run parse.py > PATH/TO/your-favorite-name.proto
```
