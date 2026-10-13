#!/bin/bash
# Bash completion for pyker

_pyker_completion() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="start stop restart delete list logs info enable disable startup unstartup resurrect uninstall"
    
    # Get current processes for name completion
    local processes=""
    if command -v pyker &> /dev/null && [[ -f ~/.pyker/processes.json ]]; then
        # Extract process names from JSON file
        processes=$(python3 -c "
import json
try:
    with open('$HOME/.pyker/processes.json', 'r') as f:
        data = json.load(f)
        print(' '.join(data.keys()))
except:
    pass
" 2>/dev/null)
    fi

    case $cword in
        1)
            # Complete main commands
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
        2)
            case $prev in
                start)
                    # Complete with process name (new) and show files
                    COMPREPLY=($(compgen -f -- "$cur"))
                    ;;
                stop|restart|delete|logs|info|enable|disable)
                    # Complete with existing process names
                    COMPREPLY=($(compgen -W "$processes" -- "$cur"))
                    ;;
                list|uninstall|startup|unstartup|resurrect)
                    # No further completion
                    ;;
            esac
            ;;
        3)
            case ${words[1]} in
                start)
                    # Complete script file path for start command
                    COMPREPLY=($(compgen -f -X "!*.py" -- "$cur"))
                    ;;
                logs)
                    # Complete with log options
                    COMPREPLY=($(compgen -W "-f --follow -n --lines" -- "$cur"))
                    ;;
            esac
            ;;
        *)
            case ${words[1]} in
                start)
                    # Complete with start options based on current word
                    case "$cur" in
                        --venv=*)
                            # Complete directory paths for venv
                            local venv_path="${cur#--venv=}"
                            COMPREPLY=($(compgen -d -- "$venv_path"))
                            ;;
                        *)
                            COMPREPLY=($(compgen -W "--auto-restart --on-boot --venv=" -- "$cur"))
                            ;;
                    esac
                    ;;
                logs)
                    if [[ ${words[3]} == "-n" || ${words[3]} == "--lines" ]]; then
                        # Complete with numbers for line count
                        COMPREPLY=($(compgen -W "10 20 50 100 200 500" -- "$cur"))
                    else
                        # Complete with log options
                        COMPREPLY=($(compgen -W "-f --follow -n --lines" -- "$cur"))
                    fi
                    ;;
            esac
            ;;
    esac
}

# Register the completion function
complete -F _pyker_completion pyker 