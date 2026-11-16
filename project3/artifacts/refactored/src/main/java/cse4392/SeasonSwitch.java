package cse4392;

import javax.swing.Timer;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.concurrent.CountDownLatch;

public class SeasonSwitch implements ActionListener {
    static State state = new OffState();
    static final State OFF  = new OffState();
    static final State COOL = new CoolState();
    static final State HEAT = new HeatState();

    AC ac = new AC();
    Heater heater = new Heater();
    Timer timer = new Timer(1200, this);
    Room room = new Room();
    int coolTemp = 68;
    int heatTemp = 77;

    public void cool() {
        if (state == null) return;
        state.cool(this);
    }

    public void heat() {
        if (state == null) return;
        state.heat(this);
    }

    public void off() {
        if (state == null) return;
        state.off(this);
    }

    public void actionPerformed(ActionEvent e) {
        timerOff();
    }

    public void timerOff() {
        if (state == null) return;
        state.timerOff(this);
    }

    public static void main(String[] args) {
        System.out.println("Enter off, cool or heat to run. " +
            "Press Ctrl-c to exit.");
        SeasonSwitch s = new SeasonSwitch();
        s.room.timer.start();
        if (args.length == 0) s.cool(); else
        if ("off".compareTo(args[0]) == 0) {
            s.off();
            System.out.println("System off. System exits.");
            System.exit(0);
        } else
        if ("cool".compareTo(args[0]) == 0) s.cool(); else
        if ("heat".compareTo(args[0]) == 0) s.heat(); else {
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
        boolean isOn = false;
        public void on()  { isOn = true;  }
        public void off() { isOn = false; }
    }

    class Heater {
        boolean isOn = false;
        public void on()  { isOn = true;  }
        public void off() { isOn = false; }
    }

    class Room implements ActionListener {
        public int temp = 70;
        Timer timer = new Timer(400, this);
        public void actionPerformed(ActionEvent ae) {
            if (state == null) return;
            state.roomTick(SeasonSwitch.this);
        }
    }
}
