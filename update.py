#!/usr/bin/env python3

"""
Build Dockerfiles for all supported tags.  This Dockerfile builder is generic
enough to build off of any tag on the buildpacks-deps base image.  However, the
use of the deadsnakes PPA restricts the linux variants to Ubuntu.

Inspired by/taken from the official rust-lang/docker-rust lib:
https://github.com/rust-lang/docker-rust/blob/16fead3e9d5a7e3538ee54ec20c3bfe565e8fb0a/x.py

The file at the link above is not governed by any license.
"""

from collections import namedtuple
from urllib import request
import os

RUST_VERSION = "nightly"
RUSTUP_VERSION = "1.18.3"

Arch = namedtuple("Arch", ["bashbrew", "dpkg", "rust"])

ARCHES = [
    Arch("amd64", "amd64", "x86_64-unknown-linux-gnu"),
    Arch("arm32v7", "armhf", "armv7-unknown-linux-gnueabihf"),
    Arch("arm64v8", "arm64", "aarch64-unknown-linux-gnu"),
    Arch("i386", "i386", "i686-unknown-linux-gnu"),
]

UBUNTU_VARIANTS = [
    "xenial",
]
PYTHON_VERSIONS = [
    "3.6",
    "3.7",
]


def rustup_hash(arch, version=None):
    if version is None:
        version = RUSTUP_VERSION
    url = f"https://static.rust-lang.org/rustup/archive/{version}/{arch}/rustup-init.sha256"  # noqa: E501
    with request.urlopen(url) as f:
        return f.read().decode('utf-8').split()[0]


def read_file(file):
    with open(file, "r") as f:
        return f.read()


def write_file(file, contents):
    dir = os.path.dirname(file)
    if dir and not os.path.exists(dir):
        os.makedirs(dir)
    with open(file, "w") as f:
        f.write(contents)


def generate_dockerfiles():
    arch_case = 'dpkgArch="$(dpkg --print-architecture)"; \\\n'
    arch_case += '    case "${dpkgArch##*-}" in \\\n'
    for arch in ARCHES:
        hash = rustup_hash(arch.rust)
        arch_case += f"        {arch.dpkg}) rustArch='{arch.rust}'; rustupSha256='{hash}' ;; \\\n"  # noqa: E501
    arch_case += '        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \\\n'  # noqa: E501
    arch_case += '    esac'

    template = read_file("Dockerfile.template")

    for variant in UBUNTU_VARIANTS:
        for py_version in PYTHON_VERSIONS:
            rendered = template \
                .replace("%%RUST-VERSION%%", RUST_VERSION) \
                .replace("%%RUSTUP-VERSION%%", RUSTUP_VERSION) \
                .replace("%%VARIANT%%", variant) \
                .replace("%%ARCH-CASE%%", arch_case) \
                .replace("%%PYTHON-VERSION%%", py_version)
            write_file(f"{RUST_VERSION}/{variant}/python{py_version}/Dockerfile", rendered)  # noqa: E501


if __name__ == "__main__":
    generate_dockerfiles()
