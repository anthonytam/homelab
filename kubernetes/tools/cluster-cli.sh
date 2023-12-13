#!/bin/bash

# ssh-multi
# D.Kovalov
# Based on http://linuxpixies.blogspot.jp/2011/06/tmux-copy-mode-and-how-to-control.html
# Modified by johnko https://gist.github.com/johnko/a8481db6a83ec5ea2f37

# a script to ssh multiple servers over multiple tmux panes
starttmux() {
    count=0
    HOSTS="controlplane01.local.tam.land worker01.local.tam.land worker02.local.tam.land worker03.local.tam.land worker04.local.tam.land worker05.local.tam.land"

    for i in ${HOSTS} ; do
        count=$(( count + 1 ))
        if [ ${count} -eq 1 ]; then
            if tmux ls >/dev/null 2>/dev/null ; then
                tmux new-window "ssh ${i}"
            else
                tmux new-session -d "ssh ${i}"
            fi
        else
            tmux split-window -h  "ssh ${i}"
            tmux select-layout tiled >/dev/null
        fi
    done

    tmux select-pane -t 0
    tmux set-window-option synchronize-panes on >/dev/null

}

starttmux $*

tmux attach
