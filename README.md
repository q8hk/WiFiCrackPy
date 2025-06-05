# WiFiCrackPy

WiFiCrackPy demonstrates some of the security flaws associated with WPA(2) networks by performing simple and efficient cracking. The tool is for **educational purposes** and should not be misused.

## Disclaimer

The software is intended only for **authorized security testing** on networks you own or have explicit permission to test. When running the tool you must type `AGREE` to acknowledge this disclaimer before any action takes place.

The script captures the necessary Wi-Fi packets associated with WPA(2) handshakes using platform-specific tools, processes them with [`hcxpcapngtool`](https://github.com/ZerBea/hcxtools), and then utilises [`hashcat`](https://github.com/hashcat/hashcat) to extract the hashed passkey.

## Prerequisites

You must have `python3` installed. Additional requirements depend on your operating system:

### macOS
| Command | Installation |
| --- | --- |
| `hashcat`, `libpcap`, `wget`, `hcxpcapngtool` | Install via [brew](https://brew.sh) by running `brew install hashcat libpcap wget hcxtools` |
| `~/zizzania/src/zizzania` | Clone [this](https://github.com/cyrus-and/zizzania) repository then run `make -f config.Makefile && make -j "$(sysctl -n hw.logicalcpu)"` |

### Windows
| Command | Installation |
| --- | --- |
| `Wireshark/TShark` | Download and install from [Wireshark](https://www.wireshark.org/download.html) |
| `hashcat` | Download from [hashcat](https://hashcat.net/hashcat/) and add to PATH |
| `hcxtools` | Download from [hcxtools](https://github.com/ZerBea/hcxtools/releases) and add to PATH |
| `Python requirements` | Run `pip install -r requirements.txt` |

### Linux/Debian
| Command | Installation |
| --- | --- |
| `wireless-tools` | `sudo apt-get install wireless-tools` |
| `hashcat` | `sudo apt-get install hashcat` |
| `hcxtools` | `sudo apt-get install hcxtools` |
| `libpcap` | `sudo apt-get install libpcap-dev` |
| `Python requirements` | Run `pip install -r requirements.txt` |

## Compatibility issues

- `zizzania` has the ability to send deauthentication frames to force a handshake. This feature is disabled by default as there are major compatibility issues with newer Macs (~2018 onwards)
- `hashcat` currently has major compatibility issues with Apple silicon Macs. Cracking may not be possible on these Macs so you can use the manual option to export the capture

## Usage

Download with:
```
git clone https://github.com/phenotypic/WiFiCrackPy.git
pip3 install -r requirements.txt
```

The default wordlist setting assumes `rockyou.txt` resides in `C:/Tools/SecLists/Passwords`.
If no wordlist is supplied with `-w`, the script first checks the path configured in `settings.yml` or a directory specified via the `SECLISTS_DIR` environment variable.
If the wordlist cannot be located, the script attempts common system locations and finally offers to download a shallow copy of SecLists for you.
You can still edit `settings.yml` or manually provide a path with the `-w` flag.

Run from the same directory with:
```
python3 WiFiCrackPy.py
```

The script is fairly easy to use, simply run it using the command above and enter your `sudo` password when prompted. Here are some flags you can add:

| Flag | Description |
| --- | --- |
| `-w <wordlist>` | Wordlist: Define a wordlist path (script will prompt you otherwise) |
| `-r <rule-file>` | Rules: Supply a hashcat rule file for wordlist transformations |
| `-i <interface>` | Interface: Set Wi-Fi interface (script can auto-detect default interface) |
| `-m <method>` | Method: Define the attack method (script will prompt you otherwise) |
| `-p <pattern>` | Pattern: Define a brute-force pattern in advance (script will prompt you if required) |
| `-o` | Optimised: Enable optimised kernels for `hashcat` |
| `-d` | Deauthentication: Activates zizzania's deauthentication feature to force a handshake (do not misuse) |
| `--dry-run` | Run with dummy data and mocked system commands |
| `--check-deps` | Check required external tools and exit |
| `--resume [ssid]` | Resume cracking with existing capture files. If no SSID provided, lists available captures |

After running the script, you will be asked to choose a network to crack

Following the selection of a network, you may have to wait for a while for a handshake to occur naturally on the target network (i.e. for a device to (re)connect to the network) unless you are using the `-d` flag which will force a handshake to hasten the process.

Once a handshake is captured, `hashcat` can be used to crack the Wi-Fi password. This step may take quite a while depending on several factors including your Mac's processing power and the attack method chosen. If successful, you will be presented with the password for the target network.

The script offers four attack modes: dictionary, brute-force, **low hanging fruit** (a short sequence of common wordlist and numeric masks), and manual.

WiFiCrackPy retains the handshake in its directory if you would like to perform another type of attack against the capture.

### Dry run example

To see the workflow without executing any external commands, run:

```
python3 WiFiCrackPy.py --dry-run
```

This uses dummy network data and prints the commands that would normally be executed.

