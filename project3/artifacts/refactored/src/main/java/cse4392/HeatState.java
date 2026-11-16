package cse4392;

public class HeatState implements State {
    @Override
    public void cool(SeasonSwitch ss) {
        ss.heater.off();
        ss.ac.on();
        ss.timer.start();
        SeasonSwitch.state = SeasonSwitch.COOL;
        System.out.println("Cooling started. RmTemp=" + ss.room.temp);
    }

    @Override
    public void heat(SeasonSwitch ss) {
        // already heating, no-op
    }

    @Override
    public void off(SeasonSwitch ss) {
        ss.heater.off();
        ss.timer.stop();
        SeasonSwitch.state = SeasonSwitch.OFF;
        System.out.println("Heating stopped. RmTemp=" + ss.room.temp);
    }

    @Override
    public void timerOff(SeasonSwitch ss) {
        if (ss.room.temp < ss.heatTemp) {
            ss.heater.on();
            System.out.println("Heating started. RmTemp=" + ss.room.temp);
        } else {
            ss.heater.off();
            System.out.println("Heating stopped. RmTemp=" + ss.room.temp);
        }
    }

    @Override
    public void roomTick(SeasonSwitch ss) {
        if (ss.heater.isOn) ss.room.temp++; else ss.room.temp--;
    }
}
