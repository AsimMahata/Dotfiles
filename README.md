# My Dotfiles

# Tools I use on Windows to make it look cool

```
1. Window Manager: GlazeWM
2. Status Bar: Zebar
3. Alt Snap (window resizing)
4. Chocolatey (package manager)
5. Flow Launcher
6. CLI tools
   - fastfetch
   - cava
   - nvim
   - starship
   - PowerShell

```

# To add all the Dotfiles Configs in Linux

- Download Stow
`sudo pacman -S stow`
- Go to the Folder `dotfiles-linux`
- type the command
`stow -t ~ */` -- for all configs at onces
- for single config use
`stow -t ~ <NAME>`

### [NOTE]

- make sure no files exists on the .config folder for specific folder before using stow
- its Reccomended to make a backup of your old configs
