# see https://github.com/xtdb/xtdb/pkgs/container/xtdb/versions for tags
# `latest`: latest tagged release
# `nightly`: built every night from `main` branch
# `edge`: latest nightly plus urgent fixes

# To delete state: sudo rm -rf /tmp/xtdb-data-dir

# Add -v to persist states
# From https://docs.xtdb.com/intro/installation-via-docker.html

docker rm -f xtdb-2

sudo rm -rf /tmp/xtdb-data-dir

docker run -d -it --name="xtdb-2" --pull=always \
  -p 5432:5432 \
  -p 8080:8080 \
  -p 3000:3000 \
  -v /tmp/xtdb-data-dir:/var/lib/xtdb \
  ghcr.io/xtdb/xtdb:2.0.0-beta6.1

# Using this image for now: https://github.com/xtdb/xtdb/pkgs/container/xtdb/374319005?tag=2.0.0-beta6.1

# 5432: Postgres wire-compatible server (primary API)
# 8080: Monitoring/healthz HTTP endpoints
# 3000: HTTP query/tx API