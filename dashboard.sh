#!/bin/bash
#
#     Script for a user friendly dashboard showing all necessary deamons and stats
#     Bob Brandt <projects@brandt.ie>
#          
#

#
# exit status 0)  success
# exit status 1)  generic or unspecified error

_version=1.1
_brandt_utils=/opt/brandt/common/brandt.sh
_this_conf=/etc/brandt/dashboard.conf
_this_script=/opt/brandt/deamon/dashboard.sh
_this_rc=/usr/local/bin/dashboard

[ ! -r "$_brandt_utils" ] && echo "Unable to find required file: $_brandt_utils" 1>&2 && exit 6
. "$_brandt_utils"

if [ ! -r "$_this_conf" ]; then
    ( echo -e "#     Configuration file for the Brandt Dashboard script"
      echo -e "#     Bob Brandt <projects@brandt.ie>\n#"
      echo -e "###############################################################################"
      echo -e "# {always|"
      echo -e "#  present|"
      echo -e "#  never|"
      echo -e "#  last},   shortname,      long name,                     control command,                  status"
      echo -e "first,      uptime,         Uptime,                       /opt/brandt/buptime,              /opt/brandt/buptime"
      echo -e "present,    network,        Network,                      /etc/init.d/network,              /opt/brandt/init.d/network -q status"
      echo -e "always,     ntp,            Network Time Protocol,        /etc/init.d/ntp,                  /opt/brandt/init.d/ntp status"
      echo -e "present,    slp,            Service Location Protocol,    /etc/init.d/slpd,                 /opt/brandt/init.d/slp status"
      echo -e "last,       du,             Disk Usage,                   /opt/brandt/diskusage,            /opt/brandt/diskusage -p 84"
      echo -e "###############################################################################" ) > "$_this_conf"
    echo "Unable to find required file: $_this_conf" 1>&2
fi

function isInRunlevel() {
    _command="$1"
    _runlevel=$( /sbin/runlevel ) || usage 1 "${BOLD_RED}Unable to determine Runlevel.${NORMAL}"
    _runlevel=$( echo "$_runlevel" | sed "s|.* ||" )

    _scriptdir=/etc/init.d/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=/etc/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=$( find /etc/ -type d -iname "rc${_runlevel}.d" | head -1 )
    [ -d "$_scriptdir" ] || usage 1 "${BOLD_RED}Unable to find runlevel directory.${NORMAL}"
    for _script in $( find "$_scriptdir" -iname "s*" | sort ); do
        _readlink=$( readlink -f "$_script" )
        [ -x "$_readlink" ] && [ "$_readlink" == "$_command" ] && return 0
    done
    return 1
}

function status() {
    local _runstatus=0
    _ran=""
    IFS_OLD="$IFS"
    IFS=$'\n'

    _runlevel=$( /sbin/runlevel ) || usage 1 "${BOLD_RED}Unable to determine Runlevel.${NORMAL}"
    _runlevel=$( echo "$_runlevel" | sed "s|.* ||" )

    _scriptdir=/etc/init.d/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=/etc/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=$( find /etc/ -type d -iname "rc${_runlevel}.d" | head -1 )
    [ -d "$_scriptdir" ] || usage 1 "${BOLD_RED}Unable to find runlevel directory.${NORMAL}"

    # Display all the "first" deamons in the order they appear in the conf file
    for _line in $( grep "^first," "$_this_conf" ); do
        _shortname=$( trim $( echo "$_line" | cut -d"," -f2 ) )
        _longname=$( trim $( echo "$_line" | cut -d"," -f3 ) )
        if ! echo -e "${_ran}" | grep "${_shortname}" >/dev/null 2>&1 ; then
            _status=$( trim $( echo "$_line" | cut -d"," -f5 ) )
            if [ "${_status}" == "status" ]; then
                _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )
                _run="${_command} status"
            else
                _run="${_status}"
                _command=$( echo "${_status}" | sed "s| .*||" )
            fi
            eval "${_run}"
            _runstatus=$(( $_runstatus | $? ))
            _ran="${_ran}\n${_shortname}"
        fi
    done

    # Display all the present and always deamons in the order they appear in the conf file if they are started
    for _line in $( grep "^\(always\|present\)" "$_this_conf" ); do
        _oktorun=$( trim $( echo "$_line" | cut -d"," -f1 ) )
        _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )

        if [ "$_oktorun" == "always" ] || isInRunlevel "$_command"
        then
            _shortname=$( trim $( echo "$_line" | cut -d"," -f2 ) )
            _longname=$( trim $( echo "$_line" | cut -d"," -f3 ) )
            if ! echo -e "${_ran}" | grep "${_shortname}" >/dev/null 2>&1 ; then
                _status=$( trim $( echo "$_line" | cut -d"," -f5 ) )
                if [ "${_status}" == "status" ]; then
                    _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )
                    _run="${_command} status"
                else
                    _run="${_status}"
                    _command=$( echo "${_status}" | sed "s| .*||" )
                fi
                eval "${_run}"
                _runstatus=$(( $_runstatus | $? ))
                _ran="${_ran}\n${_shortname}"
            fi
        fi
    done

    # Display all the remaining "last" deamons in the order they appear in the conf file
    for _line in $( grep "^last," "$_this_conf" ); do
        _shortname=$( trim $( echo "$_line" | cut -d"," -f2 ) )        
        _longname=$( trim $( echo "$_line" | cut -d"," -f3 ) )
        if ! echo -e "${_ran}" | grep "${_shortname}" >/dev/null 2>&1 ; then
            _status=$( trim $( echo "$_line" | cut -d"," -f5 ) )
            if [ "${_status}" == "status" ]; then
                _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )
                _run="${_command} status"
            else
                _run="${_status}"
                _command=$( echo "${_status}" | sed "s| .*||" )
            fi
            eval "${_run}"
            _runstatus=$(( $_runstatus | $? ))
            _ran="${_ran}\n${_shortname}"
        fi
    done

    IFS="$IFS_OLD"
    return ${_runstatus}
 }

function xmlstatus() {
    local _runstatus=0
    IFS_OLD="$IFS"
    IFS=$'\n'

    _runlevel=$( /sbin/runlevel ) || usage 1 "${BOLD_RED}Unable to determine Runlevel.${NORMAL}"
    _runlevel=$( echo "$_runlevel" | sed "s|.* ||" )

    _scriptdir=/etc/init.d/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=/etc/rc${_runlevel}.d
    [ -d "$_scriptdir" ] || _scriptdir=$( find /etc/ -type d -iname "rc${_runlevel}.d" | head -1 )
    [ -d "$_scriptdir" ] || usage 1 "${BOLD_RED}Unable to find runlevel directory.${NORMAL}"

    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo -n '<server name="'
    echo -n $( hostname | safe4xml )
    echo -n '" time="'
    echo -n $( date -u "+%Y-%m-%dT%H:%M:%SZ" | safe4xml )
    echo -n '">'
    for _runname in $( echo "$1" | tr ',' '\n' ); do
        echo -n "<${_runname}>"
        if _line=$( grep -i "^[^,#]*,[[:space:]]*${_runname}," "$_this_conf" )
        then
            _oktorun=$( trim $( echo "$_line" | cut -d"," -f1 ) )
            _shortname=$( trim $( echo "$_line" | cut -d"," -f2 ) )
            _longname=$( trim $( echo "$_line" | cut -d"," -f3 ) )
            _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )
            _status=$( trim $( echo "$_line" | cut -d"," -f5 ) )
            case "$_oktorun" in
                "always" | "first" | "last" )
                    _oktorun="yes" ;;
                "present" )
                    _oktorun="no"
                    isInRunlevel "$_command" && _oktorun="yes" ;;
            esac
            if [ "$_oktorun" == "yes" ]; then
                if [ "${_status}" == "status" ]; then
                    _command=$( trim $( echo "$_line" | cut -d"," -f4 ) )
                    _run="${_command} status"
                else
                    _run="${_status}"
                    _command=$( echo "${_status}" | sed "s| .*||" )
                fi
                eval "${_run}" > /dev/null 2>&1
                _tmp=$?
                _runstatus=$(( $_runstatus | $_tmp ))            
                echo -n $( echo "$_tmp" | safe4xml )
            fi
        fi
        echo -n "</${_runname}>"
    done
    echo '</server>'
    return ${_runstatus}    
}
 
function usage() {
    local _exitcode=${1-0}
    local _output=2
    [ "$_exitcode" == "0" ] && _output=1
    [ "$2" == "" ] || echo -e "$2"
    ( echo -e "Usage: $0 [options]"
      echo -e "Options:"
      echo -e " -x, --xml      comma separated list of processes"
      echo -e " -h, --help     display this help and exit"
      echo -e " -v, --version  output version information and exit" ) >&$_output
    exit $_exitcode
}

# Execute getopt
if ! _args=$( getopt -o x:vh -l "xml:,help,version" -n "$0" -- "$@" 2>/dev/null ); then
    _err=$( getopt -o x:vh -l "xml:,help,version" -n "$0" -- "$@" 2>&1 >/dev/null )
    usage 1 "${BOLD_RED}$_err${NORMAL}"
fi

#Bad arguments
#[ $? -ne 0 ] && usage 1 "$0: No arguments supplied!\n"

eval set -- "$_args";
_xml=""
while /bin/true ; do
    case "$1" in
        -x | --xml )     _xml="$2" ; shift ;;
        -h | --help )      usage 0 ;;
        -v | --version )   brandt_version $_version ;;
        -- )               shift ; break ;;
        * )                usage 1 "${BOLD_RED}$0: Invalid argument!${NORMAL}" ;;
    esac
    shift
done

if [ "$( lower $1 )" == "setup" ]; then
    ln -sf "$_this_script" "$_this_rc" > /dev/null 2>&1
else
    if [ -z "$_xml" ]; then
        status
    else
        xmlstatus "$_xml"
    fi
fi
exit $?