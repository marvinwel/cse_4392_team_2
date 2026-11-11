package cse4392;

import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.concurrent.CountDownLatch;

public class SeasonSwitch implements ActionListener {
   static int state=0;
   static final int OFF=0, COOL=1, HEAT=2;
   AC ac=new AC();
   Heater heater=new Heater();
   Timer timer=new Timer(1200, this);
   Room room=new Room();
   int coolTemp=68;
   int heatTemp=77;
   public void cool() {
      switch (state) {
         case OFF:
            ac.on();
            timer.start();
            state=COOL;
            System.out.println("Cooling started. RmTemp="+room.temp);
            break;
         case COOL: break;
         case HEAT:
            heater.off();
            ac.on();
            timer.start();
            state=COOL;
            System.out.println("Cooling started. RmTemp="+room.temp);
            break;
      }
   }
   public void heat() {
      switch (state) {
         case OFF:
            heater.on();
            timer.start();
            state=HEAT;
            System.out.println("Heating started. RmTemp="+room.temp);
            break;
         case HEAT: break;
         case COOL:
            ac.off();
            heater.on();
            timer.start();
            state=HEAT;
            System.out.println("Heating started. RmTemp="+room.temp);
            break;
      }
   }
   public void off() {
      switch (state) {
         case OFF: break;
         case HEAT:
            heater.off();
            timer.stop();
            state=OFF;
            System.out.println("Heating stopped. RmTemp="+room.temp);
            break;
         case COOL:
            ac.off();
            timer.stop();
            state=OFF;
            System.out.println("Cooling stopped. RmTemp="+room.temp);
            break;
      }
   }
   public void actionPerformed(ActionEvent e) {
      timerOff();
   }
   public void timerOff() {
      switch (state) {
         case OFF: break;
         case COOL:
            if (room.temp>coolTemp) {
               ac.on();
               System.out.println("Cooling started. RmTemp="+room.temp);
            } else {
               ac.off();
               System.out.println("Cooling stopped. RmTemp="+room.temp);
            }
            break;
         case HEAT:
            if (room.temp<heatTemp) {
               heater.on();
               System.out.println("Heating started. RmTemp="+room.temp);
            } else {
               heater.off();
               System.out.println("Heating stopped. RmTemp="+room.temp);
            }
            break;
      }
   }    
   public static void main(String[] args) {
      System.out.println("Enter off, cool or heat to run. "+
         "Press Ctrl-c to exit.");
      SeasonSwitch s=new SeasonSwitch();
      s.room.timer.start();
      if (args.length==0) s.cool(); else
      if ("off".compareTo(args[0])==0) {
         s.off(); 
         System.out.println("System off. System exits.");
         System.exit(0);
      } else
      if ("cool".compareTo(args[0])==0) s.cool(); else
      if ("heat".compareTo(args[0])==0) s.heat(); else {
         System.out.println("Unknown command. System exits.");
         System.exit(1);
      }
      try {
         new CountDownLatch(5).await();
      } catch (InterruptedException e) {
         Thread.currentThread().interrupt();
         s.timer.stop();
         s.room.timer.stop();
      }
   }
class AC {
   boolean isOn=false;
   public void on() { isOn=true; }
   public void off() { isOn=false; }
}
class Heater {
   boolean isOn=false;
   public void on() { isOn=true; }
   public void off() { isOn=false; }
}
class Room implements ActionListener {
   public int temp=70;
   Timer timer=new Timer(400, this);
   public void actionPerformed(ActionEvent ae) {
      switch (state) {
         case OFF: return;
         case COOL: 
            if (ac.isOn) temp--; else temp++;
            break;
         case HEAT:
            if (heater.isOn) temp++; else temp--;
            break;
      } 
   }   
} // end of Room class
}
