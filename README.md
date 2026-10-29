# Exam-Registration-System-

## Java project

The uploaded Java application is in [`MINOR PROJECT GROUP NO/`](./MINOR%20PROJECT%20GROUP%20NO/).
The provided ZIP contains a prebuilt application JAR and its runtime libraries; it does
not include the Java source files.

### Run

Use Java 27 or later. The application was compiled to class-file version 71.
From the project directory, run:

```sh
cd "MINOR PROJECT GROUP NO"
java -jar minorproject.jar
```

Keep the `lib/` directory next to `minorproject.jar`; the JAR manifest uses those
SQLite and SLF4J libraries at runtime.

### Run in GitHub Codespaces

The Swing application needs a display. Install the virtual desktop packages once
in the Codespace:

```sh
sudo apt-get update
sudo apt-get install -y xvfb x11vnc novnc fluxbox
```

Start the app and remote desktop:

```sh
python3 run-codespace-desktop.py
```

In the Codespaces **Ports** tab, keep port `6080` private and open its forwarded
address. The launcher prints a direct noVNC link. Close the app or stop the
launcher with Ctrl+C when finished.
