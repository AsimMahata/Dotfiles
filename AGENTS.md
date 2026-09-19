# Agent Guidelines & Rules

## Maintenance of `setup.md`

Whenever you make any changes to the system or dotfiles:
1. **Document Every Installation:**
   - Whenever any new package, tool, font, daemon, utility, or dependency is installed (via `pacman`, `yay`, `pip`, cargo, etc.), add the exact installation commands, enabled services, and necessary launch/verification steps to [`setup.md`](file:///home/asim/setup/Dotfiles/setup.md).
2. **Document Configuration Changes:**
   - Whenever you modify existing configs, add new dotfiles, adjust themes, keybindings, or system behaviors, record what changed and any associated setup notes in [`setup.md`](file:///home/asim/setup/Dotfiles/setup.md).
3. **Keep `setup.md` Up to Date:**
   - `setup.md` must remain an accurate, self-contained, reproducible log of the entire system setup from post-installation onwards.

## No Trial-and-Error Fixes Without Permission

- **Definite Fixes Only:** Only apply fixes directly if the exact root cause and verified solution are known with certainty.
- **Ask Before Speculative Changes:** If a solution requires trial-and-error, experimental workarounds, or uncertain troubleshooting, you must explain the situation and ask for user permission before executing commands or modifying files, to avoid breaking working system components.
