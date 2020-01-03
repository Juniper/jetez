:
# RCSid:
#	$Id: ask.sh 493955 2012-01-31 04:15:37Z ib-builder $
#
#	@(#) Copyright (c) 1994 Simon J. Gerraty
#
#	This file is provided in the hope that it will
#	be of use.  There is absolutely NO WARRANTY.
#	Permission to copy, redistribute or otherwise
#	use this file is hereby granted provided that 
#	the above copyright notice and this notice are
#	left intact. 
#      
#	Please send copies of changes and bug-fixes to:
#	sjg@crufty.net
#

case `echo -n .` in -n*) N=; C="\c";; *) N="-n"; C=;; esac

_TTY=${_TTY:-`test -t 0 && tty`}; export _TTY

_ask() {
	if test "$_TTY"; then
		echo $N "${2:-$1?} "$C > $_TTY
		read $1 < $_TTY
	fi
}

_ask_noecho() {
	if test "$_TTY"; then
		stty -echo < $_TTY
		echo $N "${2:-$1?} "$C > $_TTY
		read $1 < $_TTY
		echo > $_TTY
		stty echo < $_TTY
	fi
}

# it would be nice to use local var etc, but not all shells support it.
ask() {
	case "$1" in
	-echo)	_askfunc=_ask_noecho; shift;;
	*)	_askfunc=_ask;;
	esac
	$_askfunc _a "$2${3:+ [}$3${3:+]}:"
	eval "$1='${_a:-$3}'"
}

# This form is suitable for foo=`asks prompt`
asks() {
	case "$1" in
	-echo)	_askfunc=_ask_noecho; shift;;
	*)	_askfunc=_ask;;
	esac
	$_askfunc __a "$@"
	echo $__a
}

no_help() {
	echo "Sorry, no help available for $1"
}

askv() {
	case "$1" in
	-echo)	_askfunc=_ask_noecho; shift;;
	*)	_askfunc=_ask;;
	esac
	while :
	do
		test "$_TTY" || break
		eval "$_askfunc _a \"$2${3:+ [}$3${3:+]}:\""
		
		case "$_a" in
		\?)	eval \${help_$1:-${help_func:-no_help}} $1
			continue
			;;
		esac
		eval \${validate_$1:-${validate_func:-:}} $1 "${_a:-$3}" && break
	done
	eval "$1='${_a:-$3}'"
}

case $0 in
*asks*)	asks "$@";;
*askv*)	askv "$@"; eval echo $1=\$$1;;
*ask*)	ask "$@"; eval echo $1=\$$1;;
esac

       
