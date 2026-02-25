Name:           systemd-fresh-boot
Version:        0.1.0
Release:        1%{?dist}
Summary:        Service units to block boot for systems that haven't booted in a while
License:        LGPL-2.1-or-later
URL:            https://github.com/jcpunk/%{name}
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  systemd-rpm-macros
Requires:       systemd bash coreutils

%description
Some times you want to block computers that haven't booted in a while.

%prep
%autosetup

%build
# no build step; script-only package
true

%install
mkdir -p %{buildroot}/etc/default
touch %{buildroot}/etc/default/boot-freshness
install -D -m 0755 boot-freshness-check %{buildroot}/%{_libexecdir}/boot-freshness-check
install -D -m 0644 systemd/fresh-boot-check.service %{buildroot}/%{_unitdir}/fresh-boot-check.service
install -D -m 0644 systemd/fresh-boot-heartbeat.service %{buildroot}/%{_unitdir}/fresh-boot-heartbeat.service
install -D -m 0644 systemd/fresh-boot-heartbeat.timer %{buildroot}/%{_unitdir}/fresh-boot-heartbeat.timer

%files
%license LICENSE
%doc README.md
%ghost /var/lib/.boot-freshness-last-seen
%config(noreplace) /etc/default/boot-freshness
%{_libexecdir}/boot-freshness-check
%{_unitdir}/fresh-boot-check.service
%{_unitdir}/fresh-boot-heartbeat.service
%{_unitdir}/fresh-boot-heartbeat.timer

%post
%systemd_post fresh-boot-check.service fresh-boot-heartbeat.timer

%preun
%systemd_preun fresh-boot-check.service fresh-boot-heartbeat.timer

%postun
%systemd_postun fresh-boot-check.service fresh-boot-heartbeat.timer

%changelog
* Wed Feb 25 2026 Pat Riehecky <riehecky@fnal.gov> - 0.1.0-1
- Initial package.
