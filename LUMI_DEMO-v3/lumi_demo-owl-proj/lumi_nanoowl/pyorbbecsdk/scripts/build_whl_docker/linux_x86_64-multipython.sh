# Run docker container and build the wheel inside it
docker run --rm -v $(pwd):/workspace pyorbbecsdk-env.linux_x86_64-multipython bash ./scripts/build_whl/build_linux_whl_docker.sh