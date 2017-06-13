**These are instructions on how to install the application.**

Last updated June 10, 2017

# Contents

* [Installation Overview](#overview)
* [Supported operating systems](#operatingsystems)
* [Users and groups](#users)
* [Installing Redis](#redis)
* [Installing MySQL](#mysql)
* [Installing Apache](#apache)
* [Installing Python](#python)
* [Installing Node](#node)
* [Installing CCI Application Code](#code)
* [Python Application Setup](#pythonapp)
* [Python Application Settings](#pythonsettings) 
* [Python-Apache Configuration](#apacheconfig) 
* [Obtaining and Patching Etherpad](#etherpad)
* [Etherpad Configuration](#etherpadconfig)
* [Setting Up Log Files](#logs)
* [Preparing Databases](#dbpreparation)
* [API and SESSION keys](#keys)
* [How to Run the Application](#running)


# Installation Overview <a id="overview"></a>

Installing this application is a long process, so it is probably valuable to describe the high-level architecture. CCI is really two applications that work together, but use different underlying technologies. This the primary reason that setup and configuration take a while. 

The first is a Python Django application. It needs all the components required to run a Python web application. We are using Apache and WSGI to do this. The second is a Javascript Node application called “Etherpad”. It is an open source project that has been significantly modified to work with CCI. Etherpad is used for the tasks in the sessions. These two applications talk over an API in Etherpad. 

There are two databases behind this. MySQL holds all the CCI application data. Redis is a noSQL data store that stores the real-time changes users are making in the tasks. 

Getting all these components set up properly and securely is not easy, and is why the instructions are lengthy. 

# Supported Operating Systems  <a id="operatingsystems"></a>

These instructions are for Red Hat Enterprise Linux 7. However, you should be able to use any UNIX/Linux operating system that can support the underlying components, and can build open source software.

# Users and Groups  <a id="users"></a>

We don’t want to run all the components of this application as root, so we need to add users and groups.

As root, or via sudo, you need to add three users: cci-user, mysql-user, and redis-user. You also need to add a “cci” group. Having separate users dramatically improves security and reduces configuration problems. Will assume you’re using sudo for these instructions.

#### Create three users:

    sudo /usr/sbin/useradd cci-user
    sudo passwd cci-user
    sudo /usr/sbin/useradd redis-user
    sudo passwd redis-user
    sudo /usr/sbin/useradd mysql-user
    sudo passwd mysql-user


#### Create CCI group, add them

    sudo /usr/sbin/groupadd cci
    sudo usermod -Gcci cci-user
    sudo usermod -Gcci redis-user
    sudo usermod -Gcci mysql-user

#### Create mysql group, add mysql-user

    sudo /usr/sbin/groupadd mysql
    sudo usermod -Gmysql mysql-user

#### Add cci and apache to wheel group

(We are doing this so apache can use the application's files.)

    sudo usermod -a -G wheel cci-user
    sudo usermod -a -G wheel apache

#### Validate users in right groups

Open /etc/groups in a text editor and make sure the correct members are in 'wheel' and 'cci'.

    sudo vi /etc/group

You’ll see lines like:

    cci:x:15:cci-user,redis-user,mysql-user
    wheel:x:12:name1,name2,cci-user,apache

#### Grant sudo ability to wheel group

We wil use the visudo tool, which is just like the vi text editor. Just type the command below to open the text editor. Go to the wheel group line and uncomment it if it’s not already)

    visudo

# Installing Redis  <a id="redis"></a>

Redis is a popular, in-memory noSQL database that CCI uses for revisions in tasks in the sessions. It is not the default database for using one of the underlying components (Etherpad) but its use improves performance. We aren’t doing anything advanced or special with this database.

We recommend building it from source on your platform before use. For Red Hat Enterprise 7, the installation instructions are here for your reference:

http://sharadchhetri.com/2015/07/05/install-redis-3-0-from-source-on-ubuntu-14-04-centos-7-rhel-7/

#### Building Redis from source

Your machine will need to have typical underlying development tools installed. These are things like “gcc” and “make”. On Red Hat 7, this can be done simply by using yum:

    yum group install "Development Tools"

That will take a little while. 

Next we are going to download Redis 3.2.x. Here we are using 3.2.8
(modify all commands and the http link for whatever version you are using)

    curl -O http://download.redis.io/releases/redis-3.2.8.tar.gz
    tar xvfz redis-3.2.8.tar.gz

You should now have a redis-3.2.8 directory. We need to copy that to /usr/local, link it symbolically to /usr/local, delete local copy, and then grant permissions to the redis-user who will run it.

    cd redis-3.2.8
    make distclean all
    (make sure that all ends without error messages)
    sudo cp -r redis-3.2.8 /usr/local
    sudo ln -s /usr/local/redis-3.2.8 /usr/local/redis
    
    sudo chown -R redis-user /usr/local/redis-3.2.8
    sudo chgrp -R cci /usr/local/redis-3.2.8

Go into /usr/local/redis/redis.conf and make sure that the following statement is uncommented, so that we only accept requests from this machine:
bind 127.0.0.1
(It probably was uncommented, as that became the default in 3.2, but it’s crucial for security, so it’s good to check.)

#### Installing Redis Database

The following command must be run using sudo:

    sudo /usr/local/redis/utils/install_server.sh

Follow the installation script and use all the defaults suggested until you get to the executable path. When you get there, use this path:
/usr/local/redis/src/redis-server

You should see an installation message ending with “Installation Successful!”

Test that redis is running:

    /usr/local/redis/src/redis-cli ping

(You should see PONG as the return value)

But we don’t want to ever run Redis as root (a very serious security risk), so let’s shutdown

    /usr/local/redis/src/redis-cli shutdown &

Change to the redis-user account. Then start it again:

    /usr/local/redis/src/redis-server &

Now we need to make it so that it will startup on reboot. Go into /usr/local/redis and type:

    sudo cp utils/redis_init_script /etc/init.d/redis_6379

Then edit that init script and change the directories of EXEC And CLIEXEC to the right paths, which use:
/usr/local/redis/src/

For your own reference:
The redis database dump file will be here:
/var/lib/redis/6379/dump.rdb

The redis configuration file will be at:  
/etc/redis/6379.conf


# Installing MySQL  <a id="mysql"></a>

We need MySQL to hold all the application data for the CCI application. Any 5.x version should be fine. We aren’t doing anything advanced or special with this database.

It doesn’t matter whether you use an official MySQL Community release or the equally-compatible MariaDB open source release. We are going to use MariaDB here. You can install it with yum.

We will install the database and client (this will take a little while)

    sudo yum install MariaDB-server MariaDB-client

We also need to install the development support library, which Python needs:
    
    sudo yum install MariaDB-devel

Now we will start the database

    sudo /etc/init.d/mysql start

Now we need to change the root password to something instead of PASSWORD below:

    '/usr/bin/mysqladmin' -u root password 'PASSWORD'
    '/usr/bin/mysqladmin' -u root -h localhost password 'PASSWORD'

Alternatively you can run secure installation and it also lets you make other security-related decisions:

    '/usr/bin/mysql_secure_installation’

#### Create databases the application will need

Now you need to go into mysql with your ROOTPASSWORD and create databases and users with strong passwords for PASSWORD

    mysql -u root -pROOTPASSWORD
    
    create database cci;
    create user 'cci'@'localhost' identified by 'PASSWORD';
    use cci;
    
    GRANT ALL ON cci.* to 'cci'@'localhost' identified by 'PASSWORD';
    
> Important: Our django application needs to have these passwords. There will be a reminder below to include them in app/cci/settings.py.

# Installing Apache  <a id="apache"></a>

Most servers have apache installed. We will use Apache 2.4 here. 

> Note: There were configuration file changes from 2.2 to 2.4. Our configuration (cci.conf) is for 2.4

However, because we need to use mod_wsgi to connect Python to apache, we need to install the http_devel package if it is not already there.

    sudo yum install http-devel

> Note: You probably want to test that Apache is running OK on the default port so you know that Apache is working OK in case you have problems connecting through to the application.

# Installing Python  <a id="python"></a>

Most servers have Python 2.7.x installed. That is fine as we require 2.7. If you don’t have that installed, please do so, or if you have less than 2.7.9, please install at least that level. 

**Important note**

> We are going to need to build two python libraries instead of using pip inside the virtual environment. When we build them, we will need to do so outside the virtual environment because we need the python development tools for that version. 

> So you cannot use a different version of Python inside the virtual environment. (You could if you used a pip version of mod_wsgi and changed the Python Image Library to Pillow and used pip to install it. But we will not cover that here.)


When you’re using UNIX/Linux you will need to build from source and will need the development tools installed (which you should already have from the Redis installation. Building it from source will take a little while. 

> Note: we need zlib support, so if you’re going to compile it from scratch, uncomment that line in Modules/Setup so it is turned on.

It is important to also have the Python development libraries installed. That can be done with:

    sudo yum install python-devel

# Installing Node  <a id="node"></a>

One of the most important components of CCI is the Etherpad application, which is written in Javascript and uses the node framework. So we need to install Node. 

Newer versions of node will most likely work, but the one we have done testing on is the 0.10.26 release.

    curl -O http://nodejs.org/dist/v0.10.26/node-v0.10.26-linux-x64.tar.gz
    tar xzf node-v0.10.26-linux-x64.tar.gz
    sudo cp -rp node-v0.10.26-linux-x64 /usr/local/
    sudo ln -s /usr/local/node-v0.10.26-linux-x64 /usr/local/node
    sudo ln -s /usr/local/node-v0.10.26-linux-x86/lib/node_modules /usr/local/lib/node_modules

Now you need to add this to your path, here at the shell, and in your account’s login script to pick it up each time:

    export PATH=$PATH:/usr/local/node/bin


# Installing CCI Application Code  <a id="code"></a>

First, create the directory where all of this will go (it can go anywhere):

    mkdir app
    
##### Note: if you use another directory name, you need to change the following properties files to match:

    /cci/bootstrap.py
    /cci/django.wsgi
    /cci/server_conf/cci.conf

Make this owned by cci-user and group wheel.

    sudo chown -R cci-user:wheel app

Now you need the code. You can either download the zip and expand inside the app directory or execute the proper git command to hit the repository, which will look something like this:

    git clone /[github-account]/cci.git

This should create a directory called “cci” that has directories in it such as: cci and nps.

At the top level, we need to create a media directory and then to give the wheel group read and write permissions to it so apache can use it:

    mkdir media
    chmod -R g+rw media

We need to do a similar thing for a static directory inside the cci directory:

    cd cci
    mkdir static
    chmod -R g+rw static

# Python Application Setup  <a id="pythonapp"></a>

Let’s install a virtual environment

    pip install virtualenv

Then let’s create virtual environment in our project inside the app directory:

    virtualenv env

(If you don't use the name 'env' then you need to change that in /cci/django.wsgi to match.)

Assuming that worked fine, now switch to that virtualenv

    source env/bin/activate

Time to install mod_wsgi. It is possible to use pip, but we will install it with yum:

    sudo yum install mod_wsgi

We now can install all the python packages that python needs. Do this from the app/cci directory:

    pip install -r requirements/apps.txt

We now can create the Python Django superuser:

    python ./manage.py createsuperuser

(If you get some sort of strange MySQL config error, you may have skipped the installation of the MariaDB-devel package in the MySQL section above.)

Now we need to go get a package that CCI needs that went out of service and can’t be installed with pip. It’s the Python Image Library, which we need to go get and compile:

    curl -O http://effbot.org/media/downloads/Imaging-1.1.7.tar.gz
    unzip Imaging-1.1.7.tar.gz
    cd Imaging-1.1.7
    python setup.py install

> Note: If you get a compilation error, try building it outside your virtual environment. If it works there, the simplest workaround it to build it outside, and then copy the PIL.pth file and the PIL directory from your system's site-packages directory to the one inside your virtual environment.

As is standard with django applications, you need to run collectstatic to get your assets ready:

    cd app/cci
    python ./manage.py collectstatic
    
We need to make sure there is support for sending emails, which the application does (to the addresses in settings.py) if there are errors. Note that you cannot run the application without email support.

We will use postfix. If it isn't installed, do so:
    
    sudo yum install postfix
    
The configuration file will be at:  /etc/postfix/main.cf  The defaults will probably be fine.

To start it:

    sudo systemctl start postfix.service
    

# Python Application Settings <a id="pythonsettings"></a>

Now we need to set some variables in the app/settings.py file.

Near the top, you can set the hostnameProd to your server name. If you are using a test server in your configuration, you can set that as well. If you don’t set the hostnameProd variable, you will run in development mode.

You can also set the ADMINS_EXTRA and ADMINS fields for those supervising this application.

Somewhere around line 30, you'll see the database credentials you set for those two databases in the MySQL installation section. Put them in for the databases cci and el, and also host and port information if you dind't use default values.

At around line 80, you need to change the install_root to the absolute location for where cci lives. Something like:

    install_root = '/home/USERNAME/app/cci/'

You do need to set SECRET_KEY to something unique for security in Python Django. It cannot be blank, as it is here in the settings file.

At the end there are lots of settings that start with MCI. Look through them and change accordingly, particularly the “Prod” domain settings, since that’s what you’ll be using. Some notes:

Ether pad must use a different port than the CCI application itself. This will be transparent to the end user. We suggest putting it on 9001, but we have run it successfully on 443.

MCI_ETHERPAD_API_KEY is a value that will be set inside the Etherpad application in the filed called APIKEY.text in the root directory. If you do not set this value, the Python application cannot communicate with Etherpad.


# Python-Apache Configuration  <a id="apacheconfig"></a>

Now we need to get the CCI application, Apache, and WSGI connected.

We need to change the cci.conf file. It is in app/cci/server_conf/ and needs to be changed in the following way:

1. Make sure WSGIPythonHome is pointing to your virtual environment directory
1. In the virtual host, change the ServerAdmin field to administrator email.
1. Make sure the Document Root points to the right place.
1. Make sure the user and group match what you set up in the users and groups in the beginning of these instructions

In the cci.conf file in your app/cci/server_conf directory, make sure that you have a line that loads the wsgi_module and that it points to wherever it is:

    LoadModule wsgi_module /opt/rh/python27/root/usr/lib64/python2.7/site-packages/mod_wsgi/server/mod_wsgi-py27.so

Copy Apache config from your installation to /etc/httpd/conf (changes listening port from 80 to 8081), and restart apache

    cp app/cci/server_conf/httpd.conf /etc/httpd/conf
    /etc/init.d/httpd restart &

If you’re not using a virtual environment,  comment out WSGIPythonHome line (otherwise it needs to point to your virtual environment)

Copy cci.conf to the conf.d directory in Apache, probably at /etc/httpd/conf.d

    sudo cp app/cci/cci/server_conf/cci.conf /etc/httpd/conf.d

There is an application-specific wsgi file you need to check: 

    app/cci/django.wsgi

In that file, make sure that ALLDIRS points to the correct site-packages directory with a line something like:

    ALLDIRS = /home/edfactor/app/cci/env/lib/python2.7/site-packages

# Obtaining and Patching Etherpad  <a id="etherpad"></a>

Etherpad has different licensing than CCI, so you need to obtain it separately and apply the supplied patch file.

> Note: if you would like to learn more about Etherpad, or what version we are using, please consult the ETHERPAD.md file in the root directory.

Go to the CCI root and use curl to get the 1.5.7 version:
    
    curl -LOk https://github.com/ether/etherpad-lite/archive/1.5.7.zip
    
Then enter that directory and apply the patch:
    
    cd etherpad-lite-1.5.7
    patch -p1 < ../etherpad-157-cci.patch
    
When asked, type "y" to proceed.

After the information messages scroll by, your installation will be ready.


# Etherpad Configuration  <a id="etherpadconfig"></a>

We need to make a symbolic link from the version-specific Etherpad directory to a generic name that we can use when referencing it. Go into the app directory and create one.

    ln -s etherpad-lite-1.5.7 etherpad-lite

#### Creating and Modifying the properties file

You will notice at the root of Etherpad a properties file called settings.json.template. Please copy that into a new file called settings.json. We will change some values in there.

Starting at the top.

_Etherpad Port_

The default port of Etherpad is 9001. Users of CCI won't see this, but they will be using this. The only requirement is that this port is visible from the outside and that your system user has the privileges to open it.


_Changing the database_

We need to tell Etherpad we are using Redis to track all the real-time changes.

At around line 33, find the line that begins with...

    //The Type of the database.

Under that you will see a section to tell Etherpad to use the default dirty database:

    "dbType" : "dirty",
    //the database specific settings
    "dbSettings" : {
    "filename" : "var/dirty.db"
    },

First, comment that out in some way, such as:

    // "dbType" : "dirty",
    //the database specific settings
    // "dbSettings" : {
    // "filename" : "var/dirty.db"
    // },

Now you need to add in a new section for Redis:

    "dbType" : "redis",
    "dbSettings" : { 
      "host" : "localhost"
    , "port" : 6379
    , "database": 1
    },
    
...of course, if you aren't using the default configuration, such as a different port number or security credentials, you might have something like this:
 
    "dbType" : "redis",
    "dbSettings" : { 
      "user" : "username"
    , "password" : "password"
    , "host" : "localhost"
    , "port" : 4444
    , "database": 1
    },

_Default Text_

You're probably better off getting rid of the welcome text. 

You can change it to:

    "defaultPadText" : "",

_Logging_

The section that begins with:

    "logconfig" :
    
... is the one we are interested in. It describes where log messages are supposed to go. They can go anywhere, but the choices are primarily the console (not very useful for a production system) or to some sort of file.
    
Let's get rid of console logging by commenting out this section:

    { "type": "console"
       //, "category": "access"// only logs pad access
    }
    
So it looks like this:
   
    // { "type": "console"
    //, "category": "access"// only logs pad access
    //     }

The section immediately after is a sample for a log file. It looks like this:

      /*
      , { "type": "file"
      , "filename": "your-log-file-here.log"
      , "maxLogSize": 1024
      , "backups": 3 // how many log files there're gonna be at max
      //, "category": "test" // only log a specific category
      } */

We want to uncomment that, get rid of that first comma before the type, and then change the declaration.

You will want to use an absolute path for this log file. We're going to put all logs into a logs directory under app, which we will create in the next section:

      { "type": "file"
      , "filename": "/home/USERNAME/app/logs/etherpad.log"
      , "maxLogSize": 100024
      , "backups": 6 // how many log files there will be at max
      }
        
... and you can change the location, maximum log file size and how many backups to whatever suits you.


(If you’re just experimenting, you can create an APIKEY.txt file there containing a key that’s a long, strong password like: somelongteststringwithlettersand1231)

You also need to set a key in the SESSIONKEY.txt file. You must create that yourself.

#### Installing supporting Javascript libraries

Etherpad is a javascript application, and you need to install the packages it needs. You can do that by going to the directory app/etherpad-lite/src and using npm:

    npm install

It will pick up the packages you need from the package.json file there.

#### Installing forever 

We need to install the forever javascript library to watch over our Etherpad application and restart it if there is a problem.

Install it like this:

    sudo /usr/local/node/bin/npm install forever -g


# Setting up Log Files  <a id="logs"></a>

We need to set up our logs. There are five application logs for CCI. One is for Etherpad itself (see last section) and four are from our django application.

We are going to put our logs under app/logs. You can put it anywhere, but that directory must match what's in settings.json in Etherpad, and settings.py for django.

    cd app
    mkdir logs
    touch etherpad.log
    touch cci_spoof.log
    touch cci_audit.log
    touch cci_debug.log
    touch cci_concentration_cards_debug.log
    
We need the user who is running the application to be able to write to all those log files.

    cd ..
    sudo chown -R cci-user:cci logs

Also, note that there are two other logs created in the cci.conf file for Apache to use. They are cci-access_log and cci-error_log and are going to be in a directory like:

    /var/log/httpd/

# Preparing Databases  <a id="dbpreparation"></a>

The application needs three databases, two in MySQL, and one in Redis. You don’t need to start a fresh installation with existing data, though you may decide to do so. In the case of MySQL, just take your dump file and import it. For Redis, just swap in your file - standard name will be dump.rdb, and put it into the data directory, probably replacing the standard one there if it has already been generated by running it the first time.

However, if you are starting from scratch, you do need to create the schema for the CCI database in MySQL. That means you need to run a migration. Go into the CCI application root and enter these two commands:

    python ./manage.py migrate mci —list
    python ./manage.py syncdb


# API and Session Keys  <a id="keys"></a>

You need to install API Key by running Etherpad once from the root directory. Don’t worry if you’ve got everything configured correctly. We just need to run it once from inside the etherpad-lite directory:

    forever start -l /home/USERNAME/app/logs/etherpad.log --append ./node_modules/ep_etherpad-lite/node/server.js & 

It will generate a file - APIKEY.txt - and you can paste that value in the app/cci/settings.py file near the end at around line 272 in the variable MCI_ETHERPAD_API_KEY.

To shut down Etherpad, you must manually kill the two processes: first the forever process, then the other Etherpad process.

# How to Run the Application  <a id="running"></a>

Assuming you have everything installed and the databases are running, you need to start both the Django and Etherpad applications. 

If you have Apache and WSGI set up properly, all you have to do is start apache and the Django application will be running normally. 

You just need to start Etherpad. The version of Node that we are using does not let Etherpad run robustly, so we use the forever javascript package to run it, which can restart it if it goes down. At the command line, start the application from the root of the Etherpad directory (important!) and make sure you have the absolute party right for the log file:

    forever start -l /home/USERNAME/app/logs/etherpad.log --append ./node_modules/ep_etherpad-lite/node/server.js &























