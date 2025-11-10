# =============================================
# Multi-Python Version Installation Image
# https://www.python.org/ftp/python
# 3.8.20/                                            07-Sep-2024 10:25
# 3.9.23/                                            03-Jun-2025 19:20
# 3.10.18/                                           03-Jun-2025 18:59
# 3.11.13/                                           03-Jun-2025 19:28
# 3.12.11/                                           03-Jun-2025 17:39
# 3.13.5/                                            11-Jun-2025 21:35
# =============================================

# Use the manylinux2014_x86_64 as the base
FROM quay.io/pypa/manylinux2014_x86_64

# Define Python versions to install
# [important]Modify PATH and LD_LIBRARY_PATH when changing python version
ENV PY_VERSIONS="3.8.20 3.9.23 3.10.18 3.11.13 3.12.11 3.13.5"

# Set non-interactive mode to avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Replace default source in the Docker container, Use faster mirror
RUN curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo && \
	curl -o /etc/yum.repos.d/epel.repo http://mirrors.cloud.tencent.com/repo/epel-7.repo && \
	yum clean all && yum makecache && yum -y update

# Build dependencies
RUN yum -y groupinstall "Development Tools" && \
    yum install -y zlib-devel openssl-devel ncurses-devel gdbm-devel libffi-devel sqlite-devel \
                   git wget curl gcc-c++ make && \
    yum clean all

# Upgrade OpenSSL for modern TLS
RUN wget https://www.openssl.org/source/openssl-1.1.1k.tar.gz && \
    tar -xzf openssl-1.1.1k.tar.gz && \
    cd openssl-1.1.1k && \
    ./config --prefix=/usr --openssldir=/usr/local/ssl && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    openssl version && \
    cd .. && rm -rf openssl-1.1.1k*

# Remove old Python if any
RUN rm -rf /usr/bin/python3* /opt/python/*

# Download all Python sources in one step for better layer caching
RUN for py in $PY_VERSIONS; do \
    curl -O https://www.python.org/ftp/python/$py/Python-$py.tgz; \
done

# Build and install all Python versions
RUN for py in $PY_VERSIONS; do \
    tar -xzf Python-$py.tgz && \
    cd Python-$py && \
    ./configure --enable-optimizations --with-ssl --enable-shared --prefix=/opt/python/$py && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-$py*; \
done

# Add all installed Python versions to PATH and LD_LIBRARY_PATH
ENV PATH="/opt/python/3.13.5/bin:\
/opt/python/3.12.11/bin:\
/opt/python/3.11.13/bin:\
/opt/python/3.10.18/bin:\
/opt/python/3.9.23/bin:\
/opt/python/3.8.20/bin:${PATH}"

ENV LD_LIBRARY_PATH="/opt/python/3.13.5/lib:\
/opt/python/3.12.11/lib:\
/opt/python/3.11.13/lib:\
/opt/python/3.10.18/lib:\
/opt/python/3.9.23/lib:\
/opt/python/3.8.20/lib:${LD_LIBRARY_PATH}"

# Create consistent symlinks & install pip tools for all versions
RUN for py in $PY_VERSIONS; do \
    py_major_minor=$(echo $py | cut -d. -f1,2); \
    bin_dir=/opt/python/$py/bin; \
    cd $bin_dir && \
    ln -sf python${py_major_minor} python3 && \
    ln -sf pip${py_major_minor} pip3 && \
    ./pip3 install --upgrade pip && \
    ./pip3 install setuptools wheel cibuildwheel auditwheel pybind11==2.11.0 pybind11-global==2.11.0 && \
    ./pip3 install opencv-python av pygame pynput; \
done

# Define /workspace as the working directory inside the container.
# All subsequent commands will be executed from this directory.
WORKDIR /workspace