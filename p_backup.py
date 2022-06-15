from netmiko import ConnectHandler
from datetime import date
from time import sleep
from time import perf_counter
from secrets import checkpoint_fw
from secrets import backup_server

CP_ip = checkpoint_fw.get("ip", "127.0.0.1")
fw_username = checkpoint_fw.get("username", "admin")
fw_password = checkpoint_fw.get("password", "admin")

CP_Fw_str = { 
    "host": CP_ip,
    "username": fw_username,
    "password": fw_password,
    "device_type": "linux",
    }

today = date.today().strftime("%b-%d-%Y")
backup_dir = "mdsbckp1-" + today

print("Backing up Checkpoint Firewall")
print(f"... connecting to FW {CP_ip} with user:{fw_username}")
net_connect = ConnectHandler(**CP_Fw_str)
print("Connection successful")
fw_prompt = net_connect.find_prompt()
print(fw_prompt)

command = "pwd"; print(f"{fw_prompt}"+ command)    
output = net_connect.send_command(command)
print(output)

command = "cd /var/log"
print(f"{fw_prompt}"+ command)  
net_connect.send_command(command)

command = "ls -ltd mdsbckp1*"
print(f"{fw_prompt}"+ command)  
output = net_connect.send_command(command)
print(output)

print(f"\n... creating backup in directory: {backup_dir} ")
command = f"mkdir {backup_dir}"
output = net_connect.send_command(command)
print(output)
sleep(5)

if "Directory not empty" in output:
    print(output)
    command = f"ls {backup_dir}"
    print(f"{fw_prompt}"+ command)  
    print(net_connect.send_command(command))
    #print("... Exiting program ")
    #print("Good-bye!")
    print(f"\n... removing directory - {backup_dir}") 
    command = f"rmdir --ignore-fail-on-non-empty {backup_dir}"   
    net_connect.send_command(command)
    print(f"... creating backup in directory: {backup_dir} \n")
    command = f"mkdir {backup_dir}"
    output = net_connect.send_command(command)
    sleep(10)
    #net_connect.disconnect()
    #exit()


command = f"cd {backup_dir}"
print(f"{fw_prompt}"+ command)  
print(net_connect.send_command(command))

command = "mdsenv"; print(f"{fw_prompt}"+ command)
print(net_connect.send_command(command)); sleep(2)

command = "mdsstop"; print(f"{fw_prompt}"+ command)
print(net_connect.send_command(command)); sleep(5)

command = "mdsstat"; print(f"{fw_prompt}"+ command)
print(net_connect.send_command(command))

start_time = perf_counter()
#command = "mds_backup -l -b -v 2>/dev/null";
try:
    command = "mds_backup -l -b 2>/dev/null"; print(f"{fw_prompt}"+ command)
    print(net_connect.send_command(command, delay_factor=36))
except:
    end_time = perf_counter()
    print(f"mds_backup -l -b 2>/dev/null took {end_time - start_time:0.4f} secs")
    raise
    
end_time = perf_counter()
print(f"mds_backup -l -b 2>/dev/null took {end_time - start_time:0.4f} secs")

command = "mdsstart"; print(f"{fw_prompt}"+ command)
print(net_connect.send_command(command)); sleep(180)

command = "mdsstat"; print(f"{fw_prompt}"+ command)
print(net_connect.send_command(command))

command = f"ls -lt"
print(f"{fw_prompt}"+ command)  
print(net_connect.send_command(command))

command = f"cd ..; ls -ltd mdsbckp1*"
print(f"{fw_prompt}"+ command)  
print(net_connect.send_command(command))

#Remove Oldest Backup.
command = "ls -td mdsbckp1* | tail -n 1 | xargs rm -fr "
print(f"{fw_prompt}"+ command)  
net_connect.send_command(command)

command = f"ls -ltd mdsbckp1*"
print(f"{fw_prompt}"+ command)  
print(net_connect.send_command(command))

net_connect.disconnect()

backup_server_ip = backup_server.get("ip")
username = backup_server.get("username")
password = backup_server.get("password")


backup_server = {
    "host": backup_server_ip ,
    "username": username,
    "password": password,
    "device_type": "linux",
}

print("Backing up to Backup Server")
print(f"... connecting to FW {backup_server_ip} with user:{username}")
net_connect = ConnectHandler(**backup_server)
print("Connection successful")
srv_prompt = net_connect.find_prompt()
print(srv_prompt)

command = "cd /gsn/nodes/Provider_1/backups"
print(f"{srv_prompt}"+ command)  
net_connect.send_command(command, expect_string="backups")

srv_prompt = net_connect.find_prompt()

command = "ls -lt"
print(f"{srv_prompt}"+ command)  
print(net_connect.send_command(command))

#Remove Oldest Backup.
command = "ls -t | tail -n 1 | xargs rm -fr "
print(f"{srv_prompt}"+ command)  
net_connect.send_command(command)

start_time = perf_counter()
command = f"scp -r {fw_username}@{CP_ip}:/var/log/{backup_dir} ."
#command = "scp -r admin@172.27.11.100:/var/log/mdsbckp1-May-21-2021 ."
#command = "scp -r admin@172.27.11.100:/var/log/test ."
print(f"{srv_prompt}"+ command)  

print(net_connect.send_command(command, expect_string="password"))
#expect_string: admin@172.27.11.100's password:
#net_connect.send_command(fw_password + "\n")
#output = net_connect.send_command_timing(fw_password, strip_prompt=False, strip_command=False)
output = net_connect.send_command_timing(fw_password)

print(output)

end_time = perf_counter()
print(f"{command} took {end_time - start_time:0.4f} secs")

command = "ls -lt"
print(f"{srv_prompt}"+ command)  
print(net_connect.send_command(command))

net_connect.disconnect()
