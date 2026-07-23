{
  description = "NixOS and Home Manager configurations";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      nixpkgs,
      home-manager,
      ...
    }:

    let
      mkHost =
        {
          hostname,
          system ? "x86_64-linux",
          users ? [ ],
        }:

        nixpkgs.lib.nixosSystem {
          inherit system;

          specialArgs = {
            inherit inputs hostname;
          };

          modules =
            [
              ./hosts/${hostname}

              home-manager.nixosModules.home-manager

              {
                networking.hostName = hostname;

                home-manager.useGlobalPkgs = true;
                home-manager.useUserPackages = true;

                home-manager.extraSpecialArgs = {
                  inherit inputs hostname;
                };
              }
            ]
            ++ map (user: ./users/${user}/nixos.nix) users
            ++ map
              (user: {
                home-manager.users.${user} =
                  import ./users/${user}/home.nix;
              })
              users;
        };
    in
    {
      nixosConfigurations = {
        TDC-NixOS = mkHost {
          hostname = "TDC-NixOS";
          system = "x86_64-linux";
          users = [ "atam" ];
        };
      };
    };
}