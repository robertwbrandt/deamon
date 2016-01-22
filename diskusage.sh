#!/bin/bash
#
#     Quick script to show Disk Usage (df) with color
#     Bob Brandt <projects@brandt.ie>
#          

#
# exit status 0)  success
# exit status 1)  generic or unspecified error

_version=1.1
_percent=80
_brandt_utils=/opt/brandt/common/brandt.sh
_this_script=/opt/brandt/deamon/diskusage.sh
_this_rc=/usr/local/bin/diskusage

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
. "$_brandt_utils"

function usage() {
    local _exitcode=${1-0}
    local _output=2
    [ "$_exitcode" == "0" ] && _output=1
    [ "$2" == "" ] || echo -e "$2"
    ( echo -e "Usage: $0 [options]"
      echo -e "Options:"
      echo -e " -p, --percent  percentage to display red (Default: $_percent)"
      echo -e " -h, --help     display this help and exit"
      echo -e " -v, --version  output version information and exit" ) >&$_output
    exit $_exitcode
}

# Execute getopt
if ! _args=$( getopt -o p:vh -l "percent:,help,version" -n "$0" -- "$@" 2>/dev/null ); then
    _err=$( getopt -o p:vh -l "percent:,help,version" -n "$0" -- "$@" 2>&1 >/dev/null )
    usage 1 "${BOLD_RED}$_err${NORMAL}"
fi

#Bad arguments
#[ $? -ne 0 ] && usage 1 "$0: No arguments supplied!\n"

brandt_amiroot && ( ln -sf "$_this_script" "$_this_rc" > /dev/null 2>&1 )

eval set -- "$_args";
_quiet=1
while /bin/true ; do
    case "$1" in
        -p | --percent )   _percent=$2 ; shift ;;
        -h | --help )      usage 0 ;;
        -v | --version )   brandt_version $_version ;;
        -- )               shift ; break ;;
        * )                usage 1 "${BOLD_RED}$0: Invalid argument!${NORMAL}" ;;
    esac
    shift
done

_status=0
IFS_OLD="$IFS"
IFS=$'\n'
for line in $( df -ah | tr '\n' '\r' | sed -e "s|\r | |g" -e "s| \+| |g" | tr '\r' '\n' | grep "% " | column -t )
do
    if echo "$line" | grep -vi "use%"  > /dev/null 2>&1
    then
        tmp=$( echo "$line" | awk '{ print $5 ; }' )
        len=${#tmp}-1
        if [[ ${tmp:0:$len} -gt $_percent ]]  > /dev/null 2>&1
        then
            echo -n "${BOLD_RED}" 
            _status=1
        fi
    else
        line=$( echo "$line" | sed "s|Mounted \+on|Mounted on|" )
    fi
    echo "$line${NORMAL}"
done
IFS="$IFS_OLD"
exit $_status
