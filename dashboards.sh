#!/bin/bash
#
#     Script to Monitor Servers
#     Bob Brandt <projects@brandt.ie>
#  

_version=1.1
_output_dir=/opt/opw/dashboard
_output_xml=$_output_dir/dashboard.xml
_output_html=$_output_dir/dashboard.html
_output_xslt=$_output_dir/server-dashboard.xslt
_ssh_options="-o ConnectionAttempts=1 -o ConnectTimeout=5"
_ftp_server="web-node01"
_ftp_user="intranet"
_ftp_pass="qodmfh9l"
_email_smtp="smtp.opw.ie"
_email_from="server-watch@opw.ie"
_email_to="storagealerts@opw.ie"
#_email_to="bob.brandt@opw.ie"
_title="OPW Server Report for $( date '+%d %b %Y %H:%M' )"

  NORMAL=$( echo -en "${ESC}[m\017" )
BOLD_RED="${ESC}[1;31m"

function getServerInfo() {
    local _server="$1"
    local _type="$2"
    local _status=0

    logger -st "server-dashboard" "Processing server $_server"
    tmp=$( ssh -i "/root/.ssh/bssh_id_rsa" $_ssh_options -x -l root "$_server" "TERM=$TERM dashboard -x" )
    if [ -n "$tmp" ]; then
        echo "$tmp" > "$_output_dir/tmp-${_type}-${_server}.xml"
        return 0
    fi
    logger -st "server-dashboard" "Error while processing server $_server"
    echo '<?xml version="1.0" encoding="UTF-8"?>' > "$_output_dir/tmp-${_type}-${_server}.xml"
    echo "<deamons host=\"$_server\"/>" >> "$_output_dir/tmp-${_type}-${_server}.xml"
    return 1
}

function getallServerInfo() {
    logger -st "server-dashboard" "Server processing began at $( date '+%d %b %Y %H:%M:%S' )"
    # NDS Servers
    getServerInfo "athenry" "nds"
    getServerInfo "athlone" "nds"
    getServerInfo "ballina" "nds"
    getServerInfo "blaskets" "nds"
    getServerInfo "botanics" "nds"
    getServerInfo "castlebar" "nds"
    getServerInfo "claremorris" "nds"
    getServerInfo "collinsbrks" "nds"
    getServerInfo "cork" "nds"
    getServerInfo "dromahair" "nds"
    getServerInfo "dubcastle" "nds"
    getServerInfo "dublin-iprint" "nds"
    getServerInfo "farmleigh" "nds"
    getServerInfo "furniture" "nds"
    getServerInfo "galway" "nds"
    getServerInfo "headford" "nds"
    getServerInfo "kilkenny" "nds"
    getServerInfo "killarneydo" "nds"
    getServerInfo "killarneynm" "nds"
    getServerInfo "kilmainham" "nds"
    getServerInfo "letterkenny" "nds"
    getServerInfo "mallow" "nds"
    getServerInfo "mungret" "nds"
    getServerInfo "phoenixpark" "nds"
    getServerInfo "sligodo" "nds"
    getServerInfo "trim" "nds"
    getServerInfo "trimhq-iprint" "nds"
    getServerInfo "waterford" "nds"

    #getServerInfo "dublinnotes" "msg"
    getServerInfo "im-sso" "msg"
    #getServerInfo "trimnotes" "msg"
    getServerInfo "zarafa-core" "msg"
    getServerInfo "zarafa-activesync" "msg"
    getServerInfo "zarafa-caldav" "msg"
    getServerInfo "zarafa-imap" "msg"
    getServerInfo "zarafa-web" "msg"

    #getServerInfo "radius1" "auth"
    getServerInfo "nds2" "auth"
    getServerInfo "nds3" "auth"
    getServerInfo "mail-ldap" "auth"
    getServerInfo "imanager" "auth"

    logger -st "server-dashboard" "Server processing finished at $( date '+%d %b %Y %H:%M:%S' )"
    return 0
}

function combineXMLFile() {
    echo -e '<?xml version="1.0" encoding="UTF-8"?>' > "$_output_xml"
    echo -e '<servers>' >> "$_output_xml"
    echo -e '<authservers>' >> "$_output_xml"
    cat $_output_dir/tmp-auth-*.xml | grep -v '<?xml ' >> "$_output_xml"
    echo -e '</authservers>' >> "$_output_xml"
    echo -e '<msgservers>' >> "$_output_xml"
    cat $_output_dir/tmp-msg-*.xml | grep -v '<?xml ' >> "$_output_xml"
    echo -e '</msgservers>' >> "$_output_xml"
    echo -e '<ndsservers>' >> "$_output_xml"
    cat $_output_dir/tmp-nds-*.xml | grep -v '<?xml ' >> "$_output_xml"
    echo -e '</ndsservers>' >> "$_output_xml"
    echo -e '</servers>' >> "$_output_xml" 
    
    return 0
}

function publishServerInfo() {
    local _status=0
    combineXMLFile
    _status=$?

    # Create HTML File
    echo -e "<html>" > "$_output_html"
    echo -e "\t<head>" >> "$_output_html"
    echo -e "\t\t<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\"/>" >> "$_output_html"
    echo -e "\t\t<title>$_title</title>" >> "$_output_html"
    echo -e "\t</head>" >> "$_output_html"
    echo -e "\t<body>" >> "$_output_html"
    xsltproc "$_output_xslt" "$_output_xml" >> "$_output_html"
    _status=$(( $_status | $? ))
    echo -e "\t</body>" >> "$_output_html"
    echo -e "</html>\n\n" >> "$_output_html"
    sed -i "s|OPW Server Report|$_title|" "$_output_html"

    # FTP the html page to the 
    if [ "$_status" == "0" ]; then 
        tmp=$( ftp -inv "$_ftp_server" <<END_SCRIPT
user $_ftp_user $_ftp_pass
cd /dashboard
put $_output_html server-dashboard.html
bye
END_SCRIPT )
            if echo -e "$tmp" | grep -i "226 transfer complete" > /dev/null 2>&1
            then
                logger -st "server-dashboard" "Server Dashboard Report published to the Intranet."
            fi
            rm "$_output_xml"
            rm "$_output_html"
    fi
}

function emailServerInfo() {
    local _status=0
    combineXMLFile
    _status=$?

    # Create HTML File
    # echo -e "<html>" > "$_output_html"
    # echo -e "\t<head>" >> "$_output_html"
    echo -e "\t\t<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\"/>" >> "$_output_html"
    echo -e "\t\t<title>$_title</title>" >> "$_output_html"
    echo -e "\t</head>" >> "$_output_html"
    echo -e "\t<body>" >> "$_output_html"
    xsltproc "$_output_xslt" "$_output_xml" >> "$_output_html"
    _status=$(( $_status | $? ))
    echo -e "\t</body>" >> "$_output_html"
    echo -e "</html>\n\n" >> "$_output_html"
    sed -i "s|OPW Server Report|$_title|" "$_output_html"

    if [[ $_status == 0 ]] && /opt/brandt/smtpSend.py --from "$_email_from" --to "$_email_to" --subject "$_title" --server "$_email_smtp" --html "$_output_html"
    then
            logger -st "server-dashboard" "Server Dashboard Report sent to $_email_to via email."
            rm "$_output_xml"
            rm "$_output_html"
    fi
}


function usage() {
    local _exitcode=${1-0}
    local _output=2
    [ "$_exitcode" == "0" ] && _output=1
    [ "$2" == "" ] || echo -e "$2"
    ( echo -e "Usage: $0 [options]"
      echo -e "Options:"
      echo -e " -s, --server   get server information"
      echo -e " -p, --publish  publish server information to the web"
      echo -e " -e, --email    email server information."
      echo -e " -h, --help     display this help and exit"
      echo -e " -v, --version  output version information and exit" ) >&$_output
    exit $_exitcode
}

function version() {
  echo -e "$( basename $0 ) $_version"
  echo -e "Copyright (C) 2011 Free Software Foundation, Inc."
  echo -e "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>."
  echo -e "This is free software: you are free to change and redistribute it."
  echo -e "There is NO WARRANTY, to the extent permitted by law.\n"
  echo -e "Written by Bob Brandt <projects@brandt.ie>."
  exit 0
}

# Execute getopt
if ! _args=$( getopt -o spevh -l "server,publish,email,help,version" -n "$0" -- "$@" 2>/dev/null ); then
    _err=$( getopt -o spevh -l "server,publish,email,help,version" -n "$0" -- "$@" 2>&1 >/dev/null )
    usage 1 "${BOLD_RED}$_err${NORMAL}"
fi

#Bad arguments
#[ $? -ne 0 ] && usage 1 "$0: No arguments supplied!\n"

_server=
_publish=
_email=
eval set -- "$_args";
while /bin/true ; do
    case "$1" in
        -s | --server )    _server=1 ;;
        -p | --publish )   _publish=1 ;;
        -e | --email )     _email=1 ;;
        -h | --help )      usage 0 ;;
        -v | --version )   version $_version ;;
        -- )               shift ; break ;;
        * )                usage 1 "${BOLD_RED}$0: Invalid argument!${NORMAL}" ;;
    esac
    shift
done

_count=$( ps -ef | grep "$( basename $0 )" | grep -v "grep" | grep -v "$$" | sed "/^$/d" | wc -l )
if [[ $_count > 0 ]]; then
    logger -st "server-dashboard" "Another $( basename $0 ) is already running."
    exit 1
fi

if [ -z "$_server" ] && [ -z "$_publish" ] && [ -z "$_email" ]; then
    _server=1
    _publish=1
    _email=1 
fi

[ -n "$_server" ]  && getallServerInfo
[ -n "$_publish" ] && publishServerInfo
[ -n "$_email" ]   && emailServerInfo

exit $?

