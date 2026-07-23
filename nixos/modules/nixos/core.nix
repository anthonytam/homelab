{ config, pkgs, ... }:

{
    boot.loader.systemd-boot.enable = true;
    boot.loader.efi.canTouchEfiVariables = true;

    time.timeZone = "America/Toronto";
    i18n.defaultLocale = "en_CA.UTF-8";

    networking.networkmanager.enable = true;

    environment.systemPackages = with pkgs; [
        htop
        git
        wget
        vim
        zsh
        tmux
    ]
}