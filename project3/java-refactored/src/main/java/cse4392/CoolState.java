package cse4392;

public class CoolState implements State {
    @Override
    public void cool(SeasonSwitch ss) {
        // already cooling, no-op
    }

    @Override
    public void heat(SeasonSwitch ss) {
        ss.ac.off();
        ss.heater.on();
        ss.timer.start();
        SeasonSwitch.state = SeasonSwitch.HEAT;
        System.out.println("Heating started. RmTemp=" + ss.room.temp);
    }

    @Override
    public void off(SeasonSwitch ss) {
        ss.ac.off();
        ss.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
        System.out.println("Cooling stopped. RmTemp=" + ss.room.temp);
    }

    @Override
    public void timerOff(SeasonSwitch ss) {
        if (ss.room.temp > ss.coolTemp) {
            ss.ac.on();
            System.out.println("Cooling started. RmTemp=" + ss.room.temp);
        } else {
            ss.ac.off();
            System.out.println("Cooling stopped. RmTemp=" + ss.room.temp);
        }
    }

    @Override
    public void roomTick(SeasonSwitch ss) {
        if (ss.ac.isOn) ss.room.temp--; else ss.room.temp++;
    }
}
