# TDSR NVDA Server

This addon aims to provide a convenient method for using TDSR with NVDA.
[TDSR][1] is a console screen reader written by [Tyler Spivey][2]. It provides efficient access to consoles, especially over ssh, where traditionally, screen readers struggle due to a multitude of factors. 

## Rationale:

When using ssh with NVDA, cursor tracking is immediately problemmatic.
NVDA tracks the cursor in a syncronous fassion.
While this has benefits in that it doesn't chance double speaking or other strange behavior, it becomes problematic in terminals because NVDA waits a certain amount of time before giving up on the hope of a cursor move, and simply reporting the same character again.
Assuming the user presses right arrow while focused on "p" in vim,   NVDA waits .03 seconds, and then  gives up on a cursor move; it then  says "p" again instead of "e".
To solve this problem, I invented [console timer][3]. This was a good start, but still requires user configuration, and is still an annoyance.
TDSR has the advantage that it is running on the remote machine, so it doesn't have to wait for cursor moves as long, because there is no network connection to wait on.
There is still a network connection, but all the work is done on the remote end. Characters are simply sent over the encrypted ssh channel. (assuming a port forward over ssh).

Second, NVDA must diff the entire screen, even if only one character has changed, due to the way Accessibility APIs work. NVDA's console support is therefore slow sometimes, and dynamic content changes can be either too verbose, or not verbose enough, or plain wrong.
This is not a problem NVDA can fix easily.
However, TDSR is the shell on the remote machine, (Client), therefore, it doesn't have to do any diffing. It just sees the characters that have changed, and works with them directly.

Thirdly, in the future, TDSR is in a much better possition than NVDA to allow modules or plugins to exist for terminals only. 
While I have done work on console modules for NVDA, it is sort of out of scope, and may or may not be easily dueable in NVDA without serious performance hits to users who never will use a terminal.
I'm about 90% confident that it is possible to do console module support in NVDA as a plugin. However, TDSR is in a better position to do this because of point 1.
It is likely I'll write plugin support for TDSR, and then write a Vi plugin.

When using TDSR, NVDA simply acts as a server, and becomes TDSR's slave. It simply speaks whatever TDSR tells it to speak.
This means that it becomes possible to more efficiently do a hole load of things, as outlined in points 1, 2 and 3.
To finalize, review cursor support in the terminal is still possible, and is more efficient than using TDSR for review since that happens over the connection.
The combination of TDSR disabling automatic live region support and cursor tracking, along with still being able to use the review cursor makes NVDA and TDSR a good combination.
This global plugin should make this easier.

## setup.

It is necessary to launch TDSR with the server running.
It is also necessary to forward the correct port over ssh.
The server is set up to use port 64111. The server runs only on localhost, and the client also runs only on localhost.

### Some remote machine work:

* First, go grab TDSR on the remote machine.
    `git clone https://github.com/tspivey/tdsr.git`
* Now, cd into tdsr.
* After this, get `server_sock.sh` to this remote machine in your tdsr directory.
* You need socat. On ubuntu: `sudo apt-get install socat` I assume yum has it as well.
* Install pyte and other dependencies. I recommend following [the install instructions for tdsr][1].

Now, for the NVDA addon install.

### Get the addon.

Go install the addon. Check the releases page for the addon, or build it yourself. You'd need the addonTemplate build instructions for this.
I assume that if you are technically competent enough to be reading this, you can figure out how to install an NVDA addon, or look at the NVDA users guide if you need to.

### Set up a port forward:

You need to set up a port forward for ssh.
If you are using putty, it can be done by going to ssh in the tree, expanding that and going down to tunnel. Now, add 64111 in the source and 127.0.0.1:64111 in the destination, and select remote, then press add. You'll see `R64111	127.0.0.1:64111` in the list.
If you use ssh unix style, then you can do it with code like this in your host I think.
```
host example.com
    RemoteForward 127.0.0.1:64111 127.0.0.1:64111
```

Your terminal must support the meta key. Once this is done, proceed to the test stage.

### Testing our server.

On the remote, run `./server_sock.sh` from your tdsr directory. If it won't execute, `chmod u+x` it.
Now, if it runs and the server port opens (It'll be sitting waiting for input on stdin), type the following. one line at a time. Then, proceed to the advanced test.

```
sHello, I'm speaking!
lHello, I'll spell this out character by character.
sif [ true ]; then
s'
```
If NVDA talked, you're good to go, try running this next command to make sure it can send the shut up command across. Warning: This will spam NVDA with hello's. After ten seconds it should shut up, if not, kill it.
```
yes sHello | head -n 1000 | ./server_sock.sh; sleep 10; echo 'x' | ./server_sock.sh; sleep 5
```
If you got a bunch of hello's, and then it abruptly shut up, good. 

### Now, run it:

Yay! Let's go! 
CD into your tdsr directory.
```
./tdsr -s server_sock.sh
```
You can still pass a shell to tdsr if you want to just by putting it after the server. For example you could run your shell as /bin/sh.
if it said "tdsr active" it's working.

### Create an alias.

If you want, create an alias like 
`alias tdsr='PATH_TO_TDSR -s PATH_TO_SERVER'`

## Disabling NVDA's console support.

Pressing nvda+f5 will kill console support. Review cursor still works, but bye bye editing commands and dynamic content changes.
Note: There are still bugs here, if you know how to fix them, tell me, otherwise, I'll investigate them sometime.

## Caviots

* If you are doing something with a boat load of text in the bakground like a linux kernel compile, and switch to another window, TDSR will still communicate with NVDA, because focus doesn't matter. You need to turn on quiet mode in TDSR to fix this. This is *bye design*
* Copy in TDSR doesn't work, It only works in tdsr on mac.

[1]: https://github.com/tspivey/tdsr
[2]: https://github.com/tspivey/
[3]: https://github.com/derekriemer/consoletimer
