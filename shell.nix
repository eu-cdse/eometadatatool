{ }:

let
  # Update packages with `nixpkgs-update` command
  pkgs =
    import
      (fetchTarball "https://github.com/NixOS/nixpkgs/archive/3fcbdcfc707e0aa42c541b7743e05820472bdaec.tar.gz")
      { };

  wrapPrefix = if (!pkgs.stdenv.isDarwin) then "LD_LIBRARY_PATH" else "DYLD_LIBRARY_PATH";
  pythonLibs = with pkgs; [
    gdal.out
    zlib.out
    stdenv.cc.cc.lib
  ];
  python' =
    with pkgs;
    (symlinkJoin {
      name = "python";
      paths = [ python313 ];
      buildInputs = [ makeWrapper ];
      postBuild = ''
        wrapProgram "$out/bin/python3.13" --prefix ${wrapPrefix} : "${lib.makeLibraryPath pythonLibs}"
      '';
    });

  packages' = with pkgs; [
    python'
    uv
    ruff
    gdal
    geos
    coreutils
    gnugrep
    jq

    (writeShellScriptBin "run-tests" ''
      set +e
      COVERAGE_CORE=sysmon python -m coverage run -m pytest \
        --verbose \
        --no-header
      result=$?
      set -e
      if [ "$1" = "term" ]; then
        python -m coverage report --skip-covered
      else
        python -m coverage xml --quiet
      fi
      python -m coverage erase
      exit $result
    '')
    (writeShellScriptBin "watch-tests" "exec watchexec -w app -w tests --exts py run-tests")
    (writeShellScriptBin "metadata_extract" ".venv/bin/python -c \"from eometadatatool.metadata_extract import main; main()\" \"$@\"")
    (writeShellScriptBin "nixpkgs-update" ''
      set -e
      hash=$(
        ${pkgs.curlMinimal}/bin/curl --silent --location \
        https://prometheus.nixos.org/api/v1/query \
        -d "query=channel_revision{channel=\"nixpkgs-unstable\"}" | \
        egrep -o "[0-9a-f]{40}")
      sed -i -E "s|/nixpkgs/archive/[0-9a-f]{40}\.tar\.gz|/nixpkgs/archive/$hash.tar.gz|" shell.nix
      echo "Nixpkgs updated to $hash"
    '')
  ];

  shell' = ''
    export TZ=UTC
    export NIX_ENFORCE_NO_NATIVE=0
    export NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
    export SSL_CERT_FILE=$NIX_SSL_CERT_FILE
    export PYTHONNOUSERSITE=1
    export PYTHONPATH=""


    current_python=$(readlink -e .venv/bin/python || echo "")
    current_python=''${current_python%/bin/*}
    [ "$current_python" != "${python'}" ] && rm -rf .venv/

    echo "Installing Python dependencies"
    export CPATH="${pkgs.python313Packages.numpy.out}/lib/python3.13/site-packages/numpy/_core/include:$CPATH"
    export UV_PYTHON="${python'}/bin/python"
    uv sync --frozen

    echo "Activating Python virtual environment"
    source .venv/bin/activate

    # prefer nix implementation for macOS compatibility
    rm -f .venv/bin/metadata_extract

    export AWS_S3_EODATA_BUCKET=eodata
    export AWS_VIRTUAL_HOSTING=false

    if [ -f credentials.json ]; then
      echo "Loading credentials.json file"
      eval "$(jq -r \
        'to_entries[] | "export AWS_\(.key|ascii_upcase|gsub("AWS_";""))=\(.value | @sh)"' \
        credentials.json)"
    else
      echo "Skipped loading credentials.json file (not found)"
    fi

    if [ -f .env ]; then
      echo "Loading .env file"
      set -o allexport
      source .env set
      set +o allexport
    else
      echo "Skipped loading .env file (not found)"
    fi
  '';
in
pkgs.mkShell {
  buildInputs = packages';
  shellHook = shell';
}
