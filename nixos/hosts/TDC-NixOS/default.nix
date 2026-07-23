# hosts/desktop/default.nix
{ ... }:

{
    imports = [
        ./hardware-configuration.nix
        ../../modules/nixos/core.nix
        ../../modules/nixos/profiles/desktop.nix
    ];

    home-manager.users.atam.imports = [
        ../../modules/home/home.nix
        ../../modules/home/profiles/desktop.nix
    ];
    
    services.xserver.videoDrivers = [ "amdgpu" ];

    system.stateVersion = "26.05";
}