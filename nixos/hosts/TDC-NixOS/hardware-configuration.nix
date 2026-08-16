{ config, lib, pkgs, modulesPath, ... }:

{
  imports =
    [ (modulesPath + "/installer/scan/not-detected.nix")
    ];

  boot.initrd.availableKernelModules = [ "nvme" "xhci_pci" "ahci" "usb_storage" "usbhid" "sd_mod" ];
  boot.initrd.kernelModules = [ ];
  boot.kernelModules = [ "kvm-amd" "amdgpu" ];
  boot.extraModulePackages = [ ];

  fileSystems."/" =
    { device = "/dev/mapper/luks-a5799262-c6ef-4a2e-8d9e-e4b59c522a03";
      fsType = "ext4";
    };

  boot.initrd.luks.devices."luks-a5799262-c6ef-4a2e-8d9e-e4b59c522a03".device = "/dev/disk/by-uuid/a5799262-c6ef-4a2e-8d9e-e4b59c522a03";

  fileSystems."/boot" =
    { device = "/dev/disk/by-uuid/E363-D5D2";
      fsType = "vfat";
      options = [ "fmask=0077" "dmask=0077" ];
    };

  swapDevices = [ ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;
}
