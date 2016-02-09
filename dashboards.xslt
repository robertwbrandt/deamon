<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="ascii"/>
<xsl:template match="/">
  <style type="text/css">
  <xsl:text>
    body,div,table,thead,tbody,tfoot,tr,th,td,p { text-align: right; color:black; font-family:"Liberation Sans"; font-size:x-small }
    th { text-align: center; padding: 0px 10px 0px 10px; }
    td { text-align: left; padding: 0px 10px 0px 10px; white-space: nowrap; }
    tr.details:hover { background: #BBBFFF }
    .error { text-align: center; color:red; font-weight: bold; }
    .good { text-align: center; color:green; font-weight: bold; }
  </xsl:text>
  </style> 
  <h2 align="center">OPW Server Report</h2>
  <xsl:apply-templates select="servers/authservers"/>  
  <xsl:apply-templates select="servers/msgservers"/>  
  <xsl:apply-templates select="servers/ndsservers"/>
</xsl:template>

<xsl:template name="cell">
  <xsl:param name="exitvalue"/>
  <td>
  <xsl:choose>
    <xsl:when test="string-length($exitvalue/@returncode) &gt; 0">
      <xsl:choose>
        <xsl:when test="$exitvalue/@returncode = 0"><xsl:attribute name="class">good</xsl:attribute>Good</xsl:when>
        <xsl:otherwise><xsl:attribute name="class">error</xsl:attribute>Error</xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>&#160;</xsl:otherwise>
  </xsl:choose>
  <xsl:text>
  </xsl:text><xsl:comment>Name: <xsl:value-of select="$exitvalue/@name"/></xsl:comment>  
  <xsl:text>
  </xsl:text><xsl:comment>Return Code: <xsl:value-of select="$exitvalue/@returncode"/></xsl:comment>
  <xsl:text>
  </xsl:text><xsl:comment>Command Str: <xsl:value-of select="$exitvalue/@cmdStr"/></xsl:comment>  
  <xsl:text>
  </xsl:text><xsl:comment>Output: <xsl:value-of select="$exitvalue/output"/></xsl:comment>  
  <xsl:text>
  </xsl:text><xsl:comment>Error: <xsl:value-of select="$exitvalue/error"/></xsl:comment>  
  </td>  
</xsl:template>


<xsl:template match="authservers">
  <table border="1" align="center">
    <caption><h2>Authentication Servers</h2></caption>
    <tr>
      <th align="center" height="32">Server Name</th>
      <th align="center">Network Time</th>
      <th align="center">eDirectory</th>
      <th align="center">Radius</th>
      <th align="center">Linux User<br/>Management</th>
      <th align="center">DHCP</th>
      <th align="center">iManager</th>      
      <th align="center">Disk Usage</th>
    </tr>
    <xsl:for-each select="/servers/authservers/deamons">
      <xsl:sort select="translate(@host, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')" order="ascending" />
      <tr>
        <td><xsl:value-of select="@host"/><xsl:comment>Date: <xsl:value-of select="@date"/></xsl:comment></td>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='ntp']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='nds']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='radius']"/></xsl:call-template>        
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='lum']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='dhcp']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='imanager']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='du']"/></xsl:call-template>
      </tr>
    </xsl:for-each>        
  </table>
</xsl:template>

<xsl:template match="msgservers">
  <table border="1" align="center">
    <caption><h2>Messaging Servers</h2></caption>
    <tr>
      <th align="center" height="32">Server Name</th>
      <th align="center">Network Time</th>      
      <th align="center">SMTP (MTA)</th>
      <th align="center">Mail Server (MDA)</th>      
      <th align="center">Web Access</th>
      <th align="center">IMAP Server</th>      
      <th align="center">CalDav Server</th>
      <th align="center">ActiveSync</th>
      <th align="center">Instant Messaging</th>
      <th align="center">Disk Usage</th>
    </tr>
    <xsl:for-each select="/servers/msgservers/deamons">
      <xsl:sort select="translate(@host, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')" order="ascending" />
      <tr>
        <td><xsl:value-of select="@host"/></td>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='ntp']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='mta']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='mda']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='web']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='imap']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='caldav']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='mobile']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='im']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='du']"/></xsl:call-template>
      </tr>
    </xsl:for-each>
  </table>
</xsl:template>

<xsl:template match="ndsservers">
  <table border="1" align="center">
	  <caption><h2>Remote and Print Servers</h2></caption>
    <tr>
      <th align="center" height="32">Server Name</th>
      <th align="center">Network Time</th>
      <th align="center">eDirectory</th>      
      <th align="center">Linux User<br/>Management</th>
      <th align="center">Novell Storage</th>      
      <th align="center">Samba Shares</th>
      <th align="center">Novell iPrint</th>
      <th align="center">DHCP</th>
      <th align="center">McAfee Antivirus</th>      
      <th align="center">Disk Usage</th>
    </tr>
    <xsl:for-each select="/servers/ndsservers/deamons">
      <xsl:sort select="translate(@host, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')" order="ascending" />
      <tr>
        <td><xsl:value-of select="@host"/></td>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='ntp']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='nds']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='lum']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='nss']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='samba']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='iprint']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='dhcp']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='mcafee']"/></xsl:call-template>
        <xsl:call-template name="cell"><xsl:with-param name="exitvalue" select="deamon[@name='du']"/></xsl:call-template>
      </tr>
    </xsl:for-each>        
  </table>
</xsl:template>
</xsl:stylesheet>

