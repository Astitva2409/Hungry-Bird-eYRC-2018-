#!/usr/bin/env python

'''

This python file runs a ROS-node of name drone_control which holds the position of e-Drone on the given dummy.
This node publishes and subsribes the following topics:

		PUBLICATIONS			SUBSCRIPTIONS
		/drone_command			/whycon/poses
		/alt_error				/pid_tuning_altitude
		/pitch_error			/pid_tuning_pitch
		/roll_error				/pid_tuning_roll
		/yaw_error				/pid_tuning_yaw
								/drone_yaw

Rather than using different variables, use list. eg : self.setpoint = [1,2,3,4], where index corresponds to x,y,z and yaw_value...rather than defining self.x_setpoint = 1, self.y_setpoint = 2
CODE MODULARITY AND TECHNIQUES MENTIONED LIKE THIS WILL HELP YOU GAINING MORE MARKS WHILE CODE EVALUATION.	
'''

# Importing the required libraries

from plutodrone.msg import *
from geometry_msgs.msg import PoseArray
from std_msgs.msg import Int16
from std_msgs.msg import Int64
from std_msgs.msg import Float64
from pid_tune.msg import PidTune
import rospy
import time


class Edrone():
	"""docstring for Edrone"""
	def __init__(self):
		
		rospy.init_node('drone_control')	# initializing ros node with name drone_control

		# This corresponds to your current position of drone. This value must be updated each time in your whycon callback
		# [x,y,z,yaw_value]
		self.drone_position = [0.0,0.0,0.0,0.0]	

		# [x_setpoint, y_setpoint, z_setpoint, yaw_value_setpoint]
		self.setpoint =[-8.39,4.98,27.92,.01] # whycon marker at the position of the dummy given in the scene. Make the whycon marker associated with position_to_hold dummy renderable and make changes accordingly


		#Declaring a cmd of message type PlutoMsg and initializing values
		self.cmd = PlutoMsg()
		self.cmd.rcRoll = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcThrottle = 1500
		self.cmd.rcAUX1 = 1500
		self.cmd.rcAUX2 = 1500
		self.cmd.rcAUX3 = 1500
		self.cmd.rcAUX4 = 1500
		# self.cmd.plutoIndex = 0


		#initial setting of Kp, Kd and ki for [pitch, roll, throttle, yaw]. eg: self.Kp[2] corresponds to Kp value in throttle axis
		#after tuning and computing corresponding PID parameters, change the parameters
		self.Kp = [5,5,32,2]
		self.Ki = [0,0,0,0]
		self.Kd = [0,0,240,0]


		#-----------------------Add other required variables for pid here ----------------------------------------------
                self.error=[0,0,0,0]
                self.error_sum=[0,0,0,0]
                self.error_rate=[0,0,0,0]
  
                self.previous_error=[8.39,-4.98,-27.92,0.0]
                self.max_values=[1800,1800,1800,1530]
                self.min_values=[1200,1200,1200,1480]
                self.out=[0,0,0,0]   
                







		# Hint : Add variables for storing previous errors in each axis, like self.prev_values = [0,0,0,0] where corresponds to [pitch, roll, throttle, yaw]
		#		 Add variables for limiting the values like self.max_values = [1800,1800,1800,1800] corresponding to [pitch, roll, throttle, yaw]
		#													self.min_values = [1200,1200,1200,1200] corresponding to [pitch, roll, throttle, yaw]
		#																	You can change the upper limit and lower limit accordingly. 
		#----------------------------------------------------------------------------------------------------------

		# This is the sample time in which you need to run pid. Choose any time which you seem fit. Remember the stimulation step time is 50 ms
		self.sample_time = 0.060 # in seconds







		# Publishing /drone_command, /alt_error, /pitch_error, /roll_error, /yaw_error
		self.command_pub = rospy.Publisher('/drone_command', PlutoMsg, queue_size=1)
		#------------------------Add other ROS Publishers here-----------------------------------------------------
                self.alt_err_pub = rospy.Publisher('/alt_error', Float64 ,queue_size=1)
                self.pitch_err_pub = rospy.Publisher('/pitch_error', Float64 ,queue_size=1)
                self.roll_err_pub = rospy.Publisher('/roll_error', Float64 ,queue_size=1)
                self.yaw_err_pub = rospy.Publisher('/yaw_error', Float64 ,queue_size=1)
                self.zero=rospy.Publisher('/zero_line',Float64,queue_size=1)





		#-----------------------------------------------------------------------------------------------------------


		# Subscribing to /whycon/poses, /drone_yaw, /pid_tuning_altitude, /pid_tuning_pitch, pid_tuning_roll
		rospy.Subscriber('whycon/poses', PoseArray, self.whycon_callback)
		rospy.Subscriber('/pid_tuning_altitude',PidTune,self.altitude_set_pid)
		#-------------------------Add other ROS Subscribers here----------------------------------------------------
                rospy.Subscriber('/pid_tuning_yaw', PidTune , self.yaw_set_pid)
                rospy.Subscriber('/pid_tuning_pitch',PidTune,self.pitch_set_pid)
                rospy.Subscriber('/pid_tuning_roll',PidTune,self.roll_set_pid)
                rospy.Subscriber('/drone_yaw', Float64, self.yaw_callback)





		#------------------------------------------------------------------------------------------------------------
                self.disarm()
		self.arm() # ARMING THE DRONE
           
             
                while(1):
          
                  self.pid()
                  rospy.sleep(self.sample_time)
                
                 


	# Disarming condition of the drone
	def disarm(self):
		self.cmd.rcAUX4 = 1100
		self.command_pub.publish(self.cmd)
		rospy.sleep(1)


	# Arming condition of the drone : Best practise is to disarm and then arm the drone.
	def arm(self):

		self.disarm()
		self.cmd.rcRoll = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcThrottle = 1000
		self.cmd.rcAUX4 = 1500
		self.command_pub.publish(self.cmd)	# Publishing /drone_command
		rospy.sleep(1)



	# Whycon callback function
	# The function gets executed each time when /whycon node publishes /whycon/poses 
	def whycon_callback(self,msg):
		self.drone_position[0] = msg.poses[0].position.x
                
		#--------------------Set the remaining co-ordinates of the drone from msg----------------------------------------------
               
                self.drone_position[1]=msg.poses[0].position.y
                self.drone_position[2]=msg.poses[0].position.z

        def yaw_callback(self,msg):
                self.drone_position[3]=msg.data
        

		
		#---------------------------------------------------------------------------------------------------------------



	# Callback function for /pid_tuning_altitude
	# This function gets executed each time when /tune_pid publishes /pid_tuning_altitude
	def altitude_set_pid(self,alt):
		self.Kp[2] = alt.Kp * 0.06 # This is just for an example. You can change the fraction value accordingly
		self.Ki[2] = alt.Ki * 0.008
		self.Kd[2] = alt.Kd * 0.03

	#----------------------------Define callback function like altitide_set_pid to tune pitch, roll and yaw as well--------------

        def pitch_set_pid(self,pitch):
              self.Kp[0]=pitch.Kp*.006
              self.Ki[0]=pitch.Ki*.008
              self.Kd[0]=pitch.Kd*.03
        def roll_set_pid(self,roll):    
              self.Kp[1]=roll.Kp*.006
              self.Ki[1]=roll.Ki*.00008
              self.Kd[1]=roll.Kd*.03
        
        def yaw_set_pid(self,yaw):
              self.Kp[3]=yaw.Kp*.006
              self.Ki[3]=-yaw.Ki*.00008
              self.Kd[3]=yaw.Kd*.03

       
       
       
          
         
                 
	#----------------------------------------------------------------------------------------------------------------------


	def pid(self):
	#-----------------------------Write the PID algorithm here--------------------------------------------------------------

	# Steps:
	# 	1. Compute error in each axis. eg: error[0] = self.drone_position[0] - self.setpoint[0] ,where error[0] corresponds to error in x...
	#	2. Compute the error (for proportional), change in error (for derivative) and sum of errors (for integral) in each axis. Refer Getting_familiar_with_PID.pdf to understand PID equation.
	#	3. Calculate the pid output required for each axis. For eg: calcuate self.out_roll, self.out_pitch, etc.
	#	4. Reduce or add this computed output value on the avg value ie 1500. For eg: self.cmd.rcRoll = 1500 + self.out_roll. LOOK OUT FOR SIGN (+ or -). EXPERIMENT AND FIND THE CORRECT SIGN
	#	5. Don't run the pid continously. Run the pid only at the a sample time. self.sampletime defined above is for this purpose. THIS IS VERY IMPORTANT.
	#	6. Limit the output value and the final command value between the maximum(1800) and minimum(1200)range before publishing. For eg : if self.cmd.rcPitch > self.max_values[1]:
	#																														self.cmd.rcPitch = self.max_values[1]
	#	7. Update previous errors.eg: self.prev_error[1] = error[1] where index 1 corresponds to that of pitch (eg)
	#	8. Add error_sum
                
              
                      
                  







	#------------------------------------------------------------------------------------------------------------------------
                print("Current Position",self.drone_position)
                for i in range(4):
               
                 self.error[i]=self.drone_position[i]-self.setpoint[i]
                 self.error_sum[i]+=self.error[i]*self.sample_time
                 self.error_rate[i]=(self.error[i]-self.previous_error[i])/self.sample_time
                 self.out[i]=(self.Kp[i]*self.error[i])+(self.Kd[i]*self.error_rate[i])-(self.error_sum[i]*self.Ki[i])
        
                 self.previous_error[i]=self.error[i]
                 if 1500+(self.out[i])>self.max_values[i]:
                      self.out[i]=self.max_values[i]-1500
                 if 1500+self.out[i]<self.min_values[i]:
                      self.out[i]=self.min_values[i]-1500
               	self.cmd.rcRoll = 1500+self.out[1]
		self.cmd.rcPitch = 1500+self.out[0]
		self.cmd.rcYaw = 1500-self.out[3]
		self.cmd.rcThrottle = 1500+self.out[2]
                self.alt_err_pub.publish(self.error[2])
                self.pitch_err_pub.publish(self.error[0])
                self.roll_err_pub.publish(self.error[1])
                self.yaw_err_pub.publish(self.error[3])
                self.zero.publish(0)
		#print("Roll ",1500+self.out[1], " Pitch ",1500+self.out[0]," Yaw ",1500+self.out[3]," Throttle ",1500+self.out[2])
	        self.command_pub.publish(self.cmd)
                



if __name__ == '__main__':

	e_drone = Edrone()
      

	while not rospy.is_shutdown():
		e_drone.pid()
