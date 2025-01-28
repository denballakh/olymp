{
  description = "Webserver for a table of math olympiads";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    olymp.url = "github:denballakh/olymp";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, olymp, flake-utils, ... }: flake-utils.lib.mkDefault {
    packages.x86_64-linux = with nixpkgs.legacyPackages.x86_64-linux; rec {
      pythonWebserver = pkgs.buildPythonPackage rec {
        pname = "python-webserver";

        src = olymp;

        nativeBuildInputs = [ pkgs.python312 pkgs.python312.pip ];

        shellHook = ''
          echo hello
        '';

      };
    };

    defaultPackage.x86_64-linux = self.packages.x86_64-linux.pythonWebserver;

    defaultApp = with nixpkgs.legacyPackages.x86_64-linux; {
      nativeBuildInputs = [ pkgs.python312 ];

      shellHook = ''
        exec ${pkgs.python312}/bin/python3.12 ${self.packages.x86_64-linux.pythonWebserver}/main.py
      '';
    };
  };
}