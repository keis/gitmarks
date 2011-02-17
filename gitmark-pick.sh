#!/bin/sh

TAG_PATH=${GITMARK_TAGS:-${XDG_DATA_HOME:-$HOME/.local/share}/gitmark/tags}
DMENU_LINES=${DMENU_LINES:-10}

# Unless tags was specifed in args, pick with dmenu
if [ ! $# -eq 0 ]; then
    tags="$@"
else
    tags=$(ls $TAG_PATH | sed '/^all$/d' | dmenu -l $DMENU_LINES)
    if [ ! $? == 0 ]; then
        exit 1
    fi
fi

# display list with url title, echo url
cut -f 1-2 $(for tag in "$tags"; do echo "$TAG_PATH/$tag"; done) | dmenu -l $DMENU_LINES | cut -f 1
