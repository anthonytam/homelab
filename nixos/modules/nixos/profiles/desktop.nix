{ config, pkgs, ... }:

{
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

	services.printing.enable = true;

	services.pulseaudio.enable = false;
	security.rtkit.enable = true;
	services.pipewire = {
		enable = true;
		alsa.enable = true;
		alsa.support32Bit = true;
		pulse.enable = true;
	};
}