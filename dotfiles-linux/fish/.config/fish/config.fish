if status is-interactive
    # Disable welcome greeting
    set -g fish_greeting

    # Initialize Starship prompt with Matugen theme
    if type -q starship
        starship init fish | source
    end
end

# Added by Antigravity CLI installer
set -gx PATH "/home/asim/.local/bin" $PATH
