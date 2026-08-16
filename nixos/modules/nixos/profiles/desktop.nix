{ config, pkgs, ... }:

{
	# X & DM/DE
  services.xserver.enable = true;

  services.xserver.xkb = {
    layout = "us";
    variant = "";
  };

  services.displayManager.gdm.enable = true;
  services.desktopManager.gnome.enable = true;

  xdg.portal = {
    enable = true;

    extraPortals = [
      pkgs.xdg-desktop-portal-gtk
      pkgs.xdg-desktop-portal-gnome
    ];

    config = {
      common = {
        default = [ "gnome" ];
      };
    };
  };

	# Printing
  services.printing.enable = true;

	# Audit
  services.pulseaudio.enable = false;
  security.rtkit.enable = true;

  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
  };

	# Package Settings
	# Used by Bitwarden Desktop
	nixpkgs.config.permittedInsecurePackages = [
		"electron-39.8.10"
	];
}