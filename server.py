import socket
import sys
import subprocess
import os
import time
import pigpio
from thread import *
import signal

os.nice(-2)
pi = pigpio.pi("RC-RASPI", 8889)        

Motor1A = 7
Motor1B = 8
Motor1E = 25
pi.set_PWM_range(Motor1A, 100)
pi.set_PWM_range(Motor1B, 100)
pi.set_mode(Motor1E, pigpio.OUTPUT)
pi.write(Motor1E, 1)

ServoS = 18	
ServoW = 20
ServoH = 21

LED1 = 32
LED2 = 36
#pi.set_mode(LED1, pigpio.OUTPUT)
#pi.set_mode(LED2, pigpio.OUTPUT)

print "Going forwards"
heightSet = 90
widthSet = 90

pi.set_servo_pulsewidth(ServoS, 1400)
pi.set_servo_pulsewidth(ServoH, 1500)
pi.set_servo_pulsewidth(ServoW, 1500)

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'
s.listen(10)
print 'Socket now listening'

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
def countPWM(value):
    return (value / 9 * 50 + 1000)        
def countTurnPWM(value):
    return (1475 - value * 1.3)

#Function for handling connections
def clientthread(conn):
    print 'Socket has a customer'
    #Sending message to connected client
    conn.send('Welcome to the server. Receiving Data...\n') #send only takes string
    videoProcess = 0

    #infinite loop so that function do not terminate and thread do not end.
    while True:
    
        #Receiving from client
        data = conn.recv(1024)
        print data
        recvList = data.split(":")
        if is_number(recvList[0]) & (int(recvList[0]) == 0):
            if is_number(recvList[1]) & (int(recvList[1]) == 0):
                if is_number(recvList[2]) & (int(recvList[2]) == 0):
                    break
                else:
                                
                    if videoProcess != 0:
                        videoProcess.send_signal(signal.SIGQUIT)    
                        os.killpg(videoProcess.pid, signal.SIGTERM)
                    continue
            else:
                if videoProcess != 0:
                    videoProcess.send_signal(signal.SIGQUIT)    
                    os.killpg(videoProcess.pid, signal.SIGTERM)
                port = 'port=' + str(int(recvList[1])) + ' '
                height = str(int(recvList[2])) + ' '
                width = str(int(recvList[3])) + ' '
                fps = str(int(recvList[4])) + ' '
                rot = str(int(recvList[5])) + ' '
                host = 'host=' + str(addr[0])
                
                time.sleep(1)
                videoProcess = subprocess.Popen(['exec ' 'raspivid ' '-t ' '999999 ' '-w ' + width + '-h ' + height + '-fps ' + fps + '-rot ' + rot + '-b ' '2000000 ' '-o ' '- ' '| ' 'gst-launch-1.0 ' '-e ' '-vvv ' 'fdsrc ' '!  ' 'h264parse ' '! ' 'rtph264pay ' 'pt=96 ' 'config-interval=5 ' '! ' 'udpsink ' +host + ' ' +port], shell=True, preexec_fn=os.setsid)
                            
        elif is_number(recvList[0]) & (int(recvList[0]) == 1):
        
            if len(data) > 20:
                print "too long data"
                continue

            if is_number(recvList[1]):
                throttle = float(int(recvList[1]))
            if is_number(recvList[2]):
                turn = float(int(recvList[2]))
                print "throttle: "
            print turn

            if throttle > 100:
                throttle = 0
            elif throttle < -100:
                throttle = 0

            print throttle            
            if throttle >= 0:
                pi.set_PWM_dutycycle(Motor1B,   0) 
                pi.set_PWM_dutycycle(Motor1A, throttle) 
            elif throttle < 0:
                pi.set_PWM_dutycycle(Motor1A,   0) 
                pi.set_PWM_dutycycle(Motor1B, -throttle) 
                
            if turn > 100:
                turn = 100
            elif turn < -100:
                turn = -100
                
            pi.set_servo_pulsewidth(ServoS, countTurnPWM(turn))
            
            if len(recvList) <= 3:
                continue
            if is_number(recvList[3]):
                heightSet = int(recvList[3])
                pi.set_servo_pulsewidth(ServoH, countPWM(heightSet))
                
            if is_number(recvList[4]):
                widthSet = int(recvList[4])
                pi.set_servo_pulsewidth(ServoW, countPWM(widthSet))

        else:
            break

    print "Closing"
    closeConn(conn, videoProcess)
    
def closeConn(conn, videoProcess):
    if videoProcess != 0:
        videoProcess.send_signal(signal.SIGQUIT)    
        os.killpg(videoProcess.pid, signal.SIGTERM)
    
    conn.close()
    pi.set_servo_pulsewidth(ServoS, 1500)
    pi.set_servo_pulsewidth(ServoH, 1500)
    pi.set_servo_pulsewidth(ServoW, 1500)
    pi.set_PWM_dutycycle(Motor1A,   0)
    pi.set_PWM_dutycycle(Motor1B,   0)
    pi.set_pull_up_down(Motor1E, pigpio.PUD_DOWN)
	
#now keep talking with the client
while 1:
    #wait to accept a connection
    conn, addr = s.accept()
    print 'Connected with ' + addr[0] + ':' + str(addr[1])

    #start new thread
    start_new_thread(clientthread ,(conn,))
s.close()
pi.stop()
