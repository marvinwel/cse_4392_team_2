package cse4392;

public interface State {
    void cool(SeasonSwitch ss);
    void heat(SeasonSwitch ss);
    void off(SeasonSwitch ss);
    void timerOff(SeasonSwitch ss);
    void roomTick(SeasonSwitch ss);
}
