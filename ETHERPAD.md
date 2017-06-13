**More information about our use of Etherpad.**

Last updated June 10, 2017

## Why we use Etherpad

Etherpad (actually called Etherpad lite) is a real-time collaborative text editing tool. It can be used stand-alone.  

It is available here: [Etherpad lite](https://github.com/ether/etherpad-lite)

We use it inside the CCI application to handle most of the collaborative work.

## Version

CCI uses the released 1.5.7 version of Etherpad, with heavy modifications, including using Redis as the database instead of MySQL or DirtyDB (which is the default for Etherpad). We also pulled in some big fixes and changes that were made after 1.5.7, as we did extensive testing on that version.

## How to make changes

If you would like to make changes to Etherpad once you have installed it with our patch file, you are of course, welcome to do so.

If you want to submit a change to Etherpad, you can, of course, submit it to that project.

If you want to submit a change to the version of Etherpad that is used with CCI, the process is a bit more complicated, as you need to alter the patch file that we are using.

Here are the steps:

* Re-install CCI with an unchanged version of Etherpad. Make the change you want.

* Download a clean version of 1.5.7 from the Etherpad Github project.

* Run a diff for your changed version versus 1.5.7 to get a new patch file. That command will be something like:

<pre><code>
    diff -crb --new-file PathToOriginal157EtherpadDirectory PathToYourDirectory > etherpad-157-cci.patch
</code></pre>

* Submit that changed patch file in your pull request.




