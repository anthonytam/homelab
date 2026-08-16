{ pkgs, ... }:

{
	home.packages = with pkgs; [
        firefox-devedition
        bitwarden-desktop
        vscode
        discord
    ];
}