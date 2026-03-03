#!/bin/fish

# echo "\$DIR = $DIR"
set -g Run_program_where_the_symlink_is false
# Set this to true to use the directory where the symlink is located (Unix / POSIX style).
# Set this to false to resolve the symlink fully and use the target directory i.e. where the Program is (Windows shortcut and symlink style).
# Another name for the variable that I used initially: ALLOW_CWD_TO_BE_THE_DIRECTORY_WHERE_THE_SYMLINK_POINTING_TO_THIS_EXECUTABLE_IS, then CWD_FOLLOWS_SYMLINK_LOCATION...

if test "$Run_program_where_the_symlink_is" = "true"
	# Unix / POSIX logic: use the directory where the symlink is located
	set DIR (dirname (status -f))
	# f: https://fishshell.com/docs/current/cmds/set.html
	# I tried this line in fish and if the script is symlinked somewhere else on the drive, it resolves to the parent folder of the symlink (i.e. where the symlink is), not the folder of the target file of the symlink.
else
	# Resolve the symlink fully and use the target directory
	set DIR (dirname (readlink -f (status -f)))
end

# echo "\$DIR = $DIR"
cd "$DIR"
# echo "Current dir: $DIR" -> Echos a simple dot, not good.
echo "Current dir:"
pwd --logical
pwd --physical
#	-L or --logical
#
#	    Output the logical working directory, without resolving symlinks (default behavior).
#	-P or --physical
#
#	    Output the physical working directory, with symlinks resolved.


export PYTHONPATH="/home/xy/workspace/Safeeyes fixálása/safeeyes-3.3.1/"
python3 -m safeeyes $argv


# if test -f "./Program.py"
	# "./Program.py" $argv
	# echo "./Program.py ended"
# else if test -f "./main.py"
	# "./main.py" $argv
	# echo "./main.py ended"
# else
	# echo "～Nothing to run here."
	# echo "～Paused the terminal for readability."
	# read x
# end
# read x;
