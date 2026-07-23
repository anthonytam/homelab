{ ... }:

{
	users.users.atam = {
		isNormalUser = true;
		description = "Anthony Tam";
		extraGroups = [
			"networkmanager"
			"wheel"
            "docker"
		];
        shell = pkgs.zsh
	};
}