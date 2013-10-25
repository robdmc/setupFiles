#---  SEE THE FOLLOWING REFERENCE FOR HOW TO CHANGE BASH PROMPT
#http://news.softpedia.com/news/How-to-Customize-the-Shell-Prompt-40033.shtml

#--- disable shell meanings of ctrl-s and ctrl-q
stty stop '' >& /dev/null
stty start '' >& /dev/null

#--- make sure autolist is set
set autolist

#--- get the uname type for this machine and define mac type
unameType=$(uname)
macType="Darwin"

#--- add pwd and home bin area to path
export PATH=$HOME/bin/:./:$PATH
export PATH=$PATH:$HOME/local/dataProductivityToolkit

#--- example code for testing if this is a mac or not
#if [ "$unameType" == "$macType" ]; then 
#   echo this is a mac
#   echo yes it is
#else 
#   echo this is not a mac
#fi
#echo $unameType
#echo $macType

#--- make sure the umask is set properly
# umask 027 (writable only by owner, readable/executable only by group)
# umask 002 (read-write by owner and group, read/execute by world)
# umask 007 (read-write by owner and group, no access to others)
umask 002

#--- set up terminal working preferences
shopt -s histappend
shopt -s extglob
export EDITOR=vim
export HISTFILE="$HOME/.bash_history"
export HISTFILESIZE=200000
export HISTSIZE=200000
export HISTIGNORE="clear:ls:pwd:history:hig"
export HISTTIMEFORMAT='%F %T '
set -o vi
set -o history

export PROMPT_COMMAND="history -a; history -c; history -r;"

#--- set the appropriate prompt for the system you're on
if [ "$unameType" == "$macType" ]; then 
  PS1='<mac \W]\$ '
  alias ls=' ls --color=tty' #gls installed from macports coreutils
else
  PS1='<\h \W]\$ '
  alias ls='ls --color=tty'
fi

alias higa="history | grep "
alias hig="history | grep $(date +%F)  | grep "
alias less='less -R'
alias dirs='dirs -v'

#--- define mac specific stuff
if [ "$unameType" == "$macType" ]; then 
  alias ipyw='ipython notebook --pylab'
  alias ipywi='ipython notebook --pylab=inline'
  export PATH=/opt/local/libexec/gnubin/:$PATH
  export PATH=.:/opt/local/bin:/opt/local/sbin:$PATH
  export PATH=$HOME/bin:$HOME/usr/bin:$PATH
  export PATH=$HOME/usr/python/bin:$PATH
  export PATH=$HOME/usr/node/bin:$PATH

  #--- export the goroot directory
  export GOROOT=/usr/local/go

#--- define linux specific stuff
else
  doNothing=""
fi

#--- clear out .bashrc commands from history
history -c
#--- if history file doesn't exist, create it
[ -f $HOME/.bash_history ] || history -w

#--- reload history file into buffer
history -r

