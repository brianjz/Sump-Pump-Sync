import connect as db
import paramiko
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
import paho.mqtt.client as mqtt

mypkey = paramiko.RSAKey.from_private_key_file("PPK", "PASS")

sql_hostname = ''
sql_port = 3306
ssh_host = ''
ssh_user = ''
ssh_port = 22

with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_pkey=mypkey,
        remote_bind_address=(sql_hostname, sql_port)) as tunnel:
    rconn = db.remoteconnect(tunnel.local_bind_port)
    rcursor = rconn.cursor()
    rcursor.execute("SELECT timestamp FROM sumppump ORDER BY timestamp DESC LIMIT 1")
    latest_remote = rcursor.fetchone()[0]
    print("Finding most recent timestamp on remote server --> "+str(latest_remote))

    isDev = 0
    conn = db.connect(isDev)
    cursor = conn.cursor()
    cursor.execute("SELECT time_on FROM sump_pump ORDER BY time_on DESC LIMIT 2")
    latest = cursor.fetchone()[0]
    print("Finding most recent timestamp on local server --> "+str(latest))
    previous = cursor.fetchone()[0]

    timediff = latest - previous
    print("Publishing last time difference to MQTT server...")
    broker_address="" 
    client = mqtt.Client("SumpPumpSync") #create new instance
    client.username_pw_set(username="user",password="pass")

    print("--> Connecting to broker")
    client.connect(broker_address) #connect to broker

    print("--> Publishing to topic","sensors/sump_pump/last_run")
    client.publish("sensors/sump_pump/last_run", timediff, 1)#publish

    client.disconnect()

    updates = {}
    if(latest > latest_remote):
        print("Local is newer. Updating remote server with latest entries...")
        sqldata = {"larem": int(latest_remote)}
        cursor.execute("SELECT * FROM sump_pump WHERE time_on > %(larem)s ORDER BY time_on ASC", sqldata)
        updates = cursor.fetchall()

        for up in updates:
            update_sql = "INSERT INTO sumppump (status, timestamp, sheetkey, power_usage) VALUES (1, %(ts)s, NULL, %(power)s)"
            sqldata = {"ts": int(up[1]), "power": float(up[2])}
            rcursor.execute(update_sql, sqldata)
            rconn.commit()


db.closeconn(rconn, rcursor)
db.closeconn(conn, cursor)