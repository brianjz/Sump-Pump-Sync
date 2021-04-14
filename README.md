# Sump Pump Sync
Used to sync local sump pump run data with remote server using an SSH Tunnel.
 
During the rainy season, my sump pump runs pretty constantly. For whatever reason it seems the neighborhood underground water flows right to my house. 
 
I had previously set up a flow of the Sump Pump on a WeMo Insight Switch connected to IFTTT which wrote events to a Google Spreadsheet every time it went on. From there I wrote a quick web page using charts.js to show how often it was running. It was a good way to see the trend and if I needed to keep an eye on it. That broke (partly due to me switching to a new WeMo switch that didn't support device on/off attributes) and the fact that IFTTT has been pretty unreliable recently.
 
## Home Assistant
I recently found <a href="https://www.home-assistant.io/">Home Assistant</a> and immediately fell in love. 
 
I spent some time and was able to get the data I needed from the WeMo Insight Switch. Then, using some clever Node-RED flows, I was able to get the timestamp into a local SQL server database. Though, I wanted to data to be viewable when I was not home, so I needed to get it to my remote SQL server, but that was only accessible through an SSH tunnel which I could not figure out how to do in Node-RED. 

![Node-RED setup](https://github.com/brianjz/sump-pump-sync/raw/master/nodered.png)

I also needed to poll the WeMo Insight Switch every 10 seconds since the default state of the device points to the actual switch (on/off) and not the device plugged into it (the sump pump). So, I need to see if the Sump Pump itself is on. I do this by accessing the WeMo device data and grabbing the attribute named "state_detail" which lets me know the state of the sump pump itself (standby/on). From there it does some logic if it's on or off and writes to the database.

It also publishes a message of the WeMo attributes to the Home Assistant MQTT server so I can use that data elsewhere, if needed.

As a workaround, I wrote a Python script to sync the databases based on the most recent timestamp on the remote server. I just have this scheduled to run in Task Scheduler every 5 minutes until I possibly find a more efficient route. 

Inside the python script, it also calulates the length of time from the previous run until the most recent run. This helps to determine trends. I also publish this to the HA MQTT server and turn it into a sensor. In the bottom of the Node-RED flow, there is a sequence that should hopefully alert me (only once) if the time between runs falls below 5 minutes, so that I can keep an eye on it during big rain.
