%define	major 1
%define libname %mklibname sphinxclient %{major}
%define develname %mklibname sphinxclient -d

Summary:	SQL full-text search engine
Name:		sphinx
Version:	2.0.6
Release:	3
License:	GPLv2
Group:		System/Servers
URL:		http://sphinxsearch.com/
Source0:	http://sphinxsearch.com/files/%{name}-%{version}-release.tar.gz
Source1:        sphinx-searchd.service
Source2:	sphinx.logrotate
Patch0:		sphinx-DESTDIR.diff
Patch1:		sphinx-mdv_conf.diff
Patch2:		sphinx-libsphinxclient-version-info_fix.diff
Patch4:         sphinx-2.0.3-fix_static.patch
Patch5:		sphinx-2.0.3-gcc47.patch
Requires(post): rpm-helper
Requires(preun): rpm-helper
BuildRequires:	expat-devel
BuildRequires:	libstemmer-devel
BuildRequires:	libtool
BuildRequires:	mysql-devel
BuildRequires:	postgresql-devel

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

%setup -q -n %{name}-%{version}-release
%patch0 -p0
%patch1 -p1
%patch2 -p0
%patch4 -p1

cp %{SOURCE1} sphinx-searchd.service
cp %{SOURCE2} sphinx.logrotate

# Fix wrong-file-end-of-line-encoding
sed -i 's/\r//' api/ruby/spec/sphinx/sphinx_test.sql
sed -i 's/\r//' api/java/mk.cmd
sed -i 's/\r//' api/ruby/spec/fixtures/keywords.php
sed -i 's/\r//' api/ruby/lib/sphinx/response.rb

sed -i -e '/\/usr\/local\//d' configure.ac
sed -i -e 's/\/usr\/local\//\/someplace\/nonexisting\//g' configure


%build
%serverbuild

pushd api/libsphinxclient
libtoolize --copy --force; aclocal
cp configure.ac configure.in
sh ./buildconf.sh
cp configure.ac configure.in
export CPPFLAGS="-I%{_includedir}/libstemmer"
%configure2_5x
make
popd

#libtoolize --copy --force; aclocal; autoheader; automake --foreign --ignore-deps; autoconf

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
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}/lib/systemd/system
install -d %{buildroot}/var/lib/%{name}
install -d %{buildroot}/var/run/%{name}
install -d %{buildroot}/var/log/%{name}

%makeinstall_std
%makeinstall_std -C api/libsphinxclient

mv %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf.dist %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
mv %{buildroot}%{_sysconfdir}/%{name}/%{name}-min.conf.dist %{buildroot}%{_sysconfdir}/%{name}/%{name}-min.conf
mv %{buildroot}%{_bindir}/%{name}-searchd %{buildroot}%{_sbindir}/%{name}-searchd

install -m0644 sphinx-searchd.service %{buildroot}/lib/systemd/system/sphinx-searchd.service
install -m0644 %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}-searchd

# create ghostfiles
touch %{buildroot}/var/log/sphinx/sphinx-searchd.log
touch %{buildroot}/var/log/sphinx/sphinx-query.log

rm -f %{buildroot}%{_libdir}/*.*a

%post
%create_ghostfile /var/log/sphinx/sphinx-searchd.log root root 0644
%create_ghostfile /var/log/sphinx/sphinx-query.log root root 0644
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable searchd.service > /dev/null 2>&1 || :
    /bin/systemctl stop searchd.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart searchd.service >/dev/null 2>&1 || :
fi

%files
%doc COPYING doc/*.html doc/*.css mysqlse/gen_data.php example.sql
/lib/systemd/system/sphinx-searchd.service
%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/example.sql
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}-min.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-searchd
%attr(0755,root,root) %{_bindir}/%{name}-indexer
%attr(0755,root,root) %{_bindir}/%{name}-indextool
%attr(0755,root,root) %{_bindir}/%{name}-search
%attr(0755,root,root) %{_bindir}/%{name}-spelldump
%attr(0755,root,root) %{_sbindir}/%{name}-searchd
%attr(0755,sphinx,sphinx) %dir /var/lib/%{name}
%attr(0755,sphinx,sphinx) %dir /var/run/%{name}
%attr(0755,sphinx,sphinx) %dir /var/log/%{name}
%attr(0644,sphinx,sphinx) %ghost %config(noreplace) /var/log/sphinx/sphinx-searchd.log
%attr(0644,sphinx,sphinx) %ghost %config(noreplace) /var/log/sphinx/sphinx-query.log
%{_mandir}/man1/sphinx-indexer.1*
%{_mandir}/man1/sphinx-indextool.1*
%{_mandir}/man1/sphinx-search.1*
%{_mandir}/man1/sphinx-searchd.1*
%{_mandir}/man1/sphinx-spelldump.1*

%files -n %{libname}
%{_libdir}/*.so.%{major}*

%files -n %{develname}
%doc api/libsphinxclient/README
%{_includedir}/sphinxclient.h
%{_libdir}/*.so
