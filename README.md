# systemd-fresh-boot

Blocks boot to `rescue.target` on systems that have been offline longer than a
configurable threshold. Intended for environments where workstations and laptops
may be decommissioned informally and rediscovered years later without any admin
involvement.

## How it works

A heartbeat timer touches `/var/lib/.boot-freshness-last-seen` every 6 hours
while the system is running. On every boot, a check service reads the `mtime`
of that file. If the gap exceeds the threshold the system is isolated to
`rescue.target` rather than continuing to `multi-user.target`.

The check service runs before `sysinit.target` so the system cannot reach a
usable state without passing the freshness gate.

If the timestamp file does not exist (i.e. the package was just installed and
the system has not yet heartbeated) the check service is skipped via
`ConditionPathExists`. The file will be created on the first heartbeat after the
system reaches `multi-user.target`.

### Why `mtime` and not file contents

The timestamp is the sole state. Using `mtime` eliminates any custom format to
parse or validate and reduces the heartbeat to a plain `touch`. There is nothing
in the file to corrupt.

### Why no `Persistent=true` on the timer

`Persistent=true` would cause systemd to fire a missed heartbeat immediately on
boot, refreshing the `mtime` before the check service could inspect it. Any
shutdown longer than the threshold would be silently unblocked. The preserved
`mtime` from the last pre-shutdown heartbeat is the evidence the check depends
on.

## Units

| Unit | Role |
|------|------|
| `fresh-boot-check.service` | Oneshot check at boot, before `sysinit.target` |
| `fresh-boot-heartbeat.service` | Oneshot `touch` of the timestamp file |
| `fresh-boot-heartbeat.timer` | Fires 5 min after boot, then every 6 hours |

## Configuration

The check script reads `/etc/default/boot-freshness` as an environment file.
Set `BOOT_FRESHNESS_MAX_OFFLINE_DAYS` to override the default threshold of 93
days (approximately one quarter).

```bash
# /etc/default/boot-freshness
BOOT_FRESHNESS_MAX_OFFLINE_DAYS=180
```

The file is installed as `%config(noreplace)` so RPM upgrades will not
overwrite a locally modified value.

## Recommissioning a blocked system

When a system boots to rescue, log in as root and verify the situation:

```bash
stat /var/lib/.boot-freshness-last-seen
journalctl -t boot-freshness-check -b
```

After inspecting and recommissioning the system, refresh the timestamp and
reboot normally:

```bash
touch /var/lib/.boot-freshness-last-seen
systemctl reboot
```

## Installation

### RPM

```bash
rpmbuild -ba systemd-fresh-boot.spec
dnf install systemd-fresh-boot-*.rpm
```

The RPM scriptlets use `%systemd_post` / `%systemd_preun` / `%systemd_postun`
to run `systemctl preset` on install and handle enable/disable/restart correctly
on upgrade and removal.

To enable the units by default via preset, install a preset file:

```
# /usr/lib/systemd/system-preset/90-boot-freshness.preset
enable fresh-boot-heartbeat.timer
enable fresh-boot-check.service
```

### Manual

```bash
install -Dm 755 boot-freshness-check /usr/libexec/boot-freshness-check
install -Dm 644 fresh-boot-check.service /etc/systemd/system/
install -Dm 644 fresh-boot-heartbeat.service /etc/systemd/system/
install -Dm 644 fresh-boot-heartbeat.timer /etc/systemd/system/
install -Dm 644 /dev/null /etc/default/boot-freshness

systemctl daemon-reload
systemctl enable --now fresh-boot-heartbeat.timer
systemctl enable fresh-boot-check.service
```

## Requirements

- systemd
- bash
- coreutils (`touch`, `stat`, `date`)
- RHEL / AlmaLinux 8 or later (or any distribution with systemd ≥ 219)

## License

LGPL-2.1-or-later
