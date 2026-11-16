package cse4392;

public class OffState implements State {
    @Override
    public void cool(SeasonSwitch ss) {
        ss.ac.on();
        ss.timer.start();
        SeasonSwitch.state = SeasonSwitch.COOL;
        System.out.println("Cooling started. RmTemp=" + ss.room.temp);
    }

    @Override
    public void heat(SeasonSwitch ss) {
        ss.heater.on();
        ss.timer.start();
        SeasonSwitch.state = SeasonSwitch.HEAT;
        System.out.println("Heating started. RmTemp=" + ss.room.temp);
    }

    @Override
    public void off(SeasonSwitch ss) {
        // no-op
    }

    @Override
    public void timerOff(SeasonSwitch ss) {
        // no-op
    }

    @Override
    public void roomTick(SeasonSwitch ss) {
        // no-op
    }
}
