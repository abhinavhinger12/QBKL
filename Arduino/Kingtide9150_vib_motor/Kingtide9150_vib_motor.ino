 /*
 Group no: 16
 Date(last edited, including comments): 11th November, 2018, 7:01 pm
 Group Members: Abhinav Hinger, Akhil Chandra Panchumarthi, Ansh Sood, Shimona Verma
 Desciption:
        Uses collected pitch value of MPU9150 to check if posture is proper or not, generates vibration if incorrect after 10 seconds
 */
 
 #include "Wire.h"                            //required libraries for MPU 9150
 #include "I2Cdev.h"  
 #include "RTIMUSettings.h"  
 #include "RTIMU.h"  
 #include "RTFusionRTQF.h"   
 #include "CalLib.h"  
 #include "EEPROM.h"  
 
 RTIMU *imu;                                  // the IMU object  
 RTFusionRTQF fusion;                         // the fusion object  
 RTIMUSettings settings;                      // the settings object  
 // DISPLAY_INTERVAL sets the rate at which results are displayed  
 #define DISPLAY_INTERVAL 1000                // interval between pose displays  
 // SERIAL_PORT_SPEED defines the speed to use for the debug serial port  
 
 #define SERIAL_PORT_SPEED 9600               //baudrate
 unsigned long lastDisplay;  
 unsigned long lastRate;  
 int sampleCount; 
 uint8_t vib_count =0;                        //timer for vibration 
 int vib_pin = 40;                            //high end of vibration motor
 const int lower = 60
 const int upper = 120
 
 void setup()  
 {  
   int errcode;  
   Serial.begin(SERIAL_PORT_SPEED);  
   Wire.begin();  
   imu = RTIMU::createIMU(&settings);                                                     // create the imu object  
   Serial.print("ArduinoIMU starting using device "); Serial.println(imu->IMUName());  
   if ((errcode = imu->IMUInit()) < 0) {  
     Serial.print("Failed to init IMU: "); Serial.println(errcode);                       //initialization code for imu (uses libraries)
   }  
   if (imu->getCalibrationValid())  
     Serial.println("Using compass calibration");                                         //uses ArduinoMagCal.ino calibration stored on Arduino (if exists)
   else  
     Serial.println("No valid compass calibration data");  
   lastDisplay = lastRate = millis();  
   sampleCount = 0;  
   // Slerp power controls the fusion and can be between 0 and 1  
   // 0 means that only gyros are used, 1 means that only accels/compass are used  
   // In-between gives the fusion mix.  
   fusion.setSlerpPower(0.02);  
   // use of sensors in the fusion algorithm can be controlled here  
   // change any of these to false to disable that sensor  
   fusion.setGyroEnable(true);                                                            //for calibration purpose, all peripherals enabled
   fusion.setAccelEnable(true);  
   fusion.setCompassEnable(true);  
   Serial.println("Units");  
   Serial.println("Pose: Roll, Pitch, Magnetic Heading (measured in degrees)");           //only pitch is eventually used 
   Serial.println("----------------------------"); 
    pinMode(vib_pin,OUTPUT);                                                              //vib_pin(digital pin) set as output   
 }  
 void loop()  
 {   
   unsigned long now = millis();  
   unsigned long delta;  
   int loopCount = 1;                                                                    //collects raw values from MPU and calculates roll, pitch, and magnetic heading
   while (imu->IMURead()) {                                                              // get the latest data if ready yet  
     // this flushes remaining data in case we are falling behind  
     if (++loopCount >= 10)  
       continue;                                                                         //calculates other values (rate of change in pitch, roll, and magnetic heading, which aren't needed)
     fusion.newIMUData(imu->getGyro(), imu->getAccel(), imu->getCompass(), imu->getTimestamp());  
     sampleCount++;  
     if ((delta = now - lastRate) >= 1000) {  
       sampleCount = 0;  
       lastRate = now;  
     }  
     if ((now - lastDisplay) >= DISPLAY_INTERVAL) {  
       lastDisplay = now;  
       RTVector3 pose = fusion.getFusionPose();  
       float r = M_PI/180.0f;      // degrees to radians  
       float d = 180.0f/M_PI;      // radians to degrees  
       float roll = pose.y()*d*-1;    // left roll is negative  
       float pitch = pose.x()*d;     // nose down is negative  
       float yaw = pose.z()*d;      // 0 Yaw = 270 magnetic, this gives left or right up to 180 degrees  

       Serial.print("Pose: ");  
       Serial.print(roll);  
       Serial.print(" | ");  
       Serial.print(pitch);  
       Serial.print(" | ");  
       Serial.println(yaw);  
 
       Serial.println("----------------------------"); 
       if (pitch<lower || pitch>upper){                                                 //allowed range for good sitting posture at cubicle
           Serial.print(vib_count);
           vib_count ++;
       }
       else
           vib_count = 0;                                                               //resets vb_count if user corrects within 10 seconds
          
       if(vib_count > 10){                                                              //counter for vibration "alarm", gives 10 seconds for user to correct pose without alarm
          digitalWrite(vib_pin,HIGH);
          for(int i = 0;i<10;i++){
            analogWrite(LED_BUILTIN, 255);
            delay(200);
            analogWrite(LED_BUILTIN, 0);
            delay(200);
          }
            delay(500);
          if (!(pitch<lower || pitch>upper)){                                           //stops vibration if user corrects posture while vibrating
             break;
          }
          //delay(10000);
          digitalWrite(vib_pin,LOW);
          vib_count = 0;                                                                //resets vib_count at end of alarm (vibration)
       }
     }  
   }  
 }  
