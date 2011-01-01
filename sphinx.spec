%define	major 0
%define libname %mklibname sphinxclient %{major}
%define develname %mklibname sphinxclient -d

Summary:	SQL full-text search engine
Name:		sphinx
Version:	0.9.9
Release:	%mkrel 6
License:	GPL
Group:		System/Servers
URL:		http://sphinxsearch.com/
Source0:	http://sphinxsearch.com/downloads/%{name}-%{version}.tar.gz
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.logrotate
Patch0:		sphinx-DESTDIR.diff
Patch1:		sphinx-mdv_conf.diff
Patch2:		sphinx-libsphinxclient-version-info_fix.diff
Patch3:		sphinx-0.9.9-gcc43.diff
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	expat-devel
BuildRequires:	libstemmer-devel
BuildRequires:	libtool
BuildRequires:	mysql-devel
BuildRequires:	postgresql-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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

%package -n	%{libname}
Summary:	Shared sphinxclient library
Group:          System/Libraries

%description -n	%{libname}
This package contains the shared sphinxclient library.

%package -n	%{develname}
Summary:	Development files for the sphinxclient library
Group:		Development/C
Requires:	%{libname} = %{version}
Provides:	sphinxclient-devel = %{version}-%{release}
Provides:	lib%{name}-devel = %{version}-%{release}

%description -n	%{develname}
This package contains the development files for the sphinxclient library.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0
%patch1 -p0
%patch2 -p0
%patch3 -p0

cp %{SOURCE1} %{name}.init
cp %{SOURCE2} %{name}.sysconfig
cp %{SOURCE3} %{name}.logrotate

%build
%serverbuild

pushd api/libsphinxclient
libtoolize --copy --force; aclocal
sh ./buildconf.sh
%configure2_5x
make
popd

libtoolize --copy --force; aclocal; autoheader; automake --foreign --ignore-deps; autoconf

export CPPFLAGS="-I%{_includedir}/libstemmer"

%configure2_5x \
    --sysconfdir=%{_sysconfdir}/%{name} \
    --program-prefix="%{name}-" \
    --localstatedir=/var/lib \
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
install -d %{buildroot}/var/lib/%{name}
install -d %{buildroot}/var/run/%{name}
install -d %{buildroot}/var/log/%{name}

%makeinstall_std
%makeinstall_std -C api/libsphinxclient

mv %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf.dist %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
mv %{buildroot}%{_sysconfdir}/%{name}/%{name}-min.conf.dist %{buildroot}%{_sysconfdir}/%{name}/%{name}-min.conf
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

%if %mdkversion < 200900
%post -n %{libname} -p /sbin/ldconfig
%endif

%if %mdkversion < 200900
%postun -n %{libname} -p /sbin/ldconfig
%endif

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc COPYING doc/*.html doc/*.css mysqlse/gen_data.php example.sql
%attr(0755,root,root) %{_initrddir}/%{name}-searchd
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/example.sql
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}-min.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}-searchd
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-searchd
%attr(0755,root,root) %{_bindir}/%{name}-indexer
%attr(0755,root,root) %{_bindir}/%{name}-indextool
%attr(0755,root,root) %{_bindir}/%{name}-search
%attr(0755,root,root) %{_bindir}/%{name}-spelldump
%attr(0755,root,root) %{_sbindir}/%{name}-searchd
%attr(0755,root,root) %dir /var/lib/%{name}
%attr(0755,root,root) %dir /var/run/%{name}
%attr(0755,root,root) %dir /var/log/%{name}
%attr(0644,root,root) %ghost %config(noreplace) /var/log/sphinx/sphinx-searchd.log
%attr(0644,root,root) %ghost %config(noreplace) /var/log/sphinx/sphinx-query.log

%files -n %{libname}
%defattr(-,root,root)
%{_libdir}/*.so.*

%files -n %{develname}
%defattr(-,root,root)
%doc api/libsphinxclient/README
%{_includedir}/sphinxclient.h
%{_libdir}/*.so
%{_libdir}/*.*a
