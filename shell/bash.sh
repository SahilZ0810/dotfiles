# bash-only settings. Sourced from shell/init.sh for interactive shells.

HISTSIZE=50000
HISTFILESIZE=50000
HISTCONTROL=ignoreboth:erasedups

shopt -s histappend   # append rather than clobber on exit
shopt -s checkwinsize # keep LINES/COLUMNS correct after a resize
