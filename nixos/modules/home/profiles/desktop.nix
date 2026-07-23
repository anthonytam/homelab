{ pkgs, ... }:

{
    nixpkgs.config.permittedInsecurePackages = [
        "electron-39.8.10"
    ];

	home.packages = with pkgs; [
        firefox-devedition
        bitwarden-desktop
        vscode
        discord
    ]
}