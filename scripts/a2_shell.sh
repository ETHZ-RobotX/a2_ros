#!/bin/bash
# Sourced by .bashrc on shell startup. Lives on the workspace volume so
# changes take effect immediately without rebuilding the image.

# a2 CLI wrapper — intercepts 'source' so it affects this shell;
# all other subcommands are forwarded to the binary in PATH.
a2() {
    if [[ "${1:-}" == "source" ]]; then
        source /a2_ros/scripts/setup.sh
    else
        /usr/local/bin/a2 "$@"
    fi
}

# Bash completion for the a2 CLI. Keep the command list in sync with the case
# statement in scripts/a2.
_a2_complete() {
    local cur prev cmd ws
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    cmd="${COMP_WORDS[1]:-}"
    ws="${WORKSPACE_DIR:-/a2_ros}"

    local commands="source build clean env log sim walk stop unlock stand sit \
keyboard nav explore dlio detect topics nodes bag plotjuggler foxglove router verify ps down help"

    # Value after --scene: available scene files.
    if [[ "$prev" == "--scene" ]]; then
        local scenes
        scenes=$(cd "$ws/src/core/a2_description/mjcf" 2>/dev/null && ls scene*.xml 2>/dev/null)
        COMPREPLY=($(compgen -W "$scenes" -- "$cur"))
        return
    fi

    # First token: top-level command.
    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    # Subsequent tokens depend on the command.
    case "$cmd" in
        bag)
            if [[ $COMP_CWORD -eq 2 ]]; then
                COMPREPLY=($(compgen -W "record play" -- "$cur"))
            elif [[ "${COMP_WORDS[2]}" == "play" ]]; then
                COMPREPLY=($(compgen -W "--clock --pause" -- "$cur"))
                COMPREPLY+=($(compgen -f -- "$cur"))
            fi
            ;;
        build)
            local pkgs
            pkgs=$(find "$ws/src" -name package.xml -printf '%h\n' 2>/dev/null | xargs -r -n1 basename)
            COMPREPLY=($(compgen -W "$pkgs" -- "$cur"))
            ;;
        sim)
            COMPREPLY=($(compgen -W "--rviz --dlio --scene" -- "$cur"))
            ;;
        nav|explore|dlio)
            COMPREPLY=($(compgen -W "--rviz" -- "$cur"))
            ;;
        clean)
            COMPREPLY=($(compgen -W "--yes" -- "$cur"))
            ;;
        down)
            COMPREPLY=($(compgen -W "sim nav explore dlio detect foxglove plotjuggler" -- "$cur"))
            ;;
    esac
}
complete -F _a2_complete a2
