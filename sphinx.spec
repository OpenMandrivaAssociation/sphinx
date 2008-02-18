%define snap svn-r1112

Summary:	SQL full-text search engine
Name:		sphinx
Version:	0.9.8
Release:	%mkrel 2
License:	GPL
Group:		System/Servers
URL:		http://sphinxsearch.com/
Source0:	http://sphinxsearch.com/downloads/%{name}-%{version}-%{snap}.tar.gz
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.logrotate
Patch0:		sphinx-DESTDIR.diff
Patch1:		sphinx-mdv_conf.diff
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	expat-devel
BuildRequires:	libstemmer-devel
BuildRequires:	mysql-devel
BuildRequires:	postgresql-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-build

%description
Sphinx is a full-text search engine, distributed under GPL version 2.
Commercial licensing is also available upon request.

Generally, it's a standalone search engine, meant to provide fast,
size-efficient and relevant fulltext search functions to other applications.
Sphinx was specially designed to integrate well with SQL databases and
scripting languages. Currently built-in data source drivers support fetching
data either via direct connection to MySQL, PostgreSQL, or from a pipe in a
custom XML format.

As for the name, Sphinx is an acronym which is officially decoded as SQL Phrase
Index. Yes, I know about CMU's Sphinx project.

%prep

%setup -q -n %{name}-%{version}-%{snap}
%patch0 -p0
%patch1 -p0

cp %{SOURCE1} %{name}.init
cp %{SOURCE2} %{name}.sysconfig
cp %{SOURCE3} %{name}.logrotate

%build
libtoolize --copy --force; aclocal; autoheader; automake --foreign --ignore-deps; autoconf
%serverbuild

export CPPFLAGS="-I%{_includedir}/libstemmer"

%configure2_5x \
    --sysconfdir=%{_sysconfdir}/%{name} \
    --program-prefix="%{name}-" \
    --with-mysql \
    --with-pgsql

# hack to enable external stemmer libs
perl -pi -e "s|^LIBSTEMMER_LIBS.*|LIBSTEMMER_LIBS=-lstemmer|g" src/Makefile
perl -pi -e "s|^#define USE_LIBSTEMMER.*|#define USE_LIBSTEMMER 1|g" config/config.h

%make

%install
rm -rf %{buildroot}

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_localstatedir}/%{name}
install -d %{buildroot}/var/run/%{name}
install -d %{buildroot}/var/log/%{name}

%makeinstall_std

mv %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf.dist %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
mv %{buildroot}%{_bindir}/%{name}-searchd %{buildroot}%{_sbindir}/%{name}-searchd

install -m0755 %{name}.init %{buildroot}%{_initrddir}/%{name}-searchd
install -m0644 %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}-searchd
install -m0644 %{name}.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/%{name}-searchd

# create ghostfiles
touch %{buildroot}/var/log/sphinx/sphinx-searchd.log
touch %{buildroot}/var/log/sphinx/sphinx-query.log

%post
%create_ghostfile /var/log/sphinx/sphinx-searchd.log root root 0644
%create_ghostfile /var/log/sphinx/sphinx-query.log root root 0644
%_post_service %{name}-searchd

%preun
%_preun_service %{name}-searchd

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc COPYING api doc/*.html doc/*.css mysqlse/gen_data.php mysqlse/HOWTO.txt example.sql
%attr(0755,root,root) %{_initrddir}/%{name}-searchd
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/example.sql
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}-searchd
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-searchd
%attr(0755,root,root) %{_bindir}/%{name}-indexer
%attr(0755,root,root) %{_bindir}/%{name}-search
%attr(0755,root,root) %{_bindir}/%{name}-spelldump
%attr(0755,root,root) %{_sbindir}/%{name}-searchd
%attr(0755,root,root) %dir %{_localstatedir}/%{name}
%attr(0755,root,root) %dir /var/run/%{name}
%attr(0755,root,root) %dir /var/log/%{name}
%attr(0644,root,root) %ghost %config(noreplace) /var/log/sphinx/sphinx-searchd.log
%attr(0644,root,root) %ghost %config(noreplace) /var/log/sphinx/sphinx-query.log
