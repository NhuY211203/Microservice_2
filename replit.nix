{pkgs}: {
  deps = [
    pkgs.docker
    pkgs.docker-compose
    pkgs.postgresql
    pkgs.openssl
  ];
}
