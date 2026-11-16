package cse4392;

import java.io.File;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Runs SeasonSwitch.main(args) in a separate JVM, so System.exit(...) cannot stop the
 * test run. The child JVM gets the same JaCoCo agent as the test JVM, so the branches
 * it runs are counted in the same jacoco.exec.
 *
 * If main() is still running after waitMs (the cool/heat paths block until Ctrl-C),
 * the child is stopped with a normal terminate signal so JaCoCo still writes its data.
 *
 * main.py copies this file into src/test/java/cse4392/ before every Maven run.
 * Edit app/java_helpers/ExitTrap.java, not the copy.
 */
public final class ExitTrap {

    /** What happened when main() ran. */
    public static final class Result {
        public final boolean exitedByItself; // false: still running after waitMs, so it was stopped
        public final int exitCode;           // System.exit code; meaningless when exitedByItself is false
        public final String output;          // everything main() printed

        Result(boolean exitedByItself, int exitCode, String output) {
            this.exitedByItself = exitedByItself;
            this.exitCode = exitCode;
            this.output = output;
        }
    }

    private ExitTrap() { }

    /** Run main(args) and wait up to 3 seconds for it to exit. */
    public static Result runMain(String... args) throws IOException, InterruptedException {
        return runMain(3000, args);
    }

    /** Run main(args) and wait up to waitMs milliseconds for it to exit. */
    public static Result runMain(long waitMs, String... args) throws IOException, InterruptedException {
        List<String> command = new ArrayList<>();
        command.add(Paths.get(System.getProperty("java.home"), "bin", "java").toString());
        for (String arg : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
            if (arg.startsWith("-javaagent:") && arg.contains("jacoco")) {
                command.add(arg);
            }
        }
        command.add("-Djava.awt.headless=true");
        command.add("-cp");
        command.add(System.getProperty("java.class.path"));
        command.add("cse4392.SeasonSwitch");
        command.addAll(Arrays.asList(args));

        File log = File.createTempFile("exittrap", ".log");
        try {
            Process child = new ProcessBuilder(command)
                    .redirectErrorStream(true)
                    .redirectOutput(log)
                    .start();
            child.getOutputStream().close();
            boolean exited = child.waitFor(waitMs, TimeUnit.MILLISECONDS);
            if (!exited) {
                child.destroy(); // terminate signal: shutdown hooks run, JaCoCo writes its data
                if (!child.waitFor(10, TimeUnit.SECONDS)) {
                    child.destroyForcibly();
                    child.waitFor(5, TimeUnit.SECONDS);
                }
            }
            String output = new String(Files.readAllBytes(log.toPath()), StandardCharsets.UTF_8);
            return new Result(exited, exited ? child.exitValue() : -1, output);
        } finally {
            log.delete();
        }
    }
}
